import os
import unittest
import utils as ut
from time import sleep
import common as cm
import commands as cmds


class UtilsTest(unittest.TestCase):

    def test_get_filename_from_url(self):
        filename = ut.get_filename_from_url("http://google.com", 0)
        self.assertEqual("0-google.com", filename)
        filename = ut.get_filename_from_url("https://yahoo.com", 99)
        self.assertEqual("99-yahoo.com", filename)
        filename = ut.get_filename_from_url("https://123abc.com/somepath", 999)
        self.assertEqual("999-123abc.com-somepath", filename)
        filename = ut.get_filename_from_url(
            "https://123abc.com/somepath/", 123)
        self.assertEqual("123-123abc.com-somepath-", filename)
        filename = ut.get_filename_from_url(
            "https://123abc.com/somepath/q=query&q2=q2", 234)
        self.assertEqual("234-123abc.com-somepath-q-query-q2-q2", filename)

    def test_timeout(self):
        ut.timeout(1)
        try:
            sleep(1.1)
        except ut.TimeExceededError:
            pass  # this is what we want
        else:
            self.fail("Cannot set timeout")

    def test_cancel_timeout(self):
        ut.timeout(1)
        ut.cancel_timeout()
        try:
            sleep(1.1)
        except ut.TimeExceededError:
            self.fail("Cannot cancel timeout")

    def test_pack_crawl_data(self):
        self.assertTrue(ut.pack_crawl_data(cm.DUMMY_TEST_DIR))
        self.assertTrue(os.path.isfile(cm.DUMMY_TEST_DIR_TARGZIPPED))

        cmd = 'file "%s"' % cm.DUMMY_TEST_DIR_TARGZIPPED  # linux file command
        status, cmd_out = cmds.getstatusoutput(cmd)
        if not status:  # command executed successfully
            if 'gzip compressed data' not in cmd_out:
                self.fail("Cannot confirm file type")

        self.failIf(ut.is_targz_archive_corrupt(cm.DUMMY_TEST_DIR_TARGZIPPED))


if __name__ == "__main__":
    unittest.main()
