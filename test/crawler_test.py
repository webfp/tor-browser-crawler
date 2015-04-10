import unittest
from datacollection.crawler import Crawler
import common as cm

TEST_URL_LIST = ['https://check.torproject.org',
                 'https://www.google.de',
                 'http://nytimes.com']


class Test(unittest.TestCase):

    def test_crawl(self):
        crawler = Crawler(cm.TORRC_WANG_AND_GOLDBERG, TEST_URL_LIST,
                          cm.TBB_DEFAULT_VERSION)
        try:
            crawler.crawl(1, 1)  # we can pass batch and instance numbers
        except Exception as e:
            self.fail("It raised an exception: %s" % e)
        # TODO reduce test duration, check expected conditions


if __name__ == "__main__":
    unittest.main()
