#!/usr/bin/python3.6

import os
import requests
import time
from subprocess import call, check_output


dir_path = os.path.dirname(os.path.realpath(__file__))

read_py = os.path.join(dir_path, "read.py")
scan_py = os.path.join(dir_path, "scan.py")
readwrite_py = os.path.join(dir_path, "readwrite.py")


def get_instance():
    res = check_output("ssh ctl \"source /root/setup/admin-openrc.sh && nova list && exit\"", shell=True)\
        .decode("utf-8").split("\n")
    fields = res[3].split("|")
    return fields[1].strip()


def start_server():
    call("ssh dbserver \"bash -l -c /home/ubuntu/database/opt/local/bin/start-sample-cluster.sh\"", shell=True)
    start_feed()


def stop_server():
    call("ssh dbserver \"bash -l -c /home/ubuntu/database/opt/local/bin/stop-sample-cluster.sh\"", shell=True)


def start_feed():
    cmd = "USE ycsb; START FEED userfeed;"
    r = requests.post("http://128.110.155.182:19002/query/service", data={"statement": cmd})
    if r.status_code == 200:
        return True
    else:
        print("Error: " + r.reason + "\n" + cmd)
        return False


def stop_feed():
    cmd = "USE ycsb; STOP FEED userfeed;"
    r = requests.post("http://128.110.155.182:19002/query/service", data={"statement": cmd})
    if r.status_code == 200:
        return True
    else:
        print("Error: " + r.reason + "\n" + cmd)
        return False


def reboot_vm(instance):
    call("ssh ctl \"source /root/setup/admin-openrc.sh && nova reboot {0} && exit\"".format(instance),
         shell=True)


iid = get_instance()

# stop_feed()
# time.sleep(5)
# stop_server()
#
# reboot_vm(iid)
# time.sleep(30)
#
# start_server()
# time.sleep(5)
# start_feed()
# time.sleep(5)
#
# call("python3.6 \"{0}\"".format(scan_py), shell=True)

stop_feed()
time.sleep(5)
stop_server()

reboot_vm(iid)
time.sleep(30)

start_server()
time.sleep(5)
start_feed()
time.sleep(5)

call("python3.6 \"{0}\"".format(readwrite_py), shell=True)

