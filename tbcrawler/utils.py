import commands
import signal
from contextlib import contextmanager
from hashlib import sha256
from os import remove
from shutil import copyfile
from time import strftime
from urllib2 import urlopen

import psutil
from scapy.all import *

from log import wl_log


def get_hash_of_directory(path):
    """Return md5 hash of the directory pointed by path."""
    from hashlib import md5
    m = md5()
    for root, _, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            for line in open(full_path).readlines():
                m.update(line)
    return m.digest()


def create_dir(dir_path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def append_timestamp(_str=''):
    """Append a timestamp to a string and return it."""
    return _str + strftime('%y%m%d_%H%M%S')


def get_filename_from_url(url, prefix):
    """Return base filename for the url."""
    url = url.replace('https://', '')
    url = url.replace('http://', '')
    url = url.replace('www.', '')
    dashed = re.sub(r'[^A-Za-z0-9._]', '-', url)
    return '%s-%s' % (prefix, re.sub(r'-+', '-', dashed))


def is_targz_archive_corrupt(arc_path):
    # http://stackoverflow.com/a/2001749/3104416
    tar_gz_check_cmd = "gunzip -c %s | tar t > /dev/null" % arc_path
    tar_status, tar_txt = commands.getstatusoutput(tar_gz_check_cmd)
    if tar_status:
        wl_log.critical("Tar check failed: %s tar_status: %s tar_txt: %s"
                        % (tar_gz_check_cmd, tar_status, tar_txt))
        return tar_status
    return False  # no error


def pack_crawl_data(crawl_dir):
    """Compress the crawl dir into a tar archive."""
    if not os.path.isdir(crawl_dir):
        wl_log.critical("Cannot find the crawl dir: %s" % crawl_dir)
        return False
    if crawl_dir.endswith(os.path.sep):
        crawl_dir = crawl_dir[:-1]
    crawl_name = os.path.basename(crawl_dir)
    containing_dir = os.path.dirname(crawl_dir)
    os.chdir(containing_dir)
    arc_path = "%s.tar.gz" % crawl_name
    tar_cmd = "tar czvf %s %s" % (arc_path, crawl_name)
    wl_log.debug("Packing the crawl dir with cmd: %s" % tar_cmd)
    status, txt = commands.getstatusoutput(tar_cmd)
    if status or is_targz_archive_corrupt(arc_path):
        wl_log.critical("Tar command failed or archive is corrupt:\
                         %s \nSt: %s txt: %s" % (tar_cmd, status, txt))
        return False
    else:
        return True


def gen_all_children_procs(parent_pid):
    parent = psutil.Process(parent_pid)
    for child in parent.get_children(recursive=True):
        yield child


def kill_all_children(parent_pid):
    """Kill all child process of a given parent."""
    for child in gen_all_children_procs(parent_pid):
        child.kill()


def die(last_words="Unknown problem, quitting!"):
    wl_log.error(last_words)
    sys.exit(1)


def read_file(path, binary=False):
    """Read and return the file content."""
    options = 'rb' if binary else 'rU'
    with open(path, options) as f:
        return f.read()


def sha_256_sum_file(path, binary=True):
    """Return the SHA-256 sum of the file."""
    return sha256(read_file(path, binary=binary)).hexdigest()


def gen_read_lines(path):
    """Generator for reading the lines in a file."""
    with open(path, 'rU') as f:
        for line in f:
            yield line


def read_url(uri):
    """Fetch and return a URI content."""
    try:
        w = urlopen(uri)
        return w.read()
    except Exception as e:
        print "Error opening: {}".format(uri)
        print e


def write_to_file(file_path, data):
    """Write data to file and close."""
    with open(file_path, 'w') as ofile:
        ofile.write(data)


class HardTimeoutException(Exception): pass


@contextmanager
def timeout(seconds):
    """From: http://stackoverflow.com/a/601168/1336939 """
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def filter_pcap(pcap_path, iplist, strip=False, clean=True):
    orig_pcap = pcap_path + ".original"
    copyfile(pcap_path, orig_pcap)
    preader = PcapReader(orig_pcap)
    pcap_filtered = []
    for p in preader:
        if TCP in p:
            ip = p.payload
            if strip:
                p[TCP].remove_payload()  # stip payload (encrypted)
            if ip.dst in iplist or ip.src in iplist:
                pcap_filtered.append(p)
    wrpcap(pcap_path, pcap_filtered)
    remove(orig_pcap)

