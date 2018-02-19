import signal
import os
import subprocess
import sys
import time
import psutil

import common as cm
import utils as ut
from log import wl_log

ALL_EVENTS = ['BW', 'CIRC', 'CIRC_BW', 'CIRC_MINOR', 'CONN_BW', 'ORCONN', 'STATUS_CLIENT','STATUS_GENERAL', 'STATUS_SERVER', 'STREAM','STREAM_BW',
#'SIGNAL','ADDRMAP', 'AUTHDIR_NEWDESCS', 'BUILDTIMEOUT_SET', 'CONF_CHANGED', 'CELL_STATS', 'CLIENTS_SEEN', 'DEBUG', 'DESCCHANGED', 'ERR', 'GUARD', 'HS_DESC', 'HS_DESC_CONTENT', 'INFO', 'NEWCONSENSUS', 'NEWDESC', 'NOTICE', 'NS', 'TB_EMPTY', 'TRANSPORT_LAUNCHED', 'WARN'
]
ONIONPERF_CMD = ['python', os.path.join(cm.ONIONPERF_DIR, 'onionperf'), 'monitor', '-p', '9151', '-c', 'SIGNAL_CELL', 'SIGNAL_CIRCUIT', '-e'] + ALL_EVENTS + ['-l']



class Onionperf(object):
    def __init__(self, logpath):
        self.logpath = logpath

    def start_capture(self, device='', pcap_path=None, pcap_filter=""):
        command = ' '.join(ONIONPERF_CMD + [self.logpath])
        wl_log.info("Execute onionperf: %s" % command)
        self.p0 = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    def stop_capture(self):
        ut.kill_all_children(self.p0.pid)  # self.p0.pid is the shell pid
        os.kill(self.p0.pid, signal.SIGINT)
        #self.p0.kill()
        if os.path.isfile(self.logpath):
            wl_log.info('Onionperf killed. Capture size: %s Bytes %s' %
                        (os.path.getsize(self.logpath), self.logpath))
        else:
            wl_log.warning('Onionperf killed but cannot find capture file: %s'
                           % self.logpath)

    def __enter__(self):
        self.start_capture()
        return self

    def __exit__(self, type, value, traceback):
        self.stop_capture()

