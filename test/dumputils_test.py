import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import unittest
from datacollection.dumputils import Sniffer
import time
import common as cm
TEST_CAP_FILTER = 'host 255.255.255.255'
TEST_PCAP_PATH = os.path.join(cm.TEST_DIR, 'test.pcap')


class SnifferTest(unittest.TestCase):

    def setUp(self):
        self.snf = Sniffer()

    def tearDown(self):
        pass

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

    def test_method_chanining(self):
        self.snf.set_capture_filter(TEST_CAP_FILTER).\
            set_pcap_path(TEST_PCAP_PATH)

        self.assertTrue(TEST_CAP_FILTER == self.snf.get_capture_filter(),
                        "Sniffer filter cannot be set %s %s"
                        % (TEST_CAP_FILTER, self.snf.get_capture_filter()))
        self.assertTrue(TEST_PCAP_PATH == self.snf.get_pcap_path(),
                        "Sniffer pcap path cannot be set %s %s"
                        % (TEST_PCAP_PATH, self.snf.get_pcap_path()))

    def test_start_capture(self):
        if os.path.isfile(TEST_PCAP_PATH):
            os.remove(TEST_PCAP_PATH)
        self.snf.set_pcap_path(TEST_PCAP_PATH)
        self.snf.start_capture()
        time.sleep(1)  # TODO add a urlopen to make sure we capture packet
        self.snf.stop_capture()
        self.assertTrue(os.path.isfile(TEST_PCAP_PATH),
                        "Cannot find pcap file")
        os.remove(TEST_PCAP_PATH)
        #  TODO add size check..

if __name__ == "__main__":
    unittest.main()
