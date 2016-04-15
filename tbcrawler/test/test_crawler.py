import os
import shutil
import unittest
from os.path import isfile, isdir

from tbcrawler import common as cm
from tbcrawler.crawler import CrawlerBase

TEST_URL_LIST = ['https://www.google.de',
                 'https://torproject.org',
                 'https://firstlook.org/theintercept/']


class CrawlerTest(unittest.TestCase):
    @unittest.skip("TODO. skip for now")
    def test_crawl(self):
        # this test takes at least a few minutes to finish
        crawler = CrawlerBase(cm.TORRC_WANG_AND_GOLDBERG, TEST_URL_LIST,
                              cm.TBB_DEFAULT_VERSION, capture_screen=True)
        try:
            crawler.crawl(1, 1)  # we can pass batch and instance numbers
        except Exception as e:
            self.fail("It raised an exception: %s" % e)
        self.assertTrue(isdir(crawler.crawl_dir))
        self.assertTrue(isdir(crawler.crawl_logs_dir))
        self.assertTrue(isfile(crawler.log_file))
        self.assertTrue(isfile(crawler.tor_log))
        self.assertEqual(crawler.experiment, cm.EXP_TYPE_WANG_AND_GOLDBERG)
        self.assertListEqual(crawler.urls, TEST_URL_LIST)
        self.assertEqual(crawler.tbb_version, cm.TBB_DEFAULT_VERSION)
        self.assertFalse(crawler.xvfb)
        crawler.stop_crawl(pack_results=True)
        tar_gz_crawl_data = crawler.crawl_dir + ".tar.gz"
        self.assertTrue(isfile(tar_gz_crawl_data))
        shutil.rmtree(crawler.crawl_dir)
        os.remove(tar_gz_crawl_data)


if __name__ == "__main__":
    unittest.main()
