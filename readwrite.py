#!/usr/bin/python3.6

import requests
import os
from subprocess import call


dir_path = os.path.dirname(os.path.realpath(__file__))
res_path = os.path.join(dir_path, "results")

ycsb = os.path.join(dir_path, "ycsb-0.14.0-SNAPSHOT", "bin", "ycsb")

config_path = os.path.join(dir_path, "configs", "readwrite")


def worker():
    log_prefix = os.path.join(res_path, "readwrite")
    cmd = "python3.6 \"{0}\" run asterixdb -P \"{1}\" -p exportfile=\"{2}.txt\" -s -threads 1 > \"{2}.log\""\
        .format(ycsb, config_path, log_prefix)
    call(cmd, shell=True)


if __name__ == '__main__':
    if not os.path.isdir(res_path):
        os.mkdir(res_path)
    worker()
