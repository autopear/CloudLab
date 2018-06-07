#!/bin/sh

ssh -n -f node1 "sh -c 'mkdir -p /home/ubuntu/asterixdb/logs; nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-1-service.log 2>&1 &'"
ssh -n -f node2 "sh -c 'mkdir -p /home/ubuntu/asterixdb/logs; nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-2-service.log 2>&1 &'"
ssh -n -f node3 "sh -c 'mkdir -p /home/ubuntu/asterixdb/logs; nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-3-service.log 2>&1 &'"
ssh -n -f node4 "sh -c 'mkdir -p /home/ubuntu/asterixdb/logs; nohup /home/ubuntu/asterixdb/bin/asterixncservice > /home/ubuntu/asterixdb/logs/node-4-service.log 2>&1 &'"
