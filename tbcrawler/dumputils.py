import os
import subprocess
import time
import psutil

import common as cm
import utils as ut
from log import wl_log

SNIFFER_START_TIMEOUT = 10.0


class TShark(object):
    """Capture network traffic using tshark."""

    def __init__(self, device='eth0', path="/dev/null", filter="",
                 remove_pcap=True):
        self.pcap_file = path
        self.pcap_filter = filter
        self.device = device
        self.p0 = None
        self.is_recording = False
        self.remove_pcap = remove_pcap

    def set_pcap_path(self, pcap_filename):
        """Set filename and filter options for capture."""
        self.pcap_file = pcap_filename

    def set_capture_filter(self, _filter):
        self.pcap_filter = _filter

    def get_pcap_path(self):
        """Return capture (pcap) filename."""
        return self.pcap_file

    def get_capture_filter(self):
        """Return capture filter."""
        return self.pcap_filter

    def start_capture(self, device='', pcap_path=None, pcap_filter=""):
        """Start capture. Configure sniffer if arguments are given."""
        if pcap_filter:
            self.set_capture_filter(pcap_filter)
        if pcap_path:
            self.set_pcap_path(pcap_path)
        if device:
            self.device = device
        prefix = ""
        command = ("{}tshark -nn -T fields -E separator=, -e frame.time_epoch"
              " -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport"
              " -e ip.proto -e ip.len -e ip.hdr_len -e tcp.hdr_len -e data.len"
              " -e tcp.flags -e tcp.seq -e tcp.ack"
              " -e tcp.window_size_value -e _ws.expert.message "
              " -a duration:{} -a filesize:{} -s 0 -i {} -f \'{}\'"
              " -w {} > {}".format(prefix, cm.SOFT_VISIT_TIMEOUT,
                                   cm.MAX_DUMP_SIZE, self.device,
                                   self.pcap_filter, self.pcap_file,
                                   '%s.tshark' % self.pcap_file[:-5]))
        wl_log.info(command)
        self.p0 = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        timeout = SNIFFER_START_TIMEOUT  # in seconds
        while timeout > 0 and not self.is_running():
            time.sleep(0.1)
            timeout -= 0.1
        if timeout < 0:
            raise SnifferTimeoutError()
        else:
            wl_log.debug("tshark started in %s seconds" %
                         (SNIFFER_START_TIMEOUT - timeout))

        self.is_recording = True

    def is_running(self):
        if "thsark" in psutil.Process(self.p0.pid).cmdline():
            return self.p0.returncode is None
        for proc in ut.gen_all_children_procs(self.p0.pid):
            if "tshark" in proc.cmdline():
                return True
        return False

    def stop_capture(self):
        """Kill the tshark process."""
        ut.kill_all_children(self.p0.pid)  # self.p0.pid is the shell pid
        self.p0.kill()
        self.is_recording = False
        captcha_filepath = ut.capture_filepath_to_captcha(self.pcap_file)
        if os.path.isfile(self.pcap_file):
            wl_log.info('Sniffer killed. Capture size: %s Bytes %s' %
                        (os.path.getsize(self.pcap_file), self.pcap_file))
            if self.remove_pcap:
                wl_log.info('Deleting pcap file to save space')
            os.remove(self.pcap_file)
        elif os.path.isfile(captcha_filepath):
            wl_log.info('Sniffer killed, file renamed to captcha_*. Capture size: %s Bytes %s' %
                        (os.path.getsize(captcha_filepath), captcha_filepath))
        else:
            wl_log.warning('Sniffer killed but cannot find capture file: %s or %s'
                           % (self.pcap_file, captcha_filepath))

    def __enter__(self):
        self.start_capture()
        return self

    def __exit__(self, type, value, traceback):
        self.stop_capture()


class Dumpcap(object):
    """Capture network traffic using dumpcap."""

    def __init__(self, device='eth0', path="/dev/null", filter=""):
        self.pcap_file = path
        self.pcap_filter = filter
        self.device = device
        self.p0 = None
        self.is_recording = False

    def set_pcap_path(self, pcap_filename):
        """Set filename and filter options for capture."""
        self.pcap_file = pcap_filename

    def set_capture_filter(self, _filter):
        self.pcap_filter = _filter

    def get_pcap_path(self):
        """Return capture (pcap) filename."""
        return self.pcap_file

    def get_capture_filter(self):
        """Return capture filter."""
        return self.pcap_filter

    def start_capture(self, device='', pcap_path=None, pcap_filter=""):
        """Start capture. Configure sniffer if arguments are given."""
        if pcap_filter:
            self.set_capture_filter(pcap_filter)
        if pcap_path:
            self.set_pcap_path(pcap_path)
        if device:
            self.device = device
        prefix = ""
        command = '{}dumpcap -P -a duration:{} -a filesize:{} -i {} -s 0 -f \'{}\' -w {}'\
            .format(prefix, cm.SOFT_VISIT_TIMEOUT, cm.MAX_DUMP_SIZE,
                    self.device, self.pcap_filter, self.pcap_file)
        wl_log.info(command)
        self.p0 = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        timeout = SNIFFER_START_TIMEOUT  # in seconds
        while timeout > 0 and not self.is_running():
            time.sleep(0.1)
            timeout -= 0.1
        if timeout < 0:
            raise SnifferTimeoutError()
        else:
            wl_log.debug("dumpcap started in %s seconds" %
                         (SNIFFER_START_TIMEOUT - timeout))

        self.is_recording = True

    def is_running(self):
        if "dumpcap" in psutil.Process(self.p0.pid).cmdline():
            return self.p0.returncode is None
        for proc in ut.gen_all_children_procs(self.p0.pid):
            if "dumpcap" in proc.cmdline():
                return True
        return False

    def stop_capture(self):
        """Kill the dumpcap process."""
        ut.kill_all_children(self.p0.pid)  # self.p0.pid is the shell pid
        self.p0.kill()
        self.is_recording = False
        captcha_filepath = ut.capture_filepath_to_captcha(self.pcap_file)
        if os.path.isfile(self.pcap_file):
            wl_log.info('Sniffer killed. Capture size: %s Bytes %s' %
                        (os.path.getsize(self.pcap_file), self.pcap_file))
        elif os.path.isfile(captcha_filepath):
            wl_log.info('Sniffer killed, file renamed to captcha_*. Capture size: %s Bytes %s' %
                        (os.path.getsize(captcha_filepath), captcha_filepath))
        else:
            wl_log.warning('Sniffer killed but cannot find capture file: %s or %s'
                           % (self.pcap_file, captcha_filepath))

    def __enter__(self):
        self.start_capture()
        return self

    def __exit__(self, type, value, traceback):
        self.stop_capture()


class SnifferTimeoutError(Exception):
    pass
