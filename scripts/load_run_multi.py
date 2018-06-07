#!/usr/bin/python3.6

import os
import requests
import time
import threading
from datetime import datetime
from subprocess import call

load_name = "load.properties"
read_name = "read.properties"
num_nodes = 4

asterixdb = "/home/ubuntu/asterixdb"

table_paras = (0, 2, 3, 4, 5, 8, 10, 12, 15, 20, 25, 30, 40, 60, 80, 100, 150)

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
res_path = os.path.join(dir_path, "results_with_bf")
srv_path = os.path.join(dir_path, "server_logs_with_bf")

if not os.path.isdir(res_path):
    os.mkdir(res_path)
if not os.path.isdir(srv_path):
    os.mkdir(srv_path)

ycsb = os.path.join(dir_path, "ycsb-0.14.0-SNAPSHOT", "bin", "ycsb")

load_path = os.path.join(dir_path, "configs", load_name)
read_path = os.path.join(dir_path, "configs", read_name)

query_url = ""
feed_port = 0

with open(load_path, "r") as inf:
    for line in inf:
        if line.startswith("db.url="):
            line = line.replace("db.url=", "").replace("\r", "").replace("\n", "")
            query_url = line
        if line.startswith("db.feedport="):
            line = line.replace("db.feedport=", "").replace("\r", "").replace("\n", "")
            feed_port = int(line)
inf.close()


def exe_sqlpp(cmd):
    r = requests.post(query_url, data={"statement": cmd})
    if r.status_code == 200:
        return True
    else:
        print("Error: " + r.reason + "" + cmd)
        return False


def create_dataverse():
    cmd = """DROP DATAVERSE ycsb IF EXISTS;
CREATE DATAVERSE ycsb;"""
    return exe_sqlpp(cmd)


def create_type():
    cmd = """USE ycsb;
CREATE TYPE usertype AS CLOSED {
    YCSB_KEY: string,
    field0: binary,
    field1: binary,
    field2: binary,
    field3: binary,
    field4: binary,
    field5: binary,
    field6: binary,
    field7: binary,
    field8: binary,
    field9: binary
};"""
    return exe_sqlpp(cmd)


def create_table(num_components):
    if num_components > 1:
        cmd = """USE ycsb;
CREATE DATASET usertable (usertype)
    PRIMARY KEY YCSB_KEY
    WITH {
        "merge-policy":{
            "name":"constant",
            "parameters":{
                "num-components":""" + str(num_components) + """
            }
        }
    };"""
    else:
        cmd = """USE ycsb;
CREATE DATASET usertable (usertype)
    PRIMARY KEY YCSB_KEY
    WITH {
        "merge-policy":{
            "name":"no-merge"
        }
    };"""
    return exe_sqlpp(cmd)


def create_feed():
    cmd = """USE ycsb;
CREATE FEED userfeed WITH {
    "adapter-name":"socket_adapter",
    "sockets":"localhost:""" + str(feed_port) + """",
    "address-type":"IP",
    "type-name":"usertype",
    "format":"adm",
    "upsert-feed":"true"
};
CONNECT FEED userfeed TO DATASET usertable;"""
    return exe_sqlpp(cmd)


def start_feed():
    cmd = """USE ycsb;
START FEED userfeed;"""
    return exe_sqlpp(cmd)


def stop_feed():
    cmd = """USE ycsb;
STOP FEED userfeed;"""
    return exe_sqlpp(cmd)


def get_server_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


class clearNodeLogs(threading.Thread):
    def __init__(self, nodeid):
        threading.Thread.__init__(self)
        self.nodeid = nodeid

    def run(self):
        call("ssh node{0} \"python3.6 {1}/scripts/clear_logs.py {2}/logs/node-{0}-service.log"
             " {2}/logs/nc-node_{0}.log\""
             .format(self.nodeid, dir_path, asterixdb), shell=True)
        print("Cleared node {0}".format(self.nodeid))


class copyNodeLogs(threading.Thread):
    def __init__(self, nodeid, prefix):
        threading.Thread.__init__(self)
        self.nodeid = nodeid
        self.prefix = prefix

    def run(self):
        call("ssh node{0} \"python3.6 {1}/scripts/trim_logs.py {2}/logs/{3}_node-{0}.log.gzip"
             " {2}/logs/node-{0}-service.log"
             " {2}/logs/nc-node_{0}.log\""
             .format(self.nodeid, dir_path, asterixdb, self.prefix), shell=True)
        call("scp node{0}:{1}/logs/node-{0}.log.gzip {2}/{3}_node-{0}.log.gzip"
             .format(self.nodeid, asterixdb, srv_path, self.prefix), shell=True)
        print("Copied node {0}".format(self.nodeid))


def run_workload(operation, config, num_components, outf):
    clears = []
    for i in range(num_nodes):
        clears.append(clearNodeLogs(i+1))
    for th in clears:
        th.start()
    for th in clears:
        th.join()

    # Clear controller log
    logf = open(os.path.join(asterixdb, "logs", "cc.log"), "w")
    logf.close()

    fn = os.path.basename(config).replace(".properties", "")
    prefix = os.path.join(res_path, "{0}_{1}".format(fn, num_components))
    cmd = "python3.6 \"{0}\" {1} asterixdb -P \"{2}\"" \
          " -p exportfile=\"{3}.txt\" -s -threads 1 > \"{3}.log\"" \
        .format(ycsb, operation, config, prefix)
    if outf is not None:
        outf.write("{0}\t{1}\n".format(fn, get_server_time()))
    call(cmd, shell=True)
    time.sleep(180)

    call("python3.6 {0}/scripts/trim_logs.py {1}/{2}_cc.log.gzip {3}/logs/cc.log"
         .format(dir_path, srv_path, "{0}_{1}".format(fn, num_components), asterixdb), shell=True)

    copys = []
    for i in range(num_nodes):
        copys.append(copyNodeLogs(i+1, "{0}_{1}".format(fn, num_components)))
    for th in copys:
        th.start()
    for th in copys:
        th.join()

    time.sleep(60)


def run_exp(num_components):
    if num_components > 1:
        print("Starting with {0} components".format(num_components))
    else:
        print("Starting with {0} component".format(num_components))

    if not create_dataverse():
        print("Failed to create dataverse")
        return False
    print("Created dataverse")
    if not create_type():
        print("Failed to create type")
        return False
    print("Created type")
    if not create_table(num_components):
        print("Failed to create table")
        return False
    print("Created table")
    if not create_feed():
        print("Failed to create feed")
        return False
    print("Created feed")

    if not start_feed():
        print("Failed to start feed")
    print("Feed started")

    outf = open(os.path.join(res_path, "server_time_{0}.log".format(num_components)), "w")

    print("Loading...")
    run_workload("load", load_path, num_components, outf)

    print("Reading...")
    run_workload("run", read_path, num_components, outf)

    outf.close()

    print("Done {0}".format(num_components))


if __name__ == "__main__":
    for n in table_paras:
        run_exp(n)
