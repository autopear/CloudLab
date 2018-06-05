#!/bin/sh

sudo apt-get install -y python-software-properties debconf-utils
sudo add-apt-repository -y ppa:webupd8team/java
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections
sudo apt-get install -y oracle-java8-installer maven unzip git-core python3.6 python3.6-dev unzip curl
curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6
sudo pip3.6 install requests
git clone https://github.com/autopear/CloudLab.git /home/ubuntu/cloudlab
unzip /home/ubuntu/cloudlab/asterix-server-0.9.4-SNAPSHOT-binary-assembly.zip -d /home/ubuntu/asterixdb
sudo chown -R ubuntu:ubuntu /home/ubuntu/*
