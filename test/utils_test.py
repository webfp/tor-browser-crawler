import unittest
from os import rmdir
from os.path import join, basename
from utils import create_dir, get_latest_dir
from common import TEMP_DIR
import utils as ut


class Test(unittest.TestCase):

    def test_get_latest_dir(self):
        dir_test = join(TEMP_DIR, "dir_test")
        create_dir(dir_test)
        latest_dir = get_latest_dir(TEMP_DIR)
        self.assertEqual(basename(dir_test), latest_dir,
                         "Latest dir %s doesn't match with the expected dir %s"
                         % (latest_dir, dir_test))
        rmdir(dir_test)

    def test_get_info_from_filename(self):
        pcap_path = "/home/user/dev/webfp/crawls/crawl140210_201439"\
                    "/2/0-google.de/2/2_0_2.pcap"
        self.assertEqual(ut.get_info_from_filename(pcap_path),
                         [2, 0, 2])

if __name__ == "__main__":
    unittest.main()
