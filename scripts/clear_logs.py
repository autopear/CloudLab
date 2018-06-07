#!/usr/bin/python3.6

import os
import sys


if __name__ == "__main__":
    for i in range(1, len(sys.argv)):
        inp = sys.argv[i]
        logf = open(inp, "w")
        logf.close()
        print("Cleared " + inp)
    print("Done")
