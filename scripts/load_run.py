#!/usr/bin/python3

import os
import requests
import glob
import gzip
import time
from datetime import datetime
from subprocess import call, check_output

load_name = "load.properties"
read_name = "read.properties"

asterixdb = "/home/ubuntu/asterixdb/opt/local"

table_paras = (0, 2, 3, 5, 10, 15, 20, 25)

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


def start_server():
    call("\"{0}\"/bin/start-sample-cluster.sh".format(asterixdb), shell=True)


def stop_server():
    call("\"{0}\"/bin/stop-sample-cluster.sh".format(asterixdb), shell=True)


def remove_data_logs():
    call("rm -fr \"{0}\"/data \"{0}\"/logs".format(asterixdb), shell=True)


def empty_logs():
    for logp in glob.glob("{0}/logs/*.log".format(asterixdb)):
        outf = open(logp, "w")
        outf.close()


def ensure_finished():
    for i in range(20):
        if is_finished():
            break
        time.sleep(10 + i * 10)


def is_finished():
    return check_log(os.path.join(asterixdb, "logs", "red-service.log"))


def reverse_readline(filename, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
    with open(filename, "r", encoding="utf-8") as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split("\n")
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] is not "\n":
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if len(lines[index]):
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment


def check_log(logp):
    flush_before = -1
    flush_after = -1
    merge_before = -1
    merge_after = -1
    cnt = -1
    for logline in reverse_readline(logp):
        if flush_before > -1 and flush_after > -1 and merge_before > -1 and merge_after > -1:
            break
        cnt += 1
        if "[EXPERIMENT]" not in logline:
            continue
        if flush_before == -1 and "flush-before" in logline:
            flush_before = cnt
        elif flush_after == -1 and "flush-after" in logline:
            flush_after = cnt
        elif merge_before == -1 and "merge-before" in logline:
            merge_before = cnt
        elif merge_after == -1 and "merge-after" in logline:
            merge_after = cnt
        else:
            continue
    if flush_after > flush_before or merge_after > merge_before:
        return False
    else:
        return True


def copy_logs(operation, num_components):
    outf = gzip.open(os.path.join(srv_path, "{0}_{1}.log.gzip".format(operation, num_components)), "wt")
    for src in glob.glob("{0}/logs/*.log".format(asterixdb)):
        with open(src, "r") as inf:
            for line in inf:
                if "[EXPERIMENT]" in line and "usertable" in line:
                    line = line[line.index("[EXPERIMENT]") - 24:].replace("\r\n", "\n")
                    outf.write(line)
                elif "[QUERY]" in line:
                    line = line[line.index("[QUERY]") - 24:].replace("\r\n", "\n")
                    outf.write(line)
                else:
                    continue
        inf.close()
    outf.close()


def get_server_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def run_workload(operation, config, num_components, outf):
    fn = os.path.basename(config).replace(".properties", "")
    prefix = os.path.join(res_path, "{0}_{1}".format(fn, num_components))
    cmd = "python3.6 \"{0}\" {1} asterixdb -P \"{2}\"" \
          " -p exportfile=\"{3}.txt\" -s -threads 1 > \"{3}.log\"" \
        .format(ycsb, operation, config, prefix)
    if outf is not None:
        outf.write("{0}\t{1}\n".format(fn, get_server_time()))
    call(cmd, shell=True)
    stop_feed()
    ensure_finished()
    time.sleep(30)
    stop_server()
    copy_logs(fn, num_components)
    empty_logs()


def run_exp(num_components):
    if num_components > 1:
        print("Starting with {0} components".format(num_components))
    else:
        print("Starting with {0} component".format(num_components))

    stop_server()
    remove_data_logs()
    start_server()
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
    stop_server()
    start_server()

    if not start_feed():
        print("Failed to start feed")
    print("Feed started")

    outf = open(os.path.join(res_path, "server_time_{0}.log".format(num_components)), "w")

    print("Loading...")
    run_workload("load", load_path, num_components, outf)

    print("Reading...")
    start_server()
    start_feed()
    run_workload("run", read_path, num_components, outf)

    outf.close()

    print("Done {0}".format(num_components))


if __name__ == "__main__":
    for n in table_paras:
        run_exp(n)
