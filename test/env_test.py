import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import unittest
import common as cm
import commands


class Test(unittest.TestCase):
    def assert_py_pkg_installed(self, pkg_name):
        try:
            __import__(pkg_name)
        except:
            self.fail('Cannot find python package.\
                        Install it by sudo pip install %s' % pkg_name)

    def run_cmd(self, cmd):
        return commands.getstatusoutput('%s ' % cmd)

    def is_installed(self, pkg_name):
        """Check if a package is installed."""
        cmd = 'which %s' % pkg_name
        status, _ = self.run_cmd(cmd)
        return False if status else True

    def test_stem(self):
        self.assert_py_pkg_installed('stem')

    def test_argparse(self):
        self.assert_py_pkg_installed('argparse')

    def test_requests(self):
        self.assert_py_pkg_installed('requests')

    def test_tor_bin(self):
        self.assertTrue(self.is_installed('tor'),
                        'Cannot find tor binary on your system')

    def test_webfp_path(self):
        self.assertTrue(os.path.isdir(cm.BASE_DIR),
                        'Cannot find base dir path %s' % cm.BASE_DIR)

    def test_tb_bin_path(self):
        tb_bin_path = cm.get_tb_bin_path(version=cm.TBB_DEFAULT_VERSION)
        self.assertTrue(os.path.isfile(tb_bin_path),
                        'Cannot find Tor Browser binary path %s'
                        % tb_bin_path)

    def test_tbb_profile_path(self):
        tbb_profile_path = cm.get_tbb_profile_path(cm.TBB_DEFAULT_VERSION)
        self.assertTrue(os.path.isdir(tbb_profile_path),
                        'Cannot find Tor Browser profile dir %s'
                        % tbb_profile_path)

    def test_py_selenium_version(self):
        import selenium
        pkg_ver = selenium.__version__
        err_msg = "Python Selenium package should be greater than 2.7.32"
        min_v = 2
        min_minor_v = 37
        min_micro_v = 2
        version, minor_v, micro_v = pkg_ver.split('.')
        self.assertGreaterEqual(version, min_v, err_msg)
        self.assertGreaterEqual(minor_v, min_minor_v, err_msg)
        self.assertGreaterEqual(micro_v, min_micro_v, err_msg)


if __name__ == "__main__":
    unittest.main()
