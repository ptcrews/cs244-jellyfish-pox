#!/bin/bash

sudo apt install -y python-pip
sudo apt install -y mininet
sudo apt install -y python-tk
pip install matplotlib

sudo apt-get remove iperf3
sudo apt-get purge iperf3
sudo apt-get autoremove
git clone https://github.com/esnet/iperf.git
cd iperf
./configure
make
make install
cd ..



