import subprocess
import tempfile
import unittest
from ConfigParser import RawConfigParser
from os.path import isdir
from shutil import rmtree
from time import sleep

from tbcrawler import utils as ut
from tbcrawler.common import CONFIG_FILE


class TimeoutTest(unittest.TestCase):
    def test_timeout(self):
        try:
            with ut.timeout(1):
                sleep(1.1)
        except ut.TimeoutException:
            pass  # test passes
        else:
            self.fail("Cannot set timeout")

    def test_cancel_timeout(self):
        try:
            with ut.timeout(1):
                sleep(0.9)
        except ut.TimeoutException:
            self.fail("Cannot cancel timeout")
        else:
            pass  # test passes


class DirectoryUtilsTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        if isdir(self.tempdir):
            rmtree(self.tempdir)

    def test_create_non_existing(self):
        self.tempdir = tempfile.mkdtemp()
        rmtree(self.tempdir)
        try:
            ut.create_dir(self.tempdir)
        except:
            self.fail("shouldn't raise")

    def test_create_existing(self):
        try:
            ut.create_dir(self.tempdir)
        except:
            self.fail("shouldn't raise")

    def test_clone_dir_temporary(self):
        tmpdir = ut.clone_dir_temporary(self.tempdir)
        self.assertTrue(isdir(tmpdir))


class ProcessUtilsTests(unittest.TestCase):
    # only linux!
    def test_gen_all_children_procs_of_non_shell_parent(self):
        parent = subprocess.Popen(['/bin/sleep', '1'])
        children = len(list(ut.gen_all_children_procs(parent.pid)))
        self.assertEqual(children, 0)

    def test_gen_all_children_procs_of_shell(self):
        parent = subprocess.Popen('/bin/sleep 1', shell=True)
        children = len(list(ut.gen_all_children_procs(parent.pid)))
        self.assertEqual(children, 1)

    def test_kill_all_children(self):
        parent = subprocess.Popen('/bin/sleep 1', shell=True)
        ut.kill_all_children(parent.pid)
        children = len(list(ut.gen_all_children_procs(parent.pid)))
        self.assertEqual(children, 0)


class ConfigUtilsTests(unittest.TestCase):
    def test_get_dict_subconfig(self):
        config = RawConfigParser()
        config.read(CONFIG_FILE)
        d = ut.get_dict_subconfig(config, 'default', 'torrc')
        self.assertDictEqual(d, {'controlport': '9051',
                                 'socksport': '9050',
                                 'socksbindaddress': '127.0.0.1'})


if __name__ == "__main__":
    unittest.main()
