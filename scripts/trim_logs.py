#!/usr/bin/python3.6

import os
import gzip
import sys


def copy_logs(input, outf):
    with open(input, "r") as inf:
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


if __name__ == "__main__":
    outp = sys.argv[1]
    print("Save to " + outp)
    outf = gzip.open(outp, "wt")
    for i in range(2, len(sys.argv)):
        inp = sys.argv[i]
        copy_logs(inp, outf)
        print("Processed " + inp)
    outf.close()
    print("Done")
