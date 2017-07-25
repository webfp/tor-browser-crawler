#!/bin/bash

# configures and runs a crawl (inside a docker container)

# globals
BASE='/home/docker/tbcrawl'

# set offloads
ifconfig eth0 mtu 1500
ethtool -K eth0 tx off rx off tso off gso off gro off lro off

# install python requirements
pushd ${BASE}
pip install -U -r requirements.txt

# copy tor browser bundle
rm -rf tor-browser_en-US
cp -r /home/docker/tbb_setup/tor-browser_en-US .

# TODO: do other stuff here if you need to

# Run command with params
python bin/tbcrawler.py $1
