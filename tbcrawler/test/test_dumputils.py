import os
import pytest
import time
import unittest
import tempfile
from urllib2 import urlopen

from tbcrawler.dumputils import Sniffer

TEST_CAP_FILTER = 'host 255.255.255.255'
TEST_PCAP_FILE = tempfile.NamedTemporaryFile()
TEST_PCAP_PATH = TEST_PCAP_FILE.name


class SnifferTest(unittest.TestCase):

    def setUp(self):
        self.snf = Sniffer()

    def tearDown(self):
        pass

    @pytest.mark.skipif(bool(os.getenv('CI', False)), reason='Skip in CI')
    def test_is_dumpcap_running(self):
        self.snf.set_pcap_path(TEST_PCAP_PATH)
        self.snf.start_capture()
        self.assertTrue(self.snf.is_dumpcap_running())
        self.snf.stop_capture()
        if os.path.isfile(TEST_PCAP_PATH):
            os.remove(TEST_PCAP_PATH)

    def test_default_cap_filter(self):
        self.assertTrue(self.snf.get_capture_filter() == '')

    def test_default_pcap_path(self):
        self.assertTrue(self.snf.get_pcap_path() == '/dev/null')

    def test_set_pcap_path(self):
        self.snf.set_pcap_path(TEST_PCAP_PATH)
        self.assertTrue(TEST_PCAP_PATH == self.snf.get_pcap_path(),
                        "Sniffer pcap path cannot be set %s %s"
                        % (TEST_PCAP_PATH, self.snf.get_pcap_path()))

    def test_set_capture_filter(self):
        self.snf.set_capture_filter(TEST_CAP_FILTER)
        self.assertTrue(TEST_CAP_FILTER == self.snf.get_capture_filter(),
                        "Sniffer filter cannot be set %s %s"
                        % (TEST_CAP_FILTER, self.snf.get_capture_filter()))

    @pytest.mark.skipif(bool(os.getenv('CI', False)), reason='Skip in CI')
    def test_start_capture(self):
        if os.path.isfile(TEST_PCAP_PATH):
            os.remove(TEST_PCAP_PATH)
        self.snf.set_pcap_path(TEST_PCAP_PATH)
        self.snf.start_capture()
        time.sleep(1)
        f = urlopen("https://torproject.org/", timeout=10)
        self.assertTrue(f)
        self.snf.stop_capture()
        # TODO investigate why the we cannot capture on CI
        self.assertTrue(os.path.isfile(TEST_PCAP_PATH),
                        "Cannot find pcap file")
        self.assertGreater(os.path.getsize(TEST_PCAP_PATH), 0)
        os.remove(TEST_PCAP_PATH)

if __name__ == "__main__":
    unittest.main()
