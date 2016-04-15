import signal
from contextlib import contextmanager
from distutils.dir_util import copy_tree

import psutil
from scapy.all import *

from common import TimeoutException


def create_dir(dir_path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def clone_dir_temporary(dir_path):
    """Makes a temporary copy of a directory."""
    import tempfile
    tempdir = tempfile.mkdtemp()
    copy_tree(dir_path, tempdir)
    return tempdir


def gen_all_children_procs(parent_pid):
    """Iterator over the children of a process."""
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        yield child


def kill_all_children(parent_pid):
    """Kill all child process of a given parent."""
    for child in gen_all_children_procs(parent_pid):
        child.kill()


def get_dict_subconfig(config, section, prefix):
    """Return options in config for options with a `prefix` keyword."""
    return {option.split()[1]: config.get(section, option)
            for option in config.options(section) if option.startswith(prefix)}


@contextmanager
def timeout(seconds):
    """From: http://stackoverflow.com/a/601168/1336939"""

    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
