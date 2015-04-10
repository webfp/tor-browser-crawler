from log import wl_log, add_log_file_handler, add_symlink
from random import choice
from selenium.common.exceptions import TimeoutException
from torutils import TorBrowserDriver, TorController
from visit import Visit
import common as cm
import os
import time
import utils as ut


# timeouts and pauses
PAUSE_BETWEEN_SITES = 5      # pause before crawling a new site

# defaults for batch and instance numbers
NUM_BATCHES = 10
NUM_INSTANCES = 4
MAX_SITES_IN_BATCH = 9999999999  # don't impose a limit with that constant

CRAWL_DEBUG = False
# CRAWL_DEBUG = True
if CRAWL_DEBUG:
    NUM_INSTANCES = 2
    MAX_SITES_IN_BATCH = 2
    NUM_BATCHES = 2

BG_SITES = ("http://facebook.com", "http://gmail.com", "http://twitter.com")
MAX_SITES_PER_TOR_PROCESS = 100  # reset tor process after crawling 100


class Crawler(object):
    '''Provides methods to collect traffic traces.'''

    def __init__(self, torrc_dict, url_list, tbb_version,
                 experiment=cm.EXP_TYPE_WANG_ET_AL):
        # Create instance of Tor controller and sniffer used for the crawler
        self.crawl_dir = None
        self.crawl_logs_dir = None
        self.visit = None
        self.urls = url_list  # keep list of urls we'll visit
        self.init_crawl_dirs()  # initializes crawl_dir
        self.tor_log = os.path.join(self.crawl_logs_dir, "tor.log")
        linkname = os.path.join(cm.RESULTS_DIR, 'latest_tor_log')
        add_symlink(linkname, self.tor_log)
        self.tbb_version = tbb_version
        self.experiment = experiment
        self.tor_controller = TorController(torrc_dict, tbb_version,
                                            self.tor_log)
        self.tor_process = None
        self.tb_driver = None
        add_log_file_handler(wl_log, self.log_file)
        linkname = os.path.join(cm.RESULTS_DIR, 'latest_crawl_log')
        add_symlink(linkname, self.log_file)  # add a symbolic link

    def crawl(self, num_batches=NUM_BATCHES,
              num_instances=NUM_INSTANCES, start_line=0):
        wl_log.info("Crawl params batches: %s instances: %s **********" %
                    (num_batches, num_instances))
        # for each batch
        for batch_num in xrange(num_batches):
            wl_log.info("********** Starting batch %s **********" % batch_num)
            site_num = start_line
            bg_site = None
            batch_dir = ut.create_dir(os.path.join(self.crawl_dir,
                                                   str(batch_num)))
            # init/reset tor process to have a different circuit.
            # make sure that we're not using the same guard node again
            wl_log.info("********** Restarting Tor Before Batch **********")
            self.tor_controller.restart_tor()
            sites_crawled_with_same_proc = 0

            # for this experiment we need a browser that runs during batch
            if self.experiment == cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE:
                # Create new instance of TorBrowser
                self.tb_driver = TorBrowserDriver(
                    tbb_logfile_path=os.path.join(
                        self.crawl_dir, "logs", "firefox.log"),
                    tbb_version=self.tbb_version, page_url="")
                bg_site = BG_SITES[batch_num]
                self.tb_driver.get(bg_site)
            # for each site
            for page_url in self.urls[:MAX_SITES_IN_BATCH]:
                sites_crawled_with_same_proc += 1
                if sites_crawled_with_same_proc > MAX_SITES_PER_TOR_PROCESS:
                    wl_log.info("********** Restarting Tor Process **********")
                    self.tor_controller.restart_tor()
                    sites_crawled_with_same_proc = 0

                wl_log.info("********** Crawling %s **********" % page_url)
                page_url = page_url[:cm.MAX_FNAME_LENGTH]
                site_dir = ut.create_dir(os.path.join(batch_dir,
                                                      ut.get_filename_from_url(page_url, site_num)))

                if self.experiment == cm.EXP_TYPE_MULTITAB_ALEXA:
                    bg_site = choice(self.urls)
                # for each visit
                for instance_num in range(num_instances):
                    wl_log.info("********** Visit #%s to %s **********" %
                                (instance_num, page_url))
                    self.visit = None
                    try:
                        self.visit = Visit(batch_num, site_num,
                                           instance_num, page_url,
                                           site_dir, self.tbb_version,
                                           self.tor_controller, self, bg_site,
                                           self.experiment)

                        self.visit.get()
                    except KeyboardInterrupt:  # CTRL + C
                        raise KeyboardInterrupt
                    except (ut.TimeExceededError, TimeoutException):
                        wl_log.critical("Visit to %s timed out!" % page_url)
                        if self.visit:
                            self.visit.cleanup_visit()
                    except Exception:
                        wl_log.critical("Exception crawling %s" % page_url,
                                        exc_info=True)
                        if self.visit:
                            self.visit.cleanup_visit()
                # END - for each visit
                site_num += 1
                time.sleep(PAUSE_BETWEEN_SITES)

            if self.experiment == cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE and \
                    self.tb_driver and self.tb_driver.is_running:
                wl_log.info("Quitting selenium driver...")
                self.tb_driver.quit()

    def init_crawl_dirs(self):
        '''Creates results and logs directories for this crawl.'''
        self.crawl_dir, self.crawl_logs_dir = ut.create_crawl_dir(cm.BASE_DIR)
        sym_link = os.path.join(cm.RESULTS_DIR, 'latest')
        add_symlink(sym_link, self.crawl_dir)  # add a symbolic link
        # Create crawl log
        self.log_file = os.path.join(self.crawl_logs_dir, "crawl.log")

    def init_logger(self):
        '''Configure logging for crawler.'''
        add_log_file_handler(wl_log, self.log_file)

        #linkname = os.path.join(cm.BASE_FP_LOGS_FOLDER, 'latest')
        #add_symlink(linkname, log_filename)

    def stop_crawl(self, pack_results=True):
        ''' Cleans up crawl and kills tor process in case it's running.'''
        wl_log.info("Stopping crawl...")
        if self.visit:
            self.visit.cleanup_visit()
        self.tor_controller.kill_tor_proc()
        if pack_results:
            ut.pack_crawl_data(self.crawl_dir)
