#!/usr/bin/python3.6

import requests
import os
from subprocess import call


dir_path = os.path.dirname(os.path.realpath(__file__))
res_path = os.path.join(dir_path, "results")

ycsb = os.path.join(dir_path, "ycsb-0.14.0-SNAPSHOT", "bin", "ycsb")

config_path = os.path.join(dir_path, "configs", "readonly")

query_url = None
dataverse = "ycsb"
dataset = "usertable"
feed_host = "localhost"
feed_port = 10001


def load_properties():
    global query_url, dataverse, dataset
    with open(config_path, "r") as inf:
        for line in inf:
            if line.startswith("db.url="):
                query_url = (line.replace("\r", "").replace("\n", ""))[7:]
            elif line.startswith("db.dataverse="):
                dataverse = (line.replace("\r", "").replace("\n", ""))[13:]
            elif line.startswith("table="):
                dataset = (line.replace("\r", "").replace("\n", ""))[6:]
            elif line.startswith("db.feedhost="):
                feed_host = (line.replace("\r", "").replace("\n", ""))[12:]
            elif line.startswith("db.feedport="):
                feed_port = int((line.replace("\r", "").replace("\n", ""))[12:])
            else:
                continue
    inf.close()

    if not os.path.isdir(res_path):
        os.mkdir(res_path)


def exe_sqlpp(cmd):
    r = requests.post(query_url, data={"statement": cmd})
    if r.status_code == 200:
        return True
    else:
        print("Error: " + r.reason + "\n" + cmd)
        return False


def create_table():
    sqlpp = "DROP DATAVERSE " + dataverse + " IF EXISTS;\n"
    sqlpp += "CREATE DATAVERSE " + dataverse + ";\n"
    sqlpp += "USE " + dataverse + "\n;"

    sqlpp += "CREATE TYPE UserType AS {\n"
    sqlpp += "YCSB_KEY: string,\n"
    sqlpp += "field0: binary,\n"
    sqlpp += "field1: binary,\n"
    sqlpp += "field2: binary,\n"
    sqlpp += "field3: binary,\n"
    sqlpp += "field4: binary,\n"
    sqlpp += "field5: binary,\n"
    sqlpp += "field6: binary,\n"
    sqlpp += "field7: binary,\n"
    sqlpp += "field8: binary,\n"
    sqlpp += "field9: binary\n"
    sqlpp += "};\n"

    sqlpp += "CREATE DATASET " + dataset + "(UserType) PRIMARY KEY YCSB_KEY;"

    sqlpp += "CREATE FEED userfeed WITH {\n"
    sqlpp += "\"adapter-name\":\"socket_adapter\",\n"
    sqlpp += "\"sockets\":\"" + feed_host + ":" + str(feed_port) + "\",\n"
    sqlpp += "\"address-type\":\"IP\",\n"
    sqlpp += "\"type-name\":\"UserType\",\n"
    sqlpp += "\"format\":\"adm\",\n"
    sqlpp += "\"upsert-feed\":\"true\"\n"
    sqlpp += "};\n"

    sqlpp += "CONNECT FEED userfeed TO DATASET " + dataset + ";\n"

    sqlpp += "START FEED userfeed;"

    return exe_sqlpp(sqlpp)


def stop_feed():
    exe_sqlpp("USE " + dataverse + ";STOP FEED userfeed;")
    exe_sqlpp("USE " + dataverse + ";DISCONNECT FEED userfeed FROM DATASET " + dataset + ";")


def start_feed():
    exe_sqlpp("USE " + dataverse + ";CONNECT FEED userfeed TO DATASET " + dataset + ";")
    exe_sqlpp("USE " + dataverse + ";START FEED userfeed;")


def worker():
    log_prefix = os.path.join(res_path, "load")
    cmd = "python3.6 \"{0}\" load asterixdb -P \"{1}\" -p exportfile=\"{2}.txt\" -s -threads 1 > \"{2}.log\""\
        .format(ycsb, config_path, log_prefix)
    call(cmd, shell=True)


if __name__ == '__main__':
    load_properties()
    create_table()
    start_feed()
    worker()
