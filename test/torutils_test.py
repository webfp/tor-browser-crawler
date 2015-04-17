import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import time
import unittest
import common as cm

from utils import get_hash_of_directory
from datacollection.torutils import TorBrowserDriver
from datacollection.torutils import TorController


class TestTorUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tor_controller = TorController(cm.TORRC_WANG_AND_GOLDBERG,
                                           cm.TBB_DEFAULT_VERSION)
        cls.tor_process = cls.tor_controller.launch_tor_service()

    def test_launch_tor_service(self):
        self.tor_process.kill()
        self.tor_process = self.tor_controller.launch_tor_service()
        self.assertTrue(self.tor_process, 'Cannot launch Tor process')

    def test_close_all_streams(self):
        streams_open = False
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get('http://www.google.com')
        time.sleep(cm.WAIT_IN_SITE)
        self.tor_controller.close_all_streams()
        for stream in self.tor_controller.controller.get_streams():
            print stream.id, stream.purpose, stream.target_address, "left open"
            streams_open = True
        new_tb_driver.quit()
        self.assertFalse(streams_open, 'Could not close all streams.')

    def test_tb_orig_profile_not_modified(self):
        """Visiting a site should not modify the original profile contents."""
        tbb_profile_dir = cm.get_tbb_profile_path(cm.TBB_DEFAULT_VERSION)
        profile_hash_before = get_hash_of_directory(tbb_profile_dir)
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get('https://www.google.com')
        new_tb_driver.quit()
        profile_hash_after = get_hash_of_directory(tbb_profile_dir)
        assert(profile_hash_after == profile_hash_before)

    def test_tb_driver_simple_visit(self):
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get('http://www.google.com')
        new_tb_driver.quit()

    def test_extensions_are_installed(self):
        # We only test HTTPS Everywhere, NoScript is not tested yet
        # https://gitweb.torproject.org/boklm/tor-browser-bundle-testsuite.git/tree/mozmill-tests/tbb-tests/https-everywhere.js
        HTTP_URL = "http://www.mediawiki.org/wiki/MediaWiki"
        HTTPS_URL = "https://www.mediawiki.org/wiki/MediaWiki"
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get(HTTP_URL)
        self.assertEqual(new_tb_driver.current_url, HTTPS_URL)
        new_tb_driver.quit()

    @classmethod
    def tearDownClass(cls):
        # cls.tor_process.kill()
        cls.tor_controller.kill_tor_proc()

if __name__ == "__main__":
    unittest.main()
