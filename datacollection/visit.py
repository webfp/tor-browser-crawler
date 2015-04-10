from selenium.webdriver.common.keys import Keys
from xvfbwrapper import Xvfb
from torutils import TorBrowserDriver
from log import wl_log
import os
import common as cm
from dumputils import Sniffer
import time
import utils as ut


ENABLE_XVFB = True  # enable x virtual frame buffer
ENABLE_XVFB = False  # disable x virtual frame buffer
BAREBONE_HOME_PAGE = "file://%s/barebones.html" % cm.ETC_DIR

VBOX_GATEWAY_IP = "10.0.2.2"  # default gateway IP of VirtualBox
LXC_GATEWAY_IP = "10.0.3.1"  # default gateway IP of LXC
LOCALHOST_IP = "127.0.0.1"  # default localhost IP


class Visit(object):
    '''Hold info about a particular visit to a page.'''

    def __init__(self, batch_num, site_num, instance_num, page_url,
                 base_dir, tbb_version, tor_controller, crawl, bg_site=None,
                 experiment=cm.EXP_TYPE_WANG_ET_AL):
        '''Create a new instance of visit'''
        self.batch_num = batch_num
        self.site_num = site_num
        self.instance_num = instance_num
        self.page_url = page_url
        self.bg_site = bg_site
        self.experiment = experiment
        self.base_dir = base_dir
        self.visit_dir = None
        self.visit_log_dir = None
        self.tbb_version = tbb_version
        self.tor_controller = tor_controller
        self.crawl = crawl
        self.init_visit_dir()
        self.pcap_path = os.path.join(self.visit_dir,
                                 "{}.pcap".format(self.get_instance_name()))

        #os.environ['NSPR_LOG_MODULES'] = "timestamp,nsHttp5,\
        #    nsSocketTransport:3,nsStreamPump:3,nsHostResolver:5"
        #os.environ['NSPR_LOG_FILE'] = os.path.join(self.visit_log_dir,
        #                                           "ffnspr.log")
        if ENABLE_XVFB:
            self.vdisplay = Xvfb(width=1280, height=720)
            self.vdisplay.start()

        if experiment == cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE:
            self.tb_driver = self.crawl.tb_driver  # refer to crawl's tbb
        else:
            # Create new instance of TorBrowser
            self.tb_driver = TorBrowserDriver(
                tbb_logfile_path=os.path.join(
                    self.visit_dir, "logs", "firefox.log"),
                tbb_version=tbb_version,
                page_url=page_url)

        self.sniffer = Sniffer()

    def init_visit_dir(self):
        '''Creates results and logs directories for this visit.'''
        # Create results related to this visit
        self.visit_dir, self.visit_log_dir = ut.create_visit_dir(
            self.base_dir, str(self.instance_num))

    def get_instance_name(self):
        '''Construct and return a pcap filename.'''
        inst_file_name = '{}_{}_{}'\
            .format(self.batch_num, self.site_num, self.instance_num)
        return inst_file_name

    def cleanup_visit(self):
        '''Kill sniffer and Tor browser in case they're running.'''
        wl_log.info("Cleaning up visit.")
        wl_log.info("Cancelling timeout")
        ut.cancel_timeout()

        if self.sniffer and self.sniffer.is_recording:
            wl_log.info("Stopping sniffer...")
            self.sniffer.stop_capture()
        # If we handle a keyboard interrupt we lose the browser at this point.
        # Then webdriver.quit throws exception
        # TODO investigate, though shouldn't be a big problem since we don't
        #    record anything at this point.
        if self.experiment != cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE:
            if self.tb_driver and self.tb_driver.is_running:
                # shutil.rmtree(self.tb_driver.prof_dir_path)
                wl_log.info("Quitting selenium driver...")
                self.tb_driver.quit()

        # close all open streams to prevent pollution
        self.tor_controller.close_all_streams()
        if ENABLE_XVFB:
            self.vdisplay.stop()

    def capture_screen(self):
        """Take a screen capture."""
        try:
            self.tb_driver.get_screenshot_as_file(
                os.path.join(self.visit_dir, 'screenshot.png'))
        except:
            wl_log.info("Exception while taking screenshot of: {}".
                        format(self.page_url))

    def get_wang_et_al(self):
        """Visit the site according to Wang et al.'s settings"""
        ut.timeout(cm.HARD_VISIT_TIMEOUT)  # set timeout to stop the visit

        self.sniffer.start_capture(self.pcap_path,
                                   'tcp and not host %s and not host %s and not host %s'
                                   % (VBOX_GATEWAY_IP, LOCALHOST_IP, LXC_GATEWAY_IP))

        time.sleep(cm.PAUSE_BETWEEN_INSTANCES)
        try:
            self.tb_driver.set_page_load_timeout(cm.HARD_VISIT_TIMEOUT)
        except:
            wl_log.info("Exception setting a timeout {}".
                          format(self.page_url))

        wl_log.info("Crawling URL: {}".format(self.page_url))

        t1 = time.time()
        self.tb_driver.get(self.page_url)
        page_load_time = time.time() - t1
        wl_log.info("{} loaded in {} sec"
                    .format(self.page_url, page_load_time))
        self.capture_screen()
        time.sleep(cm.WAIT_IN_SITE)

        self.cleanup_visit()

    def get_multitab_fixedbg(self):
        ut.timeout(cm.HARD_VISIT_TIMEOUT)  # set timeout to stop the visit

        # load tor home page - dummy site needed to send keys
        self.sniffer.start_capture(self.pcap_path,
                                   'tcp and not host %s and not host %s'
                                   % (VBOX_GATEWAY_IP, LOCALHOST_IP))

        time.sleep(cm.PAUSE_BETWEEN_INSTANCES)
        try:
            self.tb_driver.set_page_load_timeout(cm.HARD_VISIT_TIMEOUT)
        except:
            wl_log.info("Exception setting a timeout {}".
                          format(self.page_url))

        wl_log.info("Crawling URL: {} with {} in the background".
                      format(self.page_url, self.bg_site))

        body = self.tb_driver.find_element_by_tag_name("body")
        body.send_keys(Keys.CONTROL + 't')  # open a new tab

        t1 = time.time()
        self.tb_driver.get(self.page_url)  # load the real site in second tab
        page_load_time = time.time() - t1

        wl_log.info("{} loaded in {} sec"
                    .format(self.page_url, page_load_time))
        self.capture_screen()
        time.sleep(cm.WAIT_IN_SITE)
        try:
            self.tb_driver.get_screenshot_as_file(os.path.join(self.visit_dir,
                                                            'screenshot.png'))
        except:
            wl_log.info("Exception while taking screenshot of: {}".
                          format(self.page_url))

        body = self.tb_driver.find_element_by_tag_name("body")
        body.send_keys(Keys.CONTROL + 'w')  # open a new tab

        self.cleanup_visit()

    def get_multitab(self):
        PAUSE_BETWEEN_TAB_OPENINGS = 0.5
        ut.timeout(cm.HARD_VISIT_TIMEOUT)  # set timeout to kill running processes

        # load tor home page - dummy site needed to send keys
        self.tb_driver.get(BAREBONE_HOME_PAGE)
        self.sniffer.start_capture(self.pcap_path,
                                   'tcp and not host %s and not host %s'
                                   % (VBOX_GATEWAY_IP, LOCALHOST_IP))

        time.sleep(cm.PAUSE_BETWEEN_INSTANCES)
        try:
            self.tb_driver.set_page_load_timeout(cm.HARD_VISIT_TIMEOUT)
        except:
            wl_log.info("Exception setting a timeout {}".
                          format(self.page_url))

        wl_log.info("Crawling URL: {} with {} in the background".
                      format(self.page_url, self.bg_site))

        body = self.tb_driver.find_element_by_tag_name("body")
        body.send_keys(Keys.CONTROL + 't')  # open a new tab
        body.send_keys('%s\n' % self.bg_site)  # load the background site

        # the delay between loading of background and real sites
        time.sleep(PAUSE_BETWEEN_TAB_OPENINGS)

        body = self.tb_driver.find_element_by_tag_name("body")
        body.send_keys(Keys.CONTROL + 't')  # open a new tab

        t1 = time.time()
        self.tb_driver.get(self.page_url)  # load the real site in second tab

        page_load_time = time.time() - t1
        wl_log.info("{} loaded in {} sec"
                    .format(self.page_url, page_load_time))
        # self.capture_screen() !!! commented as this causes freeze
        time.sleep(cm.WAIT_IN_SITE)
        try:
            self.tb_driver.get_screenshot_as_file(os.path.join(self.visit_dir,
                                                            'screenshot.png'))
        except:
            wl_log.info("Exception while taking screenshot of: {}".
                          format(self.page_url))
        self.cleanup_visit()

    def get(self, ip_entry_guard=None):
        '''Call the actual visit function'''
        if self.experiment == cm.EXP_TYPE_WANG_ET_AL:
            self.get_wang_et_al()
        elif self.experiment == cm.EXP_TYPE_MULTITAB_ALEXA:
            self.get_multitab()
        elif self.experiment == cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE:
            self.get_multitab_fixedbg()
        else:
            wl_log.critical("Cannot determine experiment type")
