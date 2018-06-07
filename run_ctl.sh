#!/bin/sh

mkdir -p /home/ubuntu/asterixdb/logs
/home/ubuntu/asterixdb/bin/asterixcc -config-file /home/ubuntu/asterixdb/opt/local/conf/cc_multi.conf > /home/ubuntu/asterixdb/logs/cc.log 2>&1 &
