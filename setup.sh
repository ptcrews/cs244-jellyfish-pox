#!/bin/bash

sudo apt install -y python-pip
sudo apt install -y mininet
sudo apt install -y python-tk
pip install matplotlib

sudo apt-get remove iperf3
sudo apt-get purge iperf3
sudo apt-get autoremove
cd ..
git clone https://github.com/esnet/iperf.git
cd iperf
git checkout 3.5
./bootstrap.sh
./configure
make
sudo make install
sudo ldconfig
cd ../cs244-jellyfish-pox



