from os.path import join
from pprint import pformat
from time import sleep

from selenium.common.exceptions import TimeoutException, WebDriverException

import common as cm
import utils as ut
from dumputils import Sniffer
from log import wl_log

# pauses
PAUSE_BETWEEN_BATCHES = 5    # pause between two batches
PAUSE_BETWEEN_SITES = 5      # pause before crawling a new site
PAUSE_BETWEEN_INSTANCES = 4  # pause before visiting the same site (instances)
PAUSE_IN_SITE = 5            # time to wait after the page loads

# timeouts
SOFT_VISIT_TIMEOUT = 120     # timeout used by selenium and dumpcap
# signal based hard timeout in case soft timeout fails
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10


class CrawlerBase(object):
    def __init__(self, controller, driver, screenshots=True):
        self.driver = driver
        self.controller = controller
        self.screenshots = screenshots

    def crawl(self, job):
        """Crawls a set of urls in batches."""
        wl_log.info("Starting new crawl")
        wl_log.info(pformat(job))
        for job.batch in xrange(job.batches):
            wl_log.info("**** Starting batch %s ***" % job.batch)
            self.__do_batch(job)
            sleep(PAUSE_BETWEEN_BATCHES)

    def post_visit(self, job):
        pass

    def __do_batch(self, job):
        """
        Must init/restart the Tor process to have a different circuit.
        If the controller is configured to not pollute the profile, each
        restart forces to switch the entry guard.
        """
        with self.controller.launch():
            for job.index, job.url, url in enumerate(job.urls):
                if len(job.url) > cm.MAX_FNAME_LENGTH:
                    wl_log.warning("URL is too long: %s" % job.url)
                    continue
                self.__do_instance(job)
                sleep(PAUSE_BETWEEN_SITES)

    def __do_instance(self, job):
        for job.visit in xrange(job.instances):
            ut.create_dir(job.path)
            wl_log.info("*** Visit #%s to %s ***" % (job.instance, job.url))
            with self.driver.launch():
                try:
                    self.driver.set_page_load_timeout(SOFT_VISIT_TIMEOUT)
                except WebDriverException as wbd_exc:
                    wl_log.error("Setting soft timeout %s", wbd_exc)
                self.__do_visit(job)
                if self.screenshots:
                    self.driver.get_screenshot_as_png(job.png_file)
            sleep(PAUSE_BETWEEN_INSTANCES)
            self.post_visit(job)

    def __do_visit(self, job):
        with Sniffer(path=job.pcap_file, filter=cm.DEFAULT_FILTER):
            try:
                with ut.timeout(HARD_VISIT_TIMEOUT):
                    self.driver.get(job.url)
                    sleep(PAUSE_IN_SITE)
            except (ut.HardTimeoutException, TimeoutException):
                wl_log.error("Visit to %s has timed out!" % job.url)


class CrawlerWebFP(CrawlerBase):

    def post_visit(self, job):
        guard_ips = set([ip for ip in self.controller.get_all_guard_ips()])
        wl_log.debug("Found %s guards in the consensus.", len(guard_ips))
        try:
            ut.filter_pcap(job.pcap_file, guard_ips, strip=True)
        except Exception as e:
            wl_log.error("ERROR: filtering pcap file: %s.", e)
            wl_log.error("Check pcap: %s", job.pcap_file)


class CrawlJob(object):
    def __init__(self, batches, urls, visits):
        self.batches = batches
        self.urls = urls
        self.visits = visits

        # indices
        self.batch = 0
        self.site = 0
        self.visit = 0

    @property
    def pcap_file(self):
        return join(self.path, "capture.pcap")

    @property
    def png_file(self):
        return join(self.path, "screenshot.png")

    @property
    def instance(self):
        return self.batch * self.visit

    @property
    def url(self):
        return self.urls[self.site]

    @property
    def path(self):
        attributes = [self.batch, self.site.index, self.instance]
        return "_".join(map(str, attributes))

    # def __repr__(self):
    #     return 'node(' + repr(self.name) + ', ' + repr(self.contents) + ')'
