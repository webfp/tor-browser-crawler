import commands
import platform
import re
import sys
import urllib
from genericpath import isfile
from hashlib import sha256
from os import mkdir, remove
from os.path import dirname, abspath, join, isdir
from subprocess import Popen
from xml.etree import ElementTree

BASE_DIR = abspath(dirname(__file__))
TBB_BASE_DIR = join(BASE_DIR, 'tbb')
TBB_DIR = join(TBB_BASE_DIR, 'tor-browser_en-US')
ETC_DIR = join(BASE_DIR, 'etc')
TBB_VERSION_FILE = join(ETC_DIR, 'release.xml')
TBB_VERSION_URL = "https://dist.torproject.org/torbrowser/update_2/release/Linux_x86_64-gcc3/x/en-US"
TBB_ARCHIVE_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/{0}/"
TBB_DEVS_KEY_FP = '0x4E2C6E8793298290'
CHECKSUM_FILE = "sha256sums-unsigned-build.txt"
CHECKSUM_FILE_URL = TBB_ARCHIVE_URL + CHECKSUM_FILE
CHECKSUM_FPATH = join(TBB_BASE_DIR, CHECKSUM_FILE)


class IntegrityCheckError(Exception):
    pass


class ExtractionError(Exception):
    pass


class DownloadError(Exception):
    pass


def get_latest_tor():
    """Download latest stable version and verify its signature."""
    version = tbb_stable_version()
    if version is None:
        raise DownloadError("Cannot find latest TBB stable version.")

    # download latest TBB
    tbb_filename = get_tbb_filename(version)
    tbb_path = join(TBB_BASE_DIR, tbb_filename)
    tbb_url = TBB_ARCHIVE_URL.format(version) + tbb_filename
    download_with_signature(tbb_url, TBB_BASE_DIR)
    download_with_signature(CHECKSUM_FILE_URL.format(version), TBB_BASE_DIR)

    # verify checksum
    if not is_checksum_correct(tbb_filename):
        raise IntegrityCheckError("Checksum of downloaded TBB is not correct.")

    # verify signature of downloaded TBB
    if not is_signature_valid(tbb_path + '.asc'):
        raise IntegrityCheckError("Invalid signature of TBB file!")
    return tbb_path


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
    arch = platform.architecture()[0][:-3]
    return 'tor-browser-linux{0}-{1}_en-US.tar.xz'.format(arch, version)


def download_with_signature(file_url, dir_path):
    download(file_url, dir_path)
    download(file_url + '.asc', dir_path)


def download(file_url, dir_path):
    """Download a file to a directory."""
    fname = file_url.split("/")[-1]  # assumes no url params and others
    fpath = join(dir_path, fname)
    urllib.urlretrieve(file_url, fpath)


def extract_tarfile(file_path):
    """Extract a tarfile to the same directory."""
    dir_path = dirname(file_path)
    tar_cmd = "tar -xvf %s -C %s" % (file_path, dir_path)
    status, txt = commands.getstatusoutput(tar_cmd)

    if status or not isdir(TBB_DIR):
        raise ExtractionError("Error extracting TBB tarball %s: (%s: %s)"
                              % (tar_cmd, status, txt))


def is_signature_valid(sig_file):
    """Verify the signature of a file."""
    ret_code = Popen(['gpg', '--verify', sig_file]).wait()
    return True if ret_code == 0 else False


def is_checksum_correct(tbb_filename):
    # get SHA256 hash
    tarball_path = join(TBB_BASE_DIR, tbb_filename)
    with open(tarball_path, 'rb') as f:
        contents = f.read()
        sha256_sum = sha256(contents).hexdigest()

    # verify checksum file signature
    if not is_signature_valid(CHECKSUM_FPATH + '.asc'):
        raise IntegrityCheckError("Checksum file has not a valid signature.")

    with open(CHECKSUM_FPATH, 'rU') as checksum_file:
        for line in checksum_file:
            if tbb_filename in line:
                if sha256_sum.lower() in line.split()[0].lower():
                    return True
    return False


def import_gpg_key(key_fp):
    """Import GPG key with the given fingerprint."""
    # https://www.torproject.org/docs/verifying-signatures.html.en
    ret_code = Popen(['gpg', '--keyserver',
                      'x-hkp://pool.sks-keyservers.net',
                      '--recv-keys', key_fp]).wait()

    if ret_code != 0:
        raise IntegrityCheckError("Cannot import signing key.")


def remove_tbb_file(file_path):
    if isfile(file_path):
        remove(file_path)
    if isfile(file_path + '.asc'):
        remove(file_path + '.asc')


def tbb_setup(clean=False):
    # prepare directory
    if not isdir(TBB_BASE_DIR):
        mkdir(TBB_BASE_DIR)

    # import TBB devs gpg key
    try:
        import_gpg_key(TBB_DEVS_KEY_FP)
    except IntegrityCheckError as int_err:
        print("[setup] - Error on integrity check: %s" % int_err)
        sys.exit(-1)
    except DownloadError as dwn_err:
        print("[setup] - Error on download of files: %s" % dwn_err)
        sys.exit(-1)

    # get the latest tor
    try:
        tbb_path = get_latest_tor()
    except ExtractionError as ext_err:
        print("[setup] - Error when extracting tarball: %s" % ext_err)
        sys.exit(-1)

    # extract tar.xz
    extract_tarfile(tbb_path)

    # clean temp files
    if clean:
        remove_tbb_file(tbb_path)
        remove_tbb_file(CHECKSUM_FPATH)


if __name__ == '__main__':
    tbb_setup(clean=True)
