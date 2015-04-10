import os
import signal
import re
import commands
from time import strftime
from random import choice
import distutils.dir_util as du
import common as cm
from log import wl_log
from common import LOCALIZED_DATASET


# constants for random
ASCII_LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'

DEFAULT_RAND_STR_SIZE = 6
DEFAULT_RAND_STR_CHARS = ASCII_LOWERCASE_CHARS + DIGITS


def get_domain_name(index):
    with open(LOCALIZED_DATASET, "r") as fp:
        for i, line in enumerate(fp):
            if i == index:
                return line.strip()


def create_empty_file(filename):
    open(filename, 'a').close()


def get_info_from_filename(filename):
    """Return batch, rank, instance tuple from trace filename."""
    filename = os.path.split(filename)[-1]
    return map(int, filename[:-5].split("_"))


class TimeExceededError(Exception):
    pass


def count_number_lines(fname):
    """Return number of lines."""
    with open(fname) as f:
        for i, _ in enumerate(f):
            pass
    return i + 1


def get_latest_dir(path):
    """Return the most recently created directory."""
    all_dirs = [os.path.join(path, d) for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))]
    return os.path.basename(max(all_dirs, key=os.path.getmtime))


def get_hash_of_directory(path):
    '''
    Returns the md5 hash of the directory pointed by `path`

    '''
    from hashlib import md5
    m = md5()
    for root, _, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            for line in open(full_path).readlines():
                m.update(line)
    return m.digest()


def create_dir(dir_path):
    """Create a dir if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def append_timestamp(_str=''):
    """Append a timestamp and return it."""
    return _str + strftime('%y%m%d_%H%M%S')


def create_crawl_dir(base_dir):
    '''
    Checks and creates results directory and creates a timestamped directory
    for the current crawl.

    :Return: the path to the results directory.

    '''
    create_dir(cm.RESULTS_DIR)
    crawl_dir = os.path.join(cm.RESULTS_DIR, 'crawl')
    crawl_dir = create_dir(append_timestamp(crawl_dir))

    crawl_logs_dir = os.path.join(crawl_dir, 'logs')
    create_dir(crawl_logs_dir)
    return crawl_dir, crawl_logs_dir


def create_visit_dir(base_dir, visit_name):
    '''
    Checks and creates a directory for the current visit.

    :Return: the path to the visit directory.

    '''
    visit_dir = os.path.join(base_dir, visit_name)
    create_dir(visit_dir)
    visit_log_dir = os.path.join(visit_dir, 'logs')
    create_dir(visit_log_dir)
    return visit_dir, visit_log_dir


def clone_dir_with_timestap(orig_dir_path):
    '''
    Creates a new directory including timestamp in name
    and copies `orig_directory` into it

    :Return: the path to the directory copy.

    '''
    new_dir = create_dir(append_timestamp(orig_dir_path))
    try:
        du.copy_tree(orig_dir_path, new_dir)
    except Exception, e:
        wl_log.error(str(e))
    finally:
        return new_dir


def raise_signal(signum, frame):
    raise TimeExceededError


def timeout(duration):
    """Timeout after given duration."""
    signal.signal(signal.SIGALRM, raise_signal)  # linux only !!!
    signal.alarm(duration)  # alarm after X seconds


def cancel_timeout():
    signal.alarm(0)


def rand_str(size=DEFAULT_RAND_STR_SIZE, chars=DEFAULT_RAND_STR_CHARS):
    """Return random string given a size and character space."""
    return ''.join(choice(chars) for _ in range(size))


def get_filename_from_url(url, prefix):
    """Return base filename for the url."""
    url = url.replace('https://', '')
    url = url.replace('http://', '')
    url = url.replace('www.', '')
    dashed = re.sub(r'[^A-Za-z0-9._]', '-', url)
    return '%s-%s' % (prefix, re.sub(r'-+', '-', dashed))


def split_seq_of_n_elements(self, s, n):
    """Return the split of `s` in groups of n elements."""
    return [s[i:i+n] for i in range(0, len(s), n)]


def pack_crawl_data(crawl_dir):
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
    if status:
        wl_log.critical("Tar command failed: %s \nSt: %s txt: %s"
                        % (tar_cmd, status, txt))
    else:
        # http://stackoverflow.com/a/2001749/3104416
        tar_gz_check_cmd = "gunzip -c %s | tar t > /dev/null" % arc_path
        tar_status, tar_txt = commands.getstatusoutput(tar_gz_check_cmd)
        if tar_status:
            wl_log.critical("Tar check failed: %s tar_status: %s tar_txt: %s"
                            % (tar_gz_check_cmd, tar_status, tar_txt))
            return False
        else:
            return True
