#!/bin/bash

rm -rf ./test_KSP_1/
rm -rf ./test_KSP_8/
rm -rf ./test_ECMP_1/
rm -rf ./test_ECMP_8/

mkdir test_KSP_1
mkdir test_KSP_8
mkdir test_ECMP_1
mkdir test_ECMP_8

# Set up test-specific variables
export N_PORTS=15
export INTER_PORTS=5
export NUM_SW=30
export SWITCH_BW=100
export HOST_BW=10

for ((i=0;i<5;i++))
do
  sudo mn -c && sudo -E TEST_NAME=KSP N_FLOWS=1 TEST_NUM=$i python2 ./build_topology.py
  sudo killall -9 dhclient
  sudo mn -c && sudo -E TEST_NAME=KSP N_FLOWS=8 TEST_NUM=$i python2 ./build_topology.py
  sudo killall -9 dhclient

  sudo mn -c && sudo -E TEST_NAME=ECMP N_FLOWS=1 TEST_NUM=$i python2 ./build_topology.py
  sudo killall -9 dhclient
  sudo mn -c && sudo -E TEST_NAME=ECMP N_FLOWS=8 TEST_NUM=$i python2 ./build_topology.py
  sudo killall -9 dhclient
done

python2 ./compute_average.py
