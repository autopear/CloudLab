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
if [[ ! -d /home/ubuntu/.ssh ]]; then
	mkdir -p /home/ubuntu/.ssh
	chmod 700 /home/ubuntu/.ssh
fi
mv /home/ubuntu/cloudlab/ssh/config /home/ubuntu/.ssh/config
chmod 644 /home/ubuntu/.ssh/id_rsa
mv /home/ubuntu/cloudlab/ssh/id_rsa /home/ubuntu/.ssh/id_rsa
chmod 600 /home/ubuntu/.ssh/id_rsa
mv /home/ubuntu/cloudlab/ssh/id_rsa.pub /home/ubuntu/.ssh/id_rsa.pub
chmod 644 /home/ubuntu/.ssh/id_rsa.pub
mv /home/ubuntu/cloudlab/ssh/authorized_keys /home/ubuntu/.ssh/authorized_keys
chmod 600 /home/ubuntu/.ssh/authorized_keys 
sudo chown -R ubuntu:ubuntu /home/ubuntu/*
