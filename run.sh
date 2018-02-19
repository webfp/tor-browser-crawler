#!/bin/bash
cd ~/tor-browser-crawler
export PYTHONPATH=$PYTHONPATH:$HOME/tor-browser-crawler/onionperf/
source $HOME/.virtualenvs/tb-crawler/bin/activate
python bin/tbcrawler.py -t WebFP -u ./etc/onionservices_7075.txt --tor-binary-path `pwd`/tor/src/or/tor --tor-data-path `pwd`/tor-browser_en-US/Browser/TorBrowser/Data/
