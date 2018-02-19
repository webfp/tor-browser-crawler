tor-browser-crawler [![Build Status](https://travis-ci.org/webfp/tor-browser-crawler.svg)](https://travis-ci.org/webfp/tor-browser-crawler)
===============
![DISCLAIMER](https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Dialog-warning-orange.svg/40px-Dialog-warning-orange.svg.png "experimental")  **experimental - PLEASE BE CAREFUL. Intended for reasearch purposes.**

*Version of the [tor-browser-crawler](http://github.com/webfp/tor-browser-crawler) that we used with Onionpop.*

We have freezed the repository with the source code that we used to collect data for our paper in NDSS 2018 [“Inside Job: Applying Traffic Analysis to Measure Tor from Within”](http://wp.internetsociety.org/ndss/wp-content/uploads/sites/25/2018/02/ndss2018_10-2_Jansen_paper.pdf).

The crawler uses a modified	`tor` to collect traces from a middle node. It is based on [Selenium](https://selenium-python.readthedocs.org/) to drive the **Tor Browser** and [stem](https://stem.torproject.org/) to control tor. Our implementation started as a fork of  [tor-browser-crawler](https://github.com/webfp/tor-browser-crawler) (by the @webfp team).

For the crawl parameters such as `batch` and `instance` refer to the ACM WPES’13 paper by Wang and Goldberg.

# Difference with respect to tor-browser-crawler

This crawler implements the functionality of `tor-browser-crawler` and extends
it to collect data from the middle position.  In particular, we use
[OnionPerf](https://github.com/robgjansen/onionperf) to collect cell-level
information. For ethical reasons, as we describe in the paper, we also
implement a signal mechanism that our crawler sends to specific middles in
order to tag circuits that our crawler has initiated, so that we do not capture
traffic from Tor users.

# Getting started

### 1. Configure the environment

* We recommend running crawls in a VM or a container (e.g. LXC) to avoid perturbations introduced by the background network traffic and system level network settings. Please note that the crawler will not only store the Tor traffic but will capture all the network traffic generated during a visit to a website. That’s why it’s extremely important to disable all the automatic/background network traffic such as the auto-updates. See, for example the [instructions for disabling automatic connections for Ubuntu](https://help.ubuntu.com/community/AutomaticConnections).

* You’ll need to set capture capabilities to your user: `sudo setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap`

* [Download the TBB](https://www.torproject.org/download/download.html.en) and extract it to `./tbb/tor-browser-linux<arch>-<version>_<locale>/`.

* You might want to change the MTU of your network interface and disable NIC offloads that might make the traffic collected by tcpdump look different from how it would have been seen on the wire.

 * Change MTU to standard ethernet MTU (1500 bytes): `sudo ifconfig <interface> mtu 1500`

 * Disable offloads: `sudo ethtool -K <interface> tx off rx off tso off gso off gro off lro off`

 * See the [Wireshark Offloading page](https://wiki.wireshark.org/CaptureSetup/Offloading) for more info.



### 2. Run a crawl with the defaults

```
python main.py -u ./etc/localized-urls-100-top.csv -e wang_and_goldberg
```

To get all the available command line parameters and the usage run:

```
python main.py --help
```

### 3. Check out the results

The collected data can be found in the `results` folder:

    * Pcaps: `./results/latest`
    * Logs: `./results/latest_crawl_log`

### Run multiple instances of the crawler (optional)

We also provide ansible roles to provision AWS images automatically. See the `AUTOMATION.md` readme for more info.

Notes
-------
* Tested on *Xubuntu 14.04* and *Debian 7.8*.

