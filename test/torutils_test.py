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
        '''
        Must launch the Tor service.

        '''
        print "\ntest_launch_tor_service"
        self.tor_process.kill()
        self.tor_process = self.tor_controller.launch_tor_service()
        self.assertTrue(self.tor_process, 'Tor service is not running.')
        # tor_process.kill()

    def test_close_all_streams(self):
        '''Must close all streams.'''
        # create test streams
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
        '''Visiting a site should not modify the original profile contents.'''
        tbb_profile_dir = cm.get_tbb_profile_path(cm.TBB_DEFAULT_VERSION)
        profile_hash_before = get_hash_of_directory(tbb_profile_dir)
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get('https://www.google.com')
        new_tb_driver.quit()
        profile_hash_after = get_hash_of_directory(tbb_profile_dir)
        assert(profile_hash_after == profile_hash_before)

    # @unittest.skip("basic test to check that tor runs correctly.")
    def test_tb_driver_visit(self):
        new_tb_driver = TorBrowserDriver()
        new_tb_driver.get('http://www.google.com')
        new_tb_driver.quit()

    def test_extensions_are_installed(self):
        # TODO: add test to check if extensions are working correctly
        pass

    @classmethod
    def tearDownClass(cls):
        cls.tor_process.kill()

if __name__ == "__main__":
    unittest.main()
