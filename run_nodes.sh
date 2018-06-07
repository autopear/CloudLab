#!/bin/sh

ssh -n -f node1 "sh -c 'nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-1-service.log 2>&1 &'"
ssh -n -f node2 "sh -c 'nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-2-service.log 2>&1 &'"
