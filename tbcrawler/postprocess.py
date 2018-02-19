import json
import mmh3
import os
import re
import sys
import traceback
import logging
from os.path import isdir, isfile, join, getsize, basename, normpath, dirname, realpath
from tld.utils import get_tld
sys.path.insert(0, dirname(dirname((dirname(realpath(__file__))))))

# from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance
from multiprocessing import Pool, Lock
from itertools import izip
# from hashes.simhash import simhash
import simhash  # https://github.com/seomoz/simhash-py
from collections import defaultdict
from variance.utils import dup_detect
from variance.utils import gen_utils
from variance.utils import file_utils as fu
from variance import common as cm
from urlparse import urlparse
from variance.utils.parallelizer import multiproc
from variance.utils.common import IP_DO
from bs4 import BeautifulSoup

import pandas as pd
import numpy as np
from scipy import stats

# ad and tracking detection
from adblockparser import AdblockRules
easylist_rules = AdblockRules(open("abp_rules/easylist.txt").readlines())
easyprivacy_rules = AdblockRules(open("abp_rules/easyprivacy.txt").readlines())


REMOVE_RETRANSMISSIONS = True
USE_TSHARK_TCP_PAYLOAD = False
SKIP_MALFORMED = True
MPLOCK = Lock()


class PacketInfo(object):
    def __init__(self):
        self.ts = 0.0
        self.src_ip = ""
        self.dst_ip = ""
        self.src_port = 0
        self.dst_port = 0
        self.proto = ""
        self.ip_payload_size = 0
        self.ip_hdr_len = 0
        self.tcp_hdr_len = 0
        self.tcp_payload_size = 0
        self.tcp_flags = ""
        self.tcp_options_tsval = 0
        self.tcp_options_tsecr = 0
        self.tcp_seq = 0
        self.tcp_ack = 0
        self.tcp_win_size = 0
        self.tcp_expert_msg = ""


class HTTPMsgInfo(object):
    def __init__(self):
        self.msg_type = ""
        self.req_method = ""
        self.version = ""
        self.size = 0
        self.ts = 0
        self.url = ""
        self.headers = None

    def __repr__(self, *args, **kwargs):
        return ("%s\t%s\t%s\t%s\t%s\t%s\t%s" %
                (self.msg_type, self.req_method, self.version,
                 self.size, self.ts, self.url, self.headers))


class VisitInfo(object):
    def __init__(self):
        # TODO change to ""
        self.http_log_file = None
        self.html_src_file = None
        self.tshark_file = None
        self.screenshot_file = None
        self.pcap_file = None

        self.batch_num = 0  # batch number for this visit
        self.instance_num = 0  # instance number for this visit
        self.site_domain = 0  # abc.onion
        self.visit_dir = ""  # path to dir holding the visit files

        self.pcap_size = 0
        self.html_src_size = 0
        self.screenshot_size = 0  # image size in bytes

        self.screenshot_hash = 0  # sha1 sum of the screenshot content
        self.html_src_hash = 0
        self.html_src_simhash = 0
        self.page_title = ""

        self.visit_success = False  # true if we've a healthy html (no error)
        self.fx_conn_error = False  # true if we Firefox connection error page

        self.num_http_req = 0  # number of HTTP requests
        self.num_http_resp = 0  # number of HTTP responses
        self.total_http_download = 0  # total response size
        self.total_http_upload = 0  # total request size
        self.http_duration = 0  # time between 1st req to last response
        self.http_req_url_set = None
        self.tshark_duration = 0  # time between first and last packet
        self.total_incoming_tcp_data = 0  # total incoming TCP payloads
        self.total_outgoing_tcp_data = 0  # total outcoming TCP payloads
        self.begin_time = 0  # beginning time of the pcap capture
        self.end_time = 0  # end time of the pcap capture
        self.site_generator = None
        self.num_domains = 0
        self.num_redirs = 0
        self.num_images = 0
        self.num_htmls = 0
        self.num_stylesheets = 0
        self.num_scripts = 0
        self.num_fonts = 0
        self.num_videos = 0
        self.num_audios = 0
        self.num_empty_content = 0
        self.num_other_content = 0
        self.time_to_first_byte = None
        self.num_waterfall_phases = 0
        # CMS/site generator type, dummy coding for the regression analysis
        self.cms_used = 0
        self.made_with_wordpress = 0
        self.made_with_woocommerce = 0
        self.made_with_joomla = 0
        self.made_with_drupal = 0
        self.made_with_mediawiki = 0
        self.made_with_dokuwiki = 0
        self.made_with_vbulletin = 0
        self.made_with_django = 0
        self.made_with_phpsqlitecms = 0
        self.made_with_onionmail = 0
        self.has_ads = 0
        self.has_tracking = 0
        # don't forget to update __repr__ method when you add a new attribute

    def col_headers(self):
        return "i_site_domain\ti_batch_num\ti_instance_num\t"\
            "i_visit_success\tmo_num_http_req\t"\
            "mo_num_http_resp\tmed_total_http_download\t"\
            "med_total_http_upload\t"\
            "i_total_incoming_tcp_data\ti_total_outgoing_tcp_data\t"\
            "med_http_duration\t"\
            "i_tshark_duration\ti_screenshot_hash\t"\
            "i_html_src_hash\ti_pcap_size\tmed_html_src_size\t"\
            "med_screenshot_size\ti_page_title\t"\
            "i_html_src_simhash\ti_begin_time\tmo_num_domains\t"\
            "mo_num_redirs\tmo_num_scripts\tmo_num_stylesheets\tmo_num_htmls\t"\
            "mo_num_images\tmo_num_videos\tmo_num_audios\tmo_num_fonts\t"\
            "mo_num_other_content\tmo_num_empty_content\ti_time_to_first_byte\t"\
            "mo_num_waterfall_phases\t"\
            "mo_cms_used\tmo_made_with_wordpress\t"\
            "mo_made_with_woocommerce\tmo_made_with_joomla\t"\
            "mo_made_with_drupal\tmo_made_with_mediawiki\t"\
            "mo_made_with_dokuwiki\tmo_made_with_vbulletin\t"\
            "mo_made_with_django\tmo_made_with_phpsqlitecms\t"\
            "mo_made_with_onionmail\tmo_has_ads\tmo_has_tracking"

    def __repr__(self, *args, **kwargs):
        return ("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%d\t"
                "%d\t%d\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t"
                "%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d" %
                (self.site_domain, self.batch_num, self.instance_num,
                 self.visit_success, self.num_http_req,
                 self.num_http_resp, self.total_http_download,
                 self.total_http_upload,
                 self.total_incoming_tcp_data, self.total_outgoing_tcp_data,
                 self.http_duration,
                 self.tshark_duration, self.screenshot_hash,
                 self.html_src_hash, self.pcap_size, self.html_src_size,
                 self.screenshot_size, self.page_title,
                 self.html_src_simhash, self.begin_time, self.num_domains,
                 self.num_redirs,
                 self.num_scripts,
                 self.num_stylesheets, self.num_htmls,
                 self.num_images, self.num_videos,
                 self.num_audios, self.num_fonts,
                 self.num_other_content, self.num_empty_content,
                 self.time_to_first_byte,
                 self.num_waterfall_phases,
                 self.cms_used,
                 self.made_with_wordpress,
                 self.made_with_woocommerce,
                 self.made_with_joomla,
                 self.made_with_drupal,
                 self.made_with_mediawiki,
                 self.made_with_dokuwiki,
                 self.made_with_vbulletin,
                 self.made_with_django,
                 self.made_with_phpsqlitecms,
                 self.made_with_onionmail,
                 self.has_ads,
                 self.has_tracking
                 ))


class CrawlInfo(object):
    def __init__(self):
        self.crawl_dir = ""
        self.num_batches = 0
        self.num_instances = 0
        self.num_sites = 0
        self.num_visit_dirs = 0
        self.num_ok_visits = 0  # total visits without any error
        self.num_conn_errors = 0  # num of visits with connection errors
        self.tcp_expert_msg = ""
        # list of selected instances  and domains after error/outlier removal
        # and setting a threshold
        self.selected_instances = []
        self.selected_domains = []
        self.visit_info_arr = []


def run_in_parallel(inputs, worker,
                    no_of_processes=cm.DEFAULT_N_JOBS_IN_PARALLEL):
    p = Pool(no_of_processes)
    p.map(worker, inputs)


def int_or_default(str_val, default_val=0):
    return int(str_val) if len(str_val) else default_val


def parse_tshark_output(tshark_out):
    packet_info_arr = []
    if not isfile(tshark_out):
        return packet_info_arr

    for line in open(tshark_out):
        packet_info = PacketInfo()
        try:
            if SKIP_MALFORMED and "Malformed Packet" in line:
                # print "Skipping malformed packet"
                continue
            # print line
            if REMOVE_RETRANSMISSIONS and "[Retransmission (suspected)]" in line:
                print "Removing retransmitted packet"
                continue
            line = line.strip()
            items = line.split("\t")
            packet_info.ts = float(items[0])
            packet_info.src_ip = items[1]
            packet_info.dst_ip = items[2]
            packet_info.src_port = items[3]
            packet_info.dst_port = items[4]
            packet_info.proto = items[5]
            assert "6" == packet_info.proto  # must be TCP (6)
            packet_info.ip_payload_size = int_or_default(items[6])
            packet_info.ip_hdr_len = int_or_default(items[7])
            packet_info.tcp_hdr_len = int_or_default(items[8])
            if USE_TSHARK_TCP_PAYLOAD:
                if "," in items[9]:
                    # packets with multiple payloads appear as A,B
                    payloads = items[9].split(",")
                    packet_info.tcp_payload_size = sum(int(payload)
                                                       for payload in payloads)
                else:
                    packet_info.tcp_payload_size = int_or_default(items[9])
                if packet_info.tcp_payload_size > packet_info.ip_payload_size:
                    print "TCP >  IP payload", packet_info.tcp_payload_size, packet_info.ip_payload_size
            else:
                packet_info.tcp_payload_size = packet_info.ip_payload_size - (packet_info.ip_hdr_len + packet_info.tcp_hdr_len)

            packet_info.tcp_flags = items[10]
            assert "0x" in packet_info.tcp_flags
            packet_info.tcp_options_tsval = int_or_default(items[11])
            packet_info.tcp_options_tsecr = int_or_default(items[12])
            packet_info.tcp_seq = int_or_default(items[13])
            packet_info.tcp_ack = int_or_default(items[14])
            packet_info.tcp_win_size = int_or_default(items[15])
            if len(items) > 16:
                packet_info.tcp_expert_msg = items[16]
            packet_info_arr.append(packet_info)
        except Exception as exc:
            print "Exception:", tshark_out, exc, line
            print traceback.format_exc()
    return packet_info_arr


def process_pcap(pcap):
    """Parse the pcap and save the packet details in the same dir as
    the pcap file."""

    print "Processing", pcap
    pcap_path, _ = os.path.splitext(pcap)
    # strip_payload_from_pcap(pcap)
    os.system("tshark -nn -T fields -E separator=/t  -e frame.time_epoch"
              " -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport"
              " -e ip.proto -e ip.len -e ip.hdr_len -e tcp.hdr_len -e data.len"
              " -e tcp.flags -e tcp.options.timestamp.tsval"
              " -e tcp.options.timestamp.tsecr -e tcp.seq  -e tcp.ack"
              " -e tcp.window_size_value -e expert.message "
              " -r  %s > %s.tshark" % (pcap, pcap_path))
    # tcpdump command from Panchenko's raw-to-tcp script
    os.system("""tcpdump -r {0} -n -l -tt -q -v | sed -e 's/^[     ]*//' |
        awk '/length ([0-9][0-9]*)/{{printf "%s ",$0;next}}{{print}}' > {1}""".\
        format(pcap, pcap_path + '.tcpdump'))


def process_crawl_pcaps(crawl_dir):
    pcap_list = list(fu.gen_find_files("*.pcap", crawl_dir))
    multiproc(process_pcap, pcap_list)  # TODO to be tested
    # run_in_parallel(pcap_list, process_pcap)
    # for pcap in gen_find_files("*.pcap", crawl_dir):


def is_moz_error_txt(page_source):
    if "global/locale/neterror.dtd" in page_source and\
        "connectionfailure.title" in page_source and\
            "problem loading page" in page_source:
        return True
    return False


def get_batch_and_instance_counts(crawl_dir):
    dir_cnt = 0
    num_batches = 0
    num_instances = 0
    crawled_domains = set()
    for dir_path in gen_find_visit_dirs(crawl_dir):
        _dir = basename(dir_path)
        assert ".onion" in _dir  # assumes HS crawl, can be removed
        batch_no, domain, instance_no = _dir.split("_")  # e.g. 9_zxh6oj6jc4olwebf.onion_46
        batch_no, instance_no = int(batch_no), int(instance_no)
        crawled_domains.add(domain)
        num_batches = batch_no if batch_no > num_batches else num_batches
        num_instances = instance_no if instance_no > num_instances else num_instances
        dir_cnt += 1

    num_batches += 1
    num_instances += 1
    num_instances /= num_batches
    total_domains = dir_cnt / (num_instances * num_batches)
    print "# of batches, # of instances per batch ", num_batches, num_instances
    print "total dirs", dir_cnt
    print "total crawled domains", total_domains
    assert len(crawled_domains) == total_domains  # assumes a complete crawl
    return num_batches, num_instances, crawled_domains


def parse_tb_http_logs(tbb_http_log):
    http_info_arr = []
    if not isfile(tbb_http_log):
        return http_info_arr
    for line in open(tbb_http_log):
        # print line
        http_info = HTTPMsgInfo()
        try:
            line = line.strip()
            # skip the header line, sometimes we've headers printed twice!
            if line.startswith("msgType"):
                continue
            items = line.split("\t")
            # print items
            http_info.msg_type = items[0]
            if http_info.msg_type == "REQUEST":
                http_info.req_method = items[1]
                http_info.version = items[2]
            assert http_info.msg_type in ["REQUEST", "RESPONSE"]
            http_info.size = int_or_default(items[3])
            http_info.ts = int_or_default(items[4])
            http_info.url = items[5]
            # http_info.headers = items[6]
            http_info.headers = json.loads(items[6])
            # print headers
            assert len(items) == 7
            http_info_arr.append(http_info)
        except Exception as exc:
            print "Exception:", tbb_http_log, exc, line
            print traceback.format_exc()
    return http_info_arr


class KeyboardInterruptError(Exception):
    pass


def parse_crawl_data_for_domain_wrapper(domain_csv_crawl_info_tuple):
    try:
        parse_crawl_data_for_domain(domain_csv_crawl_info_tuple[0],
                                    domain_csv_crawl_info_tuple[1],
                                    domain_csv_crawl_info_tuple[2])
    except KeyboardInterrupt:
        raise KeyboardInterruptError()


def parse_crawl_data_for_domain(domain, hi_level_feats_csv, crawl_info):
    visit_info_arr = []
    for batch_no in xrange(crawl_info.num_batches):
        for instance_no in xrange(crawl_info.num_instances):
            instance_num = (batch_no * crawl_info.num_instances) + instance_no
            visit_name = "%d_%s_%d" % (batch_no, domain, instance_num)
            if (PROCESS_SELECTED_INSTANCES_ONLY and
                    visit_name not in crawl_info.selected_instances):
                # print "Not selected, will continue", visit_name
                continue
            visit_dir = join(crawl_info.crawl_dir, visit_name)
            # visit_info_arr.append(get_visit_info(visit_dir, crawl_info))
            # print "Will process", domain
            visit_info = get_visit_info(visit_dir, crawl_info)
            visit_info_arr.append(visit_info)
    MPLOCK.acquire()  # to prevent interlaved lines from other processes
    fu.append_to_file(hi_level_feats_csv,
                      "\n" + "\n".join(str(visit_info_)
                                    for visit_info_ in visit_info_arr))
    MPLOCK.release()


def get_selected_domains_and_instances(crawl_dir):
    """Read and return the selected instances from a csv in variance/etc."""
    crawl_name = basename(normpath(crawl_dir))
    selected_inst_csv = join(dirname(dirname((dirname(realpath(__file__))))),
                             "data", "%s_urls.txt" % crawl_name)
    selected_instances = []
    selected_domains = set()
    if not isfile(selected_inst_csv):
        print "Can't find the list of selected instances"
    for line_ in open(selected_inst_csv):
        instance_name = line_.split()[0]
        assert ".onion" in instance_name
        selected_instances.append(instance_name)
        selected_domains.add(instance_name.split("_")[1])
    return list(selected_domains), selected_instances


RUN_IN_PARALLEL = True
# if true, only process extract feats from selected instances
PROCESS_SELECTED_INSTANCES_ONLY = True


def get_crawl_stats(crawl_dir):
    crawl_info = CrawlInfo()
    crawl_info.crawl_dir = crawl_dir
    crawl_info.selected_domains, crawl_info.selected_instances =\
        get_selected_domains_and_instances(crawl_dir)
    crawl_info.num_batches, crawl_info.num_instances,\
        crawl_info.crawled_domains = get_batch_and_instance_counts(crawl_dir)
    crawl_name = basename(normpath(crawl_dir))
    hi_level_feats_csv = join(dirname(dirname((dirname(realpath(__file__))))),
                              "data", "high_level_feats", "%s_hi_level_feats.csv" % crawl_name)

    dummy = VisitInfo()
    fu.write_to_file(hi_level_feats_csv, dummy.col_headers())

    # create an array of selected domains
    domains_to_process = []
    if not PROCESS_SELECTED_INSTANCES_ONLY:
        domains_to_process = crawl_info.crawled_domains
    else:
        domains_to_process = crawl_info.selected_domains
    if RUN_IN_PARALLEL:
        num_domains = len(domains_to_process)
        multiproc(parse_crawl_data_for_domain_wrapper,
                  izip(domains_to_process,
                       [hi_level_feats_csv] * num_domains,
                       [crawl_info] * num_domains))
    else:
        for domain in domains_to_process:
            parse_crawl_data_for_domain(crawl_info, domain, hi_level_feats_csv)


PRINT_VISITS_WITH_ERRORS = False


def get_visit_info(visit_dir, crawl_info):
    if not isdir(visit_dir):
        return None
    visit_info = VisitInfo()
    visit_info.visit_dir = visit_dir
    # extract batch & instance numbers, domain name
    path_items = basename(normpath(visit_dir)).split("_")
    visit_info.instance_num = int(path_items[-1])
    visit_info.site_domain = path_items[-2]
    visit_info.batch_num = int(path_items[-3])
    # construct visit filenames
    http_log_file = join(visit_dir, cm.HTTP_LOG_FILENAME)
    html_src_file = join(visit_dir, cm.HTML_SRC_FILENAME)
    tshark_file = join(visit_dir, cm.HTML_TSHARK_FILENAME)
    screenshot_file = join(visit_dir, cm.SCREENSHOT_FILENAME)
    pcap_file = join(visit_dir, cm.PCAP_FILENAME)

    process_source_html(html_src_file, visit_info)
    # parse tshark network packet logs
    if isfile(tshark_file):
        get_visit_info_from_tshark(tshark_file, visit_info)

    # parse HTTP logs
    if isfile(http_log_file):
        get_visit_info_from_tb_http_logs(http_log_file, visit_info)

    if isfile(pcap_file):
        visit_info.pcap_file = pcap_file
        visit_info.pcap_size = getsize(pcap_file)
    else:  # if no pcap, there shouldn't be any tshark file
        assert visit_info.tshark_file is None
        # print "NO PCAP", pcap_file

    if isfile(screenshot_file):
        visit_info.screenshot_file = screenshot_file
        visit_info.screenshot_size = getsize(screenshot_file)
        visit_info.screenshot_hash = mmh3.hash(open(screenshot_file).read())

    # check if there was an error?
    visit_info.visit_success = (not visit_info.fx_conn_error) and\
        isfile(http_log_file) and isfile(html_src_file) and\
        isfile(tshark_file) and isfile(screenshot_file)
    if PRINT_VISITS_WITH_ERRORS and not visit_info.visit_success:
        print "Errored visit", visit_dir
    if 0 and (visit_info.tshark_duration) < visit_info.http_duration:
        print "Duration (tshark - HTTP)", visit_info.tshark_duration, visit_info.http_duration
        print tshark_file
    return visit_info


def get_visit_info_from_tshark(tshark_file, visit_info):
    visit_info.tshark_file = tshark_file
    pkt_info_arr = parse_tshark_output(tshark_file)
    total_uplink_data = 0
    total_downlink_data = 0
    if not len(pkt_info_arr):
        return
    for pkt_info in pkt_info_arr:
        if pkt_info.src_ip == IP_DO:
            total_uplink_data += pkt_info.tcp_payload_size
        else:
            total_downlink_data += pkt_info.tcp_payload_size
    visit_info.begin_time = pkt_info_arr[0].ts
    visit_info.end_time = pkt_info_arr[-1].ts  # last packet's timestamp
    visit_info.tshark_duration = int(1000 * (visit_info.end_time -
                                             visit_info.begin_time))
    visit_info.total_outgoing_tcp_data = total_uplink_data
    visit_info.total_incoming_tcp_data = total_downlink_data


def get_onion_tld(url):
    hostname = urlparse(url).hostname
    if hostname.endswith(".onion"):
        # For .onion urls, we don't count the subdomains separately
        # since there won't be any additional lookup for them
        return "%s.onion" % hostname.split(".")[-2]
    else:
        return get_tld(url)


def get_resource_stats(http_responses, visit_info):
    for http_response in http_responses:
        mime_type = "other"

        # count the number of redirections
        if "Location" in http_response.headers:
            # print "Redirection", http_response.url, "->", http_response.headers["Location"]
            visit_info.num_redirs += 1

        # get the resource type
        # skip if no content
        if http_response.size == 0 or\
            ("Content-Length" in http_response.headers and
                http_response.headers["Content-Length"] == "0"):
            visit_info.num_empty_content += 1
            # print "Zero content"
            continue
        if "Content-Type" in http_response.headers:
            content_type = http_response.headers["Content-Type"].split(";")[0]  # e.g. img/jpeg
            mime_type = content_type.split("/")[0]  # e.g. img
            if "javascript" in content_type:
                visit_info.num_scripts += 1
            elif content_type == "text/css":
                visit_info.num_stylesheets += 1
            elif content_type == "text/html":
                visit_info.num_htmls += 1
            elif mime_type == "image":
                visit_info.num_images += 1
            elif mime_type == "video":
                visit_info.num_videos += 1
            elif mime_type == "audio":
                visit_info.num_audios += 1
            elif "font" in content_type:
                visit_info.num_fonts += 1
            else:  # application, binary, file etc.
                visit_info.num_other_content += 1
                # print http_response.headers["Content-Type"], visit_info.http_log_file
        else:
            # print "No content type", http_response.headers, http_response, visit_info.http_log_file
            visit_info.num_other_content += 1


def get_visit_info_from_tb_http_logs(http_log_file, visit_info):
    visit_info.http_log_file = http_log_file
    http_info_arr = parse_tb_http_logs(http_log_file)
    pcap_end_time = visit_info.end_time * 1000  # convert from sec to msec
    pcap_begin_time = visit_info.begin_time * 1000  # convert from sec to msec

    # filter out HTTP msgs received before and after the pcap capture
    # all the website related traffic should be captured
    http_info_arr = filter(lambda x:
                           (x.ts < pcap_end_time and
                            x.ts > pcap_begin_time),
                           http_info_arr)
    if not len(http_info_arr):
        return
    http_reqs = [http_info for http_info in http_info_arr
                 if http_info.msg_type == "REQUEST"]
    http_resps = [http_info for http_info in http_info_arr
                  if http_info.msg_type == "RESPONSE"]
    visit_info.http_duration = http_info_arr[-1].ts - http_reqs[0].ts
    get_resource_stats(http_resps, visit_info)
    visit_info.num_http_req = len(http_reqs)
    visit_info.num_http_resp = len(http_resps)
    assert len(http_info_arr) == (visit_info.num_http_req + visit_info.num_http_resp)
    # total http upload can't be bigger than the total ourgoing tcp data
    visit_info.total_http_upload = min(sum(http_req.size for http_req in http_reqs),
                                       visit_info.total_outgoing_tcp_data)
    # if visit_info.total_http_upload == visit_info.total_outgoing_tcp_data:
    #     print "WARNING http upload size capped", visit_info.total_outgoing_tcp_data, http_log_file
    visit_info.total_http_download = min(sum(http_resp.size for http_resp in http_resps),
                                         visit_info.total_incoming_tcp_data)
    #if visit_info.total_http_download == visit_info.total_incoming_tcp_data:
    #    print "WARNING http download size capped", visit_info.total_incoming_tcp_data, http_log_file
    visit_info.http_req_url_set = set(http_req.url for http_req in http_reqs)
    unique_tlds = set(get_onion_tld(url) for url in visit_info.http_req_url_set)
    visit_info.num_domains = len(unique_tlds)
    visit_info.time_to_first_byte = get_time_to_first_byte(http_resps, http_reqs[0].ts)
    visit_info.num_waterfall_phases = get_waterfall_phases(http_info_arr, visit_info)
    check_ads_and_tracking(http_reqs, visit_info)


def check_ads_and_tracking(http_reqs, visit_info):
    hs_http_url = "http://" + visit_info.site_domain
    hs_https_url = "https://" + visit_info.site_domain
    already_checked = set()
    for req in http_reqs:
        if req.url in already_checked:
            continue
        req_url = req.url
        already_checked.add(req_url)
        if req_url.startswith(hs_http_url) or req_url.startswith(hs_https_url):
            continue
        if easylist_rules.should_block(req_url):
            visit_info.has_ads = 1
            # print "easylist (ads): should_block", req_url, visit_info.http_log_file
        if easyprivacy_rules.should_block(req_url):
            visit_info.has_tracking = 1
            # print "easyprivacy (tracking): should_block", req_url, visit_info.http_log_file
        if visit_info.has_tracking and visit_info.has_ads:
            return


def get_waterfall_phases(http_msgs, visit_info):
    last_msg_type = None
    num_waterfall_phases = 0
    for http_msg in http_msgs:
        if last_msg_type == "REQUEST" and http_msg.msg_type == "RESPONSE":
            num_waterfall_phases += 1
        last_msg_type = http_msg.msg_type
    # print "num_switch", num_waterfall_phases, visit_info.http_log_file
    return num_waterfall_phases


def get_time_to_first_byte(http_resps, first_req_ts):
    for http_resp in http_resps:
        # exclude ocsp or tor button update requests
        if "ocsp." in http_resp.url or\
                "check.torproject.org/?TorButton" in http_resp.url:
            continue
        ttfb = http_resp.ts - first_req_ts
        # print http_resp.url, ttfb
        return ttfb
    else:
        # if no request/response pair is available
        return None


def gen_find_visit_dirs(crawl_dir):
    for _dir in os.listdir(crawl_dir):
        dir_path = join(crawl_dir, _dir)
        if isdir(dir_path):
            if re.match(r"[0-9]_.*_[0-9]*", _dir):  # assumes # batches <= 10
                yield dir_path


def replace_whitespace(txt):
    return txt.strip().replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')


def parse_html_with_bs4(html_src):
    """In case we want to parse page further."""
    try:
        BeautifulSoup(html_src, 'html.parser')
    except Exception as exc:
        print exc, traceback.format_exc()
    pass

# t_before_edit_dist = time()
# avg_edit_distance = get_avg_html_src_edit_dist(visit_dir,
# html_src_file, visit_info.site_domain, crawl_info)
# print time() - t_before_edit_dist, "sec"


def process_source_html(html_src_file, visit_info):
    if isfile(html_src_file):
        visit_info.html_src_file = html_src_file
        html_src = open(html_src_file).read()
        visit_info.html_src_size = len(html_src)
        visit_info.fx_conn_error = is_moz_error_txt(html_src)
        visit_info.html_src_hash = mmh3.hash(html_src)
        visit_info.html_src_simhash = simhash.hash(html_src)
        if not visit_info.fx_conn_error:
            visit_info.page_title = get_page_title_from_html_src(html_src)
            populate_site_generator(html_src, visit_info)
            # parse_html_with_bs4(html_src)


def populate_site_generator(html_src, visit_info):
    """Extract the generator meta tag content to detect the CMS"""
    match = re.search(r"<meta[^>]*name=.generator[^>]*", html_src)
    if match is None:
        return None
    meta_tag = match.group(0)
    match = re.search(r'content=.([^\"]*)\"', meta_tag)
    site_generator = replace_whitespace(match.group(1))
    if "wordpress" in site_generator:
        visit_info.made_with_wordpress = 1
        visit_info.cms_used = 1
    elif "woocommerce" in site_generator:
        # woocommerce is an e-commerce plugin for wordpress
        # we treat woocommerce sites as both wordpress and woocommerce
        visit_info.made_with_woocommerce = 1
        visit_info.made_with_wordpress = 1
        visit_info.cms_used = 1
    elif "joomla" in site_generator:
        visit_info.made_with_joomla = 1
        visit_info.cms_used = 1
    elif "drupal" in site_generator:
        visit_info.made_with_drupal = 1
        visit_info.cms_used = 1
    elif "mediawiki" in site_generator:
        visit_info.made_with_mediawiki = 1
        visit_info.cms_used = 1
    elif "dokuwiki" in site_generator:
        visit_info.made_with_dokuwiki = 1
        visit_info.cms_used = 1
    elif "vbulletin" in site_generator:
        visit_info.made_with_vbulletin = 1
        visit_info.cms_used = 1
    elif "django" in site_generator:
        visit_info.made_with_django = 1
        visit_info.cms_used = 1
    elif "phpsqlitecms" in site_generator:
        visit_info.made_with_phpsqlitecms = 1
        visit_info.cms_used = 1
    elif "onionmail" in site_generator:
        visit_info.made_with_onionmail = 1
        visit_info.cms_used = 1
    else:
        pass
        # we ignore unknown/other generators
        # remove the version numbers
        # site_generator = re.sub(r"[\d\.]+", "", site_generator).strip()
        # print site_generator
    # return site_generator
    # grep -oH  */source.html |
    # sed 's/ name="generator" //' | sed 's/_/"/g'  |
    # cut  -d"\"" -f 2,4 | sed 's/"/ => /'  | sort -u


def get_page_title_from_html_src(html_src):
    match = re.search(r'<title[^>]*>([^<]+)</title>', html_src)
    if match is None:
        # print "Can't find title", visit_dir
        return ""
    else:
        # return match.group(1).strip().replace('\n', ' ').replace('\r', '')
        return replace_whitespace(match.group(1).replace("&amp;", "&"))


def get_page_title(crawl_dir, site_domain, batch_num, instance_num):
    visit_dir = join(crawl_dir, "%s_%s_%s" % (batch_num, site_domain,
                                              instance_num))
    html_src = open(join(visit_dir, cm.HTML_SRC_FILENAME)).read()
    return get_page_title_from_html_src(html_src)


def get_http_req_paths(http_log_file):
    req_paths = set()
    http_info_arr = parse_tb_http_logs(http_log_file)
    for http_info in http_info_arr:
        items = urlparse(http_info.url)
        if items.path and items.path not in ["/", "/favicon.ico"]:
            req_paths.add(items.path)
    return req_paths


def process_crawl_csv(crawl_dir, csv_name):
    domain_fail_count = defaultdict(int)
    domain_screenshot_hashes = defaultdict(set)
    domain_html_src_hashes = defaultdict(set)
    domain_html_src_simhashes = defaultdict(set)
    domain_titles = defaultdict(set)
    domain_req_paths = defaultdict(set)
    for line in open(csv_name):
        items = line.strip().split("\t")
        if len(items) <= 1:
            continue
        # print items
        site_domain, batch_num, instance_num, visit_success, num_http_req,\
        num_http_resp, total_http_download, total_http_upload, http_duration,\
        tshark_duration, screenshot_hash, html_src_hash, pcap_size, html_src_size,\
        screenshot_size, page_title, html_src_simhash = items
        if visit_success == "0" or \
            html_src_size == "0" or \
            pcap_size == "0" or \
            screenshot_size == "0" or \
            html_src_hash == "1879059922" or \
            screenshot_hash in ["0", "1373743527"]:
            domain_fail_count[site_domain] += 1
        else:
            visit_dir = join(crawl_dir, "%s_%s_%s" % (batch_num, site_domain, instance_num))
            http_log_file = join(visit_dir, cm.HTTP_LOG_FILENAME)
            domain_req_paths[site_domain].update(get_http_req_paths(http_log_file))
            domain_screenshot_hashes[site_domain].add(screenshot_hash)
            domain_html_src_hashes[site_domain].add(html_src_hash)
            domain_html_src_simhashes[site_domain].add(html_src_simhash)
            if len(page_title) and not page_title in ["index of /"]:
                domain_titles[site_domain].add(page_title)
    return (domain_fail_count, domain_screenshot_hashes, domain_html_src_hashes,
            domain_html_src_simhashes, domain_titles, domain_req_paths)


DISCARD_FIRST_INSTANCE = False


def check_csv_data(crawl_dir, csv_name):
    csv_path = join(crawl_dir, csv_name)
    domain_fail_count = defaultdict(int)
    screenshot_dict = defaultdict(set)
    html_src_dict = defaultdict(set)
    hash_freq_dict = defaultdict(int)
    domain_screenshot_dict = defaultdict(dict)
    domain_screenshot_hashes = defaultdict(set)
    domain_title_set = defaultdict(set)
    screenshot_hash_html_src_hash = defaultdict(set)
    # empty_html_count = defaultdict(int)
    for line in open(csv_path):
        items = line.strip().split("\t")
        if len(items) > 1:
            # print items
            site_domain, batch_num, instance_num, visit_success, num_http_req,\
            num_http_resp, total_http_download, total_http_upload, http_duration,\
            tshark_duration, screenshot_hash, html_src_hash, pcap_size, html_src_size,\
            screenshot_size, page_title, html_src_simhash = items
            # convert to int
            if DISCARD_FIRST_INSTANCE and not int(instance_num) % 5:
                continue
            assert ".onion" in site_domain
            hash_freq_dict[screenshot_hash] += 1
            if visit_success == "0" or \
                html_src_size == "0" or \
                pcap_size == "0" or \
                screenshot_size == "0" or \
                screenshot_hash in ["0",
                                    "5e13a221e8222d50b5233cfbe805c325c5fa96e6"]:
                domain_fail_count[site_domain] += 1
            else:
                # if visit_success == "1" and screenshot_hash == "0":
                #   print "Success, no hash", site_domain, batch_num, instance_num
                screenshot_hash_html_src_hash[screenshot_hash].add(html_src_hash)
                domain_screenshot_hashes[site_domain].add(screenshot_hash)
                # page_title = get_page_title(crawl_dir, site_domain, batch_num, instance_num)
                domain_title_set[site_domain].add(page_title)
                domain_screenshot_dict[site_domain][screenshot_hash] = domain_screenshot_dict[site_domain].get(screenshot_hash, 0) + 1
                screenshot_dict[screenshot_hash].add(site_domain)
                html_src_dict[html_src_hash].add(site_domain)
    for k, v in screenshot_dict.iteritems():
        if len(v) > 1:
            print k, v

    print "HTML match"
    for k, v in html_src_dict.iteritems():
        if len(v) > 1:
            print k, v
    sort_print_dict(hash_freq_dict)
    print "Domain fails"
    sort_print_dict(domain_fail_count)
    print "Screenshot Hash with multiple html"
    for k, v in screenshot_hash_html_src_hash.iteritems():
        if len(v) > 1:
            print k, v
    for k, v in domain_title_set.iteritems():
        for k1, v1 in domain_title_set.iteritems():
            intersect = v1.intersection(v)
            if intersect and intersect != set(['']) and k != k1:
                print k, v, k1, v1

#     for domain, hash_set in domain_screenshot_hashes.iteritems():
#         for domain2, hash_set2 in domain_screenshot_hashes.iteritems():
#             common_hashes = hash_set.intersection(hash_set2)
#             if domain != domain2 and len(common_hashes):
#                 print domain, domain2, hash_set.intersection(hash_set2)
#                 for common_hash in common_hashes:
#                     print domain_screenshot_dict[domain][common_hash] , domain_screenshot_dict[domain2][common_hash]

    # for k, v in empty_html_count.iteritems():
    #    print k, v


def sort_print_dict(_dict, print_thresh=0):
    sorted_tupls = [(v, k) for k, v in _dict.iteritems()]
    sorted_tupls.sort(reverse=True)
    for v, k in sorted_tupls:
        if v >= print_thresh:
            print "%s: %d" % (k, v)


def combine_high_level_instance_features(crawl_dir):
    crawl_name = basename(normpath(crawl_dir))
    hi_level_feats_csv = join(dirname(dirname((dirname(realpath(__file__))))),
                              "data", "high_level_feats", "%s_hi_level_feats.csv" % crawl_name)
    fability_scores_csv = join(dirname(dirname((dirname(realpath(__file__))))),
                              "data", "results", crawl_name, "fp_regression_labels.csv")
    # headers: url    avg_f1    max_f1    avg_tpr    max_tpr
    fability_df = pd.read_csv(fability_scores_csv,  sep=',')
    df = pd.read_csv(hi_level_feats_csv,  sep='\t')
    # list of unique .onion domains
    domains = fability_df.url.unique()
    aggreage_feats = defaultdict(list)
    for domain in domains:
        instance_feats = df[df.i_site_domain == domain]
        # print domain, "fability", fability_df[fability_df.url == domain]
        for feat_name in instance_feats.columns:
            if feat_name.startswith("i_"):
                continue
            # print feat_name, "Variance", domain, instance_feats[feat_name].var()
            feat_var_name = feat_name.replace("mo_", "var_").replace("med_", "var_")
            # add the variance
            aggreage_feats[feat_var_name].append(instance_feats[feat_name].var())
            if feat_name.startswith("mo_"):  # mode of the feature
                feat_mode = stats.mode(instance_feats[feat_name])[0][0]
                aggreage_feats[feat_name].append(feat_mode)
            elif feat_name.startswith("med_"):  # median of the feature
                aggreage_feats[feat_name].append(instance_feats[feat_name].median())
            else:
                print "ERROR: Unrecognized high level feature name", feat_name
                sys.exit(1)
    # add aggregate features to fability dataframe
    for feat in sorted(aggreage_feats.keys()):
        assert len(aggreage_feats[feat]) == 482
        fability_df[feat] = aggreage_feats[feat]
    # write the csv
    fability_df.to_csv(hi_level_feats_csv.replace(".csv", "_aggregated.csv"),
                       sep="\t", index=False, index_label=False)



TEST_ADBLOCK_RULES = False

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    args = sys.argv[1:]
    if TEST_ADBLOCK_RULES:
        false_pos_url = "http://thebitcoinnews.com/wp-content/uploads/2016/09/728x90-black-4-80x80.gif"
        print false_pos_url
        print "is ad ?:", easylist_rules.should_block(false_pos_url)
        print "is tracking/analytics ?:", easyprivacy_rules.should_block(false_pos_url)
        sys.exit(0)
    if not args:
        print 'usage: -i input_dir -t task'
        sys.exit(1)

    if args and args[0] == '-i':
        in_dir = args[1]
        del args[0:2]

    if args and args[0] == '-t':
        task = args[1]
        del args[0:2]
    print "Will process", in_dir
    if task == "process_pcap":
        process_crawl_pcaps(in_dir)
    elif task == "combine_hi_feats":
        combine_high_level_instance_features(in_dir)
    elif task == "crawl_stats":
        get_crawl_stats(in_dir)
        combine_high_level_instance_features(in_dir)
    elif task == "check_csv":
        check_csv_data(in_dir)
    elif task == "pack_crawl_data":
        gen_utils.pack_crawl_data(in_dir)
    elif task == "find_duplicates":
        domain_infos = process_crawl_csv(in_dir, "crawl1.csv")
        _, _, crawled_domains_set = get_batch_and_instance_counts(in_dir)
        dup_detect.find_duplicates(in_dir, crawled_domains_set, domain_infos)
    else:
        print "Can't understand the task", task
        sys.exit(1)
