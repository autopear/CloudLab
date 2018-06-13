#!/usr/bin/python3

import os
import requests
import time
from datetime import datetime
import threading
from subprocess import call, check_output


#table_paras = (0, 2, 3, 4, 5, 8, 10, 12, 15, 20, 25, 30, 40, 60, 80, 100, 150)
table_paras = (60, 80, 100, 150, 0)
bf_enabled = False

dir_path = os.path.dirname(os.path.realpath(__file__))
log_path = os.path.join(dir_path, "migration_logs")
if not os.path.isdir(log_path):
    os.mkdir(log_path)

task_running = False

def get_instance():
    res = check_output("nova list", shell=True)\
        .decode("utf-8").split("\n")
    fields = res[3].split("|")
    return fields[1].strip()


iid = get_instance()


class ThreadTask(threading.Thread):
    def __init__(self, enabled, k, is_load):
        threading.Thread.__init__(self)
        self.enabled = enabled
        self.k = k
        self.is_load = is_load

    def run(self):
        global task_running, sem
        if self.enabled:
            bf = "true"
        else:
            bf = "false"
        if self.is_load:
            op = "load"
        else:
            op = "read"

        print("Start experiment")
        flagf = os.path.join(dir_path, "{0}_{1}_done".format(op, self.k))
        if os.path.isfile(flagf):
            os.remove(flagf)
        call("ssh db3 \"nohup python3.6 /home/ubuntu/cloudlab/scripts/{0}_k.py {1} {2} &\""
             .format(op, bf, self.k), shell=True)
        while not os.path.isfile(flagf):
            time.sleep(1)
        print("Done experiment")

        task_running = False


class ThreadMigration(threading.Thread):
    def __init__(self, enabled, k, is_load, lp, uuid):
        threading.Thread.__init__(self)
        self.enabled = enabled
        self.k = k
        self.is_load = is_load
        self.lp = lp
        self.uuid = uuid

    def run(self):
        global task_running
        if self.enabled:
            bf = "with_bf"
        else:
            bf = "without_bf"
        if self.is_load:
            op = "load"
        else:
            op = "read"

        time.sleep(60)

        outf = open(os.path.join(self.lp, "{0}_{1}_{2}.log".format(op, bf, self.k)), "w")
        current_id = self.get_last_migration_id() + 1
        while task_running:
            print("{0} Migrating with {1}".format(datetime.now().strftime("%H:%M:%S.%f"), current_id))
            call("nova live-migration {0}".format(self.uuid), shell=True)
            while True:
                succ, st, ed = self.check_status(current_id)
                if succ == 1:
                    outf.write("{0}\t{1}\n"
                               .format(st.strftime("%Y-%m-%d %H:%M:%S.%f"), ed.strftime("%Y-%m-%d %H:%M:%S.%f")))
                    outf.flush()
                    print("{0} Done migration with {1}".format(datetime.now().strftime("%H:%M:%S.%f"), current_id))
                    break
                elif succ == -1:
                    break
                else:
                    time.sleep(0.5)
            current_id += 1
            if not task_running:
                break
            time.sleep(120)
        outf.close()

    def check_status(self, current_id):
        res = check_output("nova migration-list", shell=True).decode("utf-8").split("\n")
        for line in res:
            if line.startswith("|") and ("Source Node" not in line):
                fields = line.split("|")
                mid = int(fields[1].strip())
                if mid == current_id:
                    status = fields[7].strip()
                    if status == "preparing" or status == "running":
                        return 0, None, None
                    elif status == "completed":
                        start = fields[-4].strip()
                        start_dt = datetime.strptime(start + " +0000", "%Y-%m-%dT%H:%M:%S.%f %z")
                        end = fields[-3].strip()
                        end_dt = datetime.strptime(end + " +0000", "%Y-%m-%dT%H:%M:%S.%f %z")
                        return 1, start_dt, end_dt
                    else:
                        return -1, None, None
        return -1, None, None

    def get_last_migration_id(self):
        res = check_output("nova migration-list", shell=True).decode("utf-8").split("\n")
        last = 0
        for line in res:
            if line.startswith("|") and ("Source Node" not in line):
                fields = line.split("|")
                mid = int(fields[1].strip())
                if mid > last:
                    last = mid
        return last

    # def get_migration_list(self, last):
    #     res = check_output("ssh ctl \"source /root/setup/admin-openrc.sh && nova migration-list && exit\"", shell=True)\
    #         .decode("utf-8").split("\n")
    #     ret = []
    #     for line in res:
    #         if line.startswith("|") and ("Source Node" not in line):
    #             fields = line.split("|")
    #             mid = int(fields[1].strip())
    #             if mid > last:
    #                 status = fields[7].strip()
    #                 if status != "completed":
    #                     continue
    #
    #                 start = fields[-4].strip()
    #                 start_dt = datetime.strptime(start + " +0000", "%Y-%m-%dT%H:%M:%S.%f %z")
    #                 end = fields[-3].strip()
    #                 end_dt = datetime.strptime(end + " +0000", "%Y-%m-%dT%H:%M:%S.%f %z")
    #                 ret.append((start_dt, end_dt))
    #     return ret


def task(enabled, k):
    global task_running
    tload = ThreadTask(enabled, k, True)
    tmigload = ThreadMigration(enabled, k, True, log_path, iid)

    task_running = True
    tload.start()
    tmigload.start()

    tload.join()
    tmigload.join()

    tread = ThreadTask(enabled, k, False)
    tmigread = ThreadMigration(enabled, k, False, log_path, iid)

    task_running = True
    tread.start()
    tmigread.start()

    tread.join()
    tmigread.join()

    if enabled:
        print("Done with bloom filter K={0}".format(k))
    else:
        print("Done without bloom filter K={0}".format(k))


def all_tasks(enabled):
    for k in table_paras:
        task(enabled, k)


if __name__ == "__main__":
    all_tasks(bf_enabled)
