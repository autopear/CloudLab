#!/usr/bin/python3.6

import os
import gzip
import sys


if __name__ == "__main__":
    with gzip.open(sys.argv[1], "rt", encoding="utf-8") as inf:
        for line in inf:
            line = line.replace("\r", "").replace("\n", "")
            if len(line) > 0:
                print(line)
    inf.close()
