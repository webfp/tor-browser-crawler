from os.path import join
from pprint import pformat
from time import sleep
from shutil import copytree

from selenium.common.exceptions import TimeoutException, WebDriverException

import common as cm
import utils as ut
from dumputils import Sniffer
from log import wl_log

# pauses
PAUSE_BETWEEN_BATCHES = 5    # pause between two batches
PAUSE_BETWEEN_SITES = 5      # pause before crawling a new site
PAUSE_BETWEEN_VISITS = 4  # pause before visiting the same site (instances)
PAUSE_IN_SITE = 5            # time to wait after the page loads



class CrawlerBase(object):
    def __init__(self, driver, controller, screenshots=True):
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
            for job.site in xrange(len(job.urls)):
                if len(job.url) > cm.MAX_FNAME_LENGTH:
                    wl_log.warning("URL is too long: %s" % job.url)
                    continue
                self.__do_instance(job)
                sleep(PAUSE_BETWEEN_SITES)

    def __do_instance(self, job):
        for job.visit in xrange(job.visits):
            ut.create_dir(job.path)
            wl_log.info("*** Visit #%s to %s ***" % (job.visit, job.url))
            with self.driver.launch():
                try:
                    self.driver.set_page_load_timeout(cm.SOFT_VISIT_TIMEOUT)
                except WebDriverException as wbd_exc:
                    wl_log.error("Setting soft timeout %s", wbd_exc)
                self.__do_visit(job)
                if self.screenshots:
                    self.driver.get_screenshot_as_file(job.png_file)
            sleep(PAUSE_BETWEEN_VISITS)
            self.post_visit(job)

    def __do_visit(self, job):
        with Sniffer(path=job.pcap_file, filter=cm.DEFAULT_FILTER):
            try:
                with ut.timeout(cm.HARD_VISIT_TIMEOUT):
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
		
		# copy browser profile before closing driver
		visit_pofile = join(job.path, 'profile')
		ut.create_dir(visit_profile)
		copytree(self.driver.temp_profile_path, visit_profile)


class CrawlJob(object):
    def __init__(self, batches, urls, visits):
        self.urls = urls
        self.visits = visits
        self.batches = batches

        # state
        self.site = 0
        self.visit = 0
        self.batch = 0

    @property
    def pcap_file(self):
        return join(self.path, "capture.pcap")

    @property
    def png_file(self):
        return join(self.path, "screenshot.png")

    @property
    def instance(self):
        return self.batch * self.visits + self.visit

    @property
    def url(self):
        return self.urls[self.site]

    @property
    def path(self):
        attributes = [self.batch, self.site, self.instance]
        return "_".join(map(str, attributes))

    def __repr__(self):
        return "Batches: %s, Sites: %s, Visits: %s" \
               % (self.batches, len(self.urls), self.visits)
