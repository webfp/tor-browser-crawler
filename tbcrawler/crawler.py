from os.path import join
from time import sleep

from selenium.common.exceptions import TimeoutException
from tbselenium.tbdriver import TorBrowserDriver

import tbcrawler.common as cm
from tbcrawler import utils as ut
from tbcrawler.dumputils import Sniffer
from tbcrawler.log import wl_log, add_log_file_handler, add_symlink
from torcontroller import TorController


class CrawlerBase(object):
    def __init__(self, output, torrc_dict, virt_display=False, capture=True):
        self.output = output
        self.torrc_dict = torrc_dict
        self.virt_display = virt_display
        self.capture = capture

    def post_crawl(self):
        pass

    def crawl(self, urls, batches, instances):
        wl_log.info("Crawl configuration:\n"
                    "\tpath: %s,\n"
                    "\tbatches: %s,\n"
                    "\tinstances: %s,\n"
                    "\tsites: %s"
                    % (cm.CRAWL_DIR, batches, instances, len(urls)))

        # for each batch
        for batch in xrange(batches):
            wl_log.info("********** Starting batch %s **********" % batch)
            batch_dir = ut.create_dir(join(cm.CRAWL_DIR, str(batch)))
            # init/reset tor process to have a different circuit.
            # make sure that we're not using the same guard node again
            wl_log.info("Restarting Tor before batch starts.")

            with TorController(cm.TBB_DEFAULT_DIR,
                               torrc_dict=self.torrc_dict,
                               pollute=False) as tor_controller:

                # for each site
                for i, url in enumerate(urls):
                    if len(url) > cm.MAX_FNAME_LENGTH:
                        wl_log.warning("Skipping URL because it's too long: %s" % url)
                        continue
                    site_dir = ut.create_dir(join(batch_dir, ut.get_filename_from_url(url, i)))

                    # for each instance
                    for instance in xrange(instances):
                        inst_dir = ut.create_dir(join(site_dir, str(instance)))
                        wl_log.info("********** Visit #%s to %s **********" % (instance, url))

                        with TorBrowserDriver(cm.TBB_DEFAULT_DIR,
                                              socks_port=tor_controller.socks_port,
                                              pref_dict=cm.FFPREFS,
                                              virt_display=self.virt_display,
                                              pollute=False) as tb_driver:
                            inst_fname = "_".join(map(str, [instance, i, batch]))
                            pcap_file = join(inst_dir, inst_fname + '.pcap')

                            with Sniffer(pcap_path=pcap_file, pcap_filter=cm.DEFAULT_FILTER) as sniffer:
                                try:
                                    ut.timeout(cm.HARD_VISIT_TIMEOUT)  # set timeout to stop the visit
                                    tb_driver.get(url)
                                    sleep(cm.PAUSE_BETWEEN_SITES)
                                    if self.capture:
                                        png_file = join(inst_dir, inst_fname + '.png')
                                        tb_driver.get_screenshot_as_png(png_file)
                                except (ut.TimeExceededError, TimeoutException) as exc:
                                    wl_log.critical("Visit to %s timed out! %s %s" %
                                                    (url, exc, type(exc)))
                                finally:
                                    ut.cancel_timeout()
                                    self.post_crawl()
