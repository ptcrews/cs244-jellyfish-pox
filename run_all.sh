#!/bin/bash

git checkout fig9reproduce
cd pox/pox/ext
sudo mn -c && sudo python build_topology.py
sudo python construct_paths.py

git checkout topo_proactive
./run_tests.sh
