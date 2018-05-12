#!/bin/sh

sudo apt-get install -y python-software-properties debconf-utils
sudo add-apt-repository -y ppa:webupd8team/java
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections
sudo apt-get install -y oracle-java8-installer python3.6 python3.6-dev unzip git-core
git clone https://github.com/autopear/CloudLab.git ~/CloudLab
unzip ~/CloudLab/asterix-server-0.9.4-SNAPSHOT-binary-assembly.zip -d ~/CloudLab/asterixdb
