#!/bin/sh

ssh -n -f node1 "sh -c 'cat /dev/null > /home/ubuntu/asterixdb/logs/node-1-service.log; cat /dev/null > /home/ubuntu/asterixdb/logs/nc-node_1.log'"
ssh -n -f node2 "sh -c 'cat /dev/null > /home/ubuntu/asterixdb/logs/node-2-service.log; cat /dev/null > /home/ubuntu/asterixdb/logs/nc-node_2.log'"
ssh -n -f node3 "sh -c 'cat /dev/null > /home/ubuntu/asterixdb/logs/node-3-service.log; cat /dev/null > /home/ubuntu/asterixdb/logs/nc-node_3.log'"
ssh -n -f node4 "sh -c 'cat /dev/null > /home/ubuntu/asterixdb/logs/node-4-service.log; cat /dev/null > /home/ubuntu/asterixdb/logs/nc-node_4.log'"
