tor-browser-crawler [![Build Status](https://travis-ci.org/webfp/tor-browser-crawler.svg)](https://travis-ci.org/webfp/tor-browser-crawler)
===============
This repository contains the source code for the data collection part of our ACM CCS’14 paper [“A Critical Analysis of Website Fingerprinting Attacks”](http://homes.esat.kuleuven.be/~mjuarezm/index_files/pdf/ccs14.pdf) [1].

The crawler can be used in the similar website fingerprinting studies. It uses [Selenium](https://selenium-python.readthedocs.org/) to drive the **Tor Browser** and [stem](https://stem.torproject.org/) to control the tor. Our implementation started as a fork of  [tor-browser-selenium by  @isislovecruft](https://github.com/isislovecruft/tor-browser-selenium).

For the crawl parameters such as `batch` and `instance` refer to the ACM WPES’13 paper by Wang and Goldberg[2].

Requirements
---------------
* Linux packages: ```python tcpdump wireshark Xvfb```
* Python packages: ```selenium requests stem psutil xvfbwrapper```

# Getting started

### 1. Configure the environment

* We recommend running crawls in a VM or a container (e.g. LXC) to avoid perturbations introduced by the background network traffic and system level network settings. Please note that the crawler will not only store the Tor traffic but will capture all the network traffic generated during a visit to a website. That’s why it’s extremely important to disable all the automatic/background network traffic such as the auto-updates. See, for example the [instructions for disabling automatic connections for Ubuntu](https://help.ubuntu.com/community/AutomaticConnections).

* You’ll need to set capture capabilities to your user: `sudo setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap`

* [Download the TBB](https://www.torproject.org/download/download.html.en) and extract it to `./tbb/tor-browser-linux<arch>-<version>_<locale>/`.

* You might want to change the MTU of your network interface and disable NIC offloads that might make the traffic collected by tcpdump look different from how it would have been seen on the wire.

 * Change MTU to standard ethernet MTU (1500 bytes): `sudo ifconfig <interface> mtu 1500`

 * Disable offloads: `sudo ethtool -K <interface> tx off rx off tso off gso off`

 * See the [Wireshark Offloading page](https://wiki.wireshark.org/CaptureSetup/Offloading) for more info.



### 2. Run a crawl with the defaults:

```
python main.py -u ./etc/localized-urls-100-top.csv -e wang_and_goldberg
```

To get all the available command line parameters and the usage run:

```
python main.py --help
```

### 3. Check out the results

The collected data can be found in the `results` folder in the root directory. :

    * Pcaps: `./results/latest`
    * Logs: `./results/latest_crawl_log`


Data samples
-------------
You can download a sample of data collected using this crawler with the configuration used by Wang and Goldberg in their paper (namely 10 batches, 100 pages and 4 instances per page) from here:

* [Crawl `140203_042843`](TODO: url)

We earmark each crawl with the creation timestamp of the crawl. We appended a list of the `id` numbers of the crawls we used along with more details in the appendix of the paper [1].


Notes
-------
* Installed and tested in *xubuntu 14.04* and *debian 7.8*.


References
-------------

[1] M. Juarez, S. Afroz, G. Acar, C. Diaz, R. Greenstadt, “A Critical Analysis of Website Fingerprinting Attacks”, in the proceedings of the ACM Conference on Computer and Communications Security (CCS), pp. 263-274, ACM, 2014.

[2] T. Wang and I. Goldberg. “Improved Website Fingerprinting on Tor”, in the proceedings of the ACM Workshop on Privacy in the Electronic Society (WPES), pp. 201–212. ACM, 2013.
