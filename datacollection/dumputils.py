import subprocess
from log import wl_log
import os
import time
import common as cm

DUMPCAP_KILL_TIMEOUT = 10


class Sniffer(object):
    """Capture network traffic using dumpcap."""

    def __init__(self):
        self.pcap_file = '/dev/null'  # uggh, make sure we set a path
        self.pcap_filter = ''
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

    def start_capture(self, pcap_path=None, pcap_filter=""):
        """Start capture. Configure sniffer if arguments are given."""
        if pcap_filter:
            self.set_capture_filter(pcap_filter)

        if pcap_path:
            self.set_pcap_path(pcap_path)

        command = 'dumpcap -a duration:{} -a filesize:{} -i any -s 0 -f \'{}\' -w {}'\
            .format(cm.SOFT_VISIT_TIMEOUT, cm.MAX_DUMP_SIZE, self.pcap_filter,
                    self.pcap_file)
        wl_log.info(command)
        self.p0 = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        self.is_recording = True

    def stop_capture(self):
        """Kill dumpcap process."""
        self.p0.kill()
        timeout = DUMPCAP_KILL_TIMEOUT
        while timeout > 0 and self.p0.poll() is None:
            time.sleep(1)
            timeout -= 1
        wl_log.info("Waited %s seconds for killing dumpcap (%s)" %
                    (DUMPCAP_KILL_TIMEOUT - timeout, self.p0.poll()))
        self.is_recording = False
        if os.path.isfile(self.pcap_file):
            wl_log.info('Dumpcap killed. Capture size: %s Bytes %s' %
                        (os.path.getsize(self.pcap_file), self.pcap_file))
        else:
            wl_log.warning('Dumpcap killed but cannot find capture file: %s'
                           % self.pcap_file)
