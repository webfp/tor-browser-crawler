import signal
from contextlib import contextmanager
from distutils.dir_util import copy_tree
from shutil import copyfile
from os import makedirs
from os.path import exists
from scapy.all import PcapReader, wrpcap

import psutil
from pyvirtualdisplay import Display

from common import TimeoutException
from tbcrawler import common as cm


def create_dir(dir_path):
    """Create a directory if it doesn't exist."""
    if not exists(dir_path):
        makedirs(dir_path)
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


def filter_tshark(tshark_path, iplist):                                          
    # Remove lines in log for IPs that are not in iplist                         
    orig_tshark = tshark_path + ".original"                                      
    move(tshark_path, orig_tshark)                                               
    tao_trace = tshark_path[:-6] + 'tao'                                         
    with open(tshark_path, 'wb') as fo, open(tao_trace, 'wb') as ft:             
        for line in open(orig_tshark):                                           
            s_line = line.strip().split(',')                                     
            ts = s_line[0]                                                       
            src, dst = s_line[1:3]                                               
            proto, ip_len, ip_hdr_len, tcp_hdr_len = s_line[5:9]                 
            msg = s_line[14]                                                     
            if proto != '6':                                                     
                continue                                                         
            datalen = int(ip_len) - (int(ip_hdr_len) + int(tcp_hdr_len))         
            if datalen == 0:                                                     
                continue                                                         
            if src not in iplist and dst not in iplist:                          
                continue                                                         
            fo.write(line)                                                       
            if src != cm.LOCAL_IP:                                               
                datalen = -datalen                                               
            if 'retransmission' in msg.lower():                                  
                continue                                                         
            ft.write('\t'.join([ts, str(datalen)]) + '\n')                       
                                                                                 
                                                                                 
def filter_pcap(pcap_path, iplist):                                              
    # TODO: parse pcap into a CSV with the following fields:                     
    # length, timestamp, src_ip. dst_ip, direction, n_cells                      
    # remove ACKs, retransmissions                                               
    # Remove sendme's and store that in a separate CSV                           
    # for the moment, keep the original .pcap                                    
    # we don't need the payload stripping                                        
    pcap_filtered = []                                                           
    orig_pcap = pcap_path + ".original"                                          
    copyfile(pcap_path, orig_pcap)                                               
    with PcapReader(orig_pcap) as preader:                                       
        for p in preader:                                                        
            if 'TCP' in p:                                                       
                ip = p.payload                                                   
                if ip.dst in iplist or ip.src in iplist:                         
                    pcap_filtered.append(p)                                      
    wrpcap(pcap_path, pcap_filtered)


def start_xvfb(win_width=cm.DEFAULT_XVFB_WIN_W,
               win_height=cm.DEFAULT_XVFB_WIN_H):
    xvfb_display = Display(visible=0, size=(win_width, win_height))
    xvfb_display.start()
    return xvfb_display


def stop_xvfb(xvfb_display):
    if xvfb_display:
        xvfb_display.stop()
