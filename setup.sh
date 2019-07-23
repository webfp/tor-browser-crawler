#!/bin/bash
PYTHON_VERSION='python2.7'
PYTHON_PATH=`which $PYTHON_VERSION`

# absolute pwd
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# install dependencies
#!/bin/bash

if [ ! -f .installed ]; then
  INSTALLED=0
else
  source .installed
fi

if [ $INSTALLED -ne 1 ]; then
  apt=`command -v apt-get`
  if [ -n "$apt" ]; then
    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install --yes --force-yes git build-essential autoconf libtool libevent-dev libssl-dev zip unzip
    sudo apt-get install --yes --force-yes python  python-dev python-setuptools
	sudo apt-get install --yes --force-yes ethtool tcpdump tshark libpcap-dev 
    sudo apt-get install --yes --force-yes Xvfb iceweasel
	echo "INSTALLED=1" > .installed
  else
  	echo "WARN: this script assumes apt-get installed, you may need to install dependencies by hand.\n\n"
  fi
else
	echo "INFO: skipping package installation and configuration"
fi

# permissions: capture capabilities
sudo setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap

# set offloads
sudo ifconfig eth0 mtu 1500
sudo ethtool -K eth0 tx off rx off tso off gso off gro off lro off

sudo easy_install pip
sudo pip2.7 install virtualenv

# set virtual environment
rm -rf ${BASE}/venv
virtualenv --no-site-packages -p $PYTHON_PATH ${BASE}/venv
source venv/bin/activate

pip2.7 install -r requirements.txt

# compile tor
cd ../tor/
git checkout -b tor-signaling origin/tor-signaling
sudo -u $USER git pull
sh autogen.sh && ./configure --disable-asciidoc && make
cd ../crawler/
mv ../tor/src/or/tor tor-browser_en-US/Browser/TorBrowser/Tor/

# clone torbutton repo
rm -rf torbutton
git clone https://git.torproject.org/user/gk/torbutton.git -b rob
cp ../tor/test_url_cell/torbutton.patch torbutton/

# apply patch
cd ${BASE}/torbutton
patch -p1 < torbutton.patch
./makexpi.sh
cd ${BASE}

# replace extension in TBB
mv ${BASE}/torbutton/pkg/torbutton-1.9.6.1.xpi ${BASE}/tor-browser_en-US/Browser/TorBrowser/Data/Browser/profile.default/extensions/torbutton@torproject.org.xpi

# TODO: check enable swap
# check if swap exists [ 1 == `sudo swapon -s | wc -l` ]
# sudo fallocate -l 4G /swapfile
# sudo chmod 600 /swapfile
# sudo mkswap /swapfile
# sudo swapon /swapfile
# sudo echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab

# set onionperf
rm -rf ${BASE}/onionperf
cd ${BASE}
export PYTHONPATH=$PYTHONPATH:${BASE}/onionperf/
git clone https://github.com/robgjansen/onionperf.git

# Run
#python bin/tbcrawler.py -c middle -t WebFP -u ../onions/frontpage_up.onions -s -e ./addons/httpdump
#python bin/tbcrawler.py -c middle -t WebFP -u ../onions/frontpage_up.onions -s -a ./addons/httpdump/ -o results/161125_124213 -r results/161125_124213/job.chkpt
#python2.7 bin/tbcrawler.py -c middle -t WebFP -u ../onions/frontpage_up.onions -s
