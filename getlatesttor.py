import platform
import re
import urllib
from os import mkdir, remove
from os.path import dirname, abspath, join, isdir
from xml.etree import ElementTree

import sys

BASE_DIR = abspath(dirname(__file__))
TBB_DIR = join(BASE_DIR, 'tbb')
ETC_DIR = join(BASE_DIR, 'etc')
TBB_VERSION_FILE = join(ETC_DIR, 'release.xml')
TBB_VERSION_URL = "https://dist.torproject.org/torbrowser/update_2/release/Linux_x86_64-gcc3/x/en-US"
TBB_ARCHIVE_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/{1}/{2}"


def get_latest_tor():
    """Download latest stable version and verify its signature."""
    version = tbb_stable_version()
    if version is None:
        raise Exception("Cannot find latest TBB stable version.")

    # download latest TBB
    tbb_filename = get_tbb_filename(version)
    tbb_path = join(TBB_DIR, tbb_filename)
    tbb_url = TBB_ARCHIVE_URL.format(version, tbb_filename)
    download(tbb_url, TBB_DIR)
    download(tbb_url + '.asc', TBB_DIR)

    # verify signature of downloaded TBB
    if is_signature_valid(tbb_path):
        raise Exception("Invalid signature of TBB file!")


def tbb_stable_version():
    """Return version of the latest TBB stable.

    Modified from: https://github.com/micahflee/torbrowser-launcher
    """
    urllib.urlretrieve(TBB_VERSION_URL, TBB_VERSION_FILE)
    tree = ElementTree.parse(TBB_VERSION_FILE)
    for up in tree.getroot():
        if up.tag == 'update' and up.attrib['appVersion']:
            version = str(up.attrib['appVersion'])
            if not re.match(r'^[a-z0-9\.\-]+$', version):
                return None
            return version
    return None


def get_tbb_filename(version):
    """Assume 'en-US' locale and new filename structure."""
    arch = platform.architecture()[0]
    return 'tor-browser-linux{1}-{2}_en-US.tar.xz'.format(arch, version)


def download(file_url, dir_path):
    """Download a file to a directory."""
    urllib.urlretrieve(file_url, join(dir_path, file_url))


def extract_tarfile(file_path):
    """Extract a tarfile to the same directory."""
    pass


def is_signature_valid(file_path):
    """Verify signature of a file."""
    pass


def tbb_setup(clean=False):
    if not isdir(TBB_DIR):
        mkdir(TBB_DIR)
    try:
        tbb_path = get_latest_tor()
    except Exception as e:
        print("[setup] - Exception: %s" % e)
        sys.exit(-1)
    extract_tarfile(tbb_path)
    if clean:
        remove(tbb_path)
        remove(tbb_path + '.asc')


if __name__ == '__main__':
    tbb_setup()
