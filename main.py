import argparse
import traceback
import logging
import common as cm
import sys
from log import wl_log
import utils as ut
from datacollection.crawler import Crawler, NUM_BATCHES, NUM_INSTANCES


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser(description='Crawl a dataset \
            in several batches.')

    # Add argument for the dataset path
    parser.add_argument('-d', '--dataset', help='dataset file path')
    parser.add_argument('-b', '--browser_version', help="Tor browser's version"
                        "used to crawl, possible values are: 'wang_et_al' or"
                        "'last_stable'")
    parser.add_argument('-v', '--verbose', help='increase output verbosity',
                        action='store_true')
    parser.add_argument("-e", "--experiment", help="Experiment type. Possible"
                        " values are: 'wang_et_al', 'multitab_alexa',"
                        "'multitab_fixbg', 'pittsburgh'")
    parser.add_argument('--batch', help='Number of batches')
    parser.add_argument('--instance', help='Number of instances')
    parser.add_argument('--start', help='Crawl URLs after this line (1)')
    parser.add_argument('--stop', help='Crawl URLs until this line')
    parser.add_argument('--action', help='Type of action: crawl, pack_data')
    parser.add_argument('-i', '--input', help='Input data (crawl dir, etc. )')

    # Parse arguments

    args = parser.parse_args()
    action = args.action
    if action == "pack_data":
        path = args.input
        ut.pack_crawl_data(path)
        sys.exit(0)

    dataset_path = args.dataset
    verbose = args.verbose
    tbb_version = args.browser_version
    # ideally experiment should specify browser type and dataset
    experiment = args.experiment
    no_of_batches = int(args.batch) if args.batch else NUM_BATCHES
    no_of_instances = int(args.instance) if args.instance else NUM_INSTANCES
    start_line = int(args.start) if args.start else 1
    stop_line = int(args.stop) if args.stop else 999999999999

    # Validate arguments
    if verbose:
        wl_log.setLevel(logging.DEBUG)
    else:
        wl_log.setLevel(logging.INFO)

    # Read urls
    url_list = []
    import os
    if not dataset_path or not os.path.isfile(dataset_path):
        wl_log.critical("ERROR: No URL list given!")
        sys.exit(1)
    else:
        try:
            with open(dataset_path) as f:
                url_list = f.read().splitlines()[start_line - 1:stop_line]
        except Exception as e:
            wl_log.error("Error opening file: {} \n{}"
                         .format(e, traceback.format_exc()))
            sys.exit(1)

    torrc_dict = cm.TORRC_DEFAULT
    if not experiment:
        wl_log.error("No experiment type specified, will use WANG_ET_AL")
        # TODO: revise default experiment
        torrc_dict = cm.TORRC_WANG_AND_GOLDBERG
        experiment = cm.EXP_TYPE_WANG_ET_AL
    elif experiment == "wang_et_al":
        torrc_dict = cm.TORRC_WANG_AND_GOLDBERG
        experiment = cm.EXP_TYPE_WANG_ET_AL
    elif experiment == "multitab_alexa":
        experiment = cm.EXP_TYPE_MULTITAB_ALEXA
    elif experiment == "multitab_fixbg":
        experiment = cm.EXP_TYPE_MULTITAB_FIXED_BG_SITE
    else:
        wl_log.error("Experiment type is not recognized."
                     " Use --help to see the possible values.")
        sys.exit(1)

    if not tbb_version:
        # Assign the last stable version of TBB
        tbb_version = cm.TBB_DEFAULT_VERSION
    elif tbb_version not in cm.TBB_KNOWN_VERSIONS:
        wl_log.error("Version of Tor browser not recognized."
                     " Use --help to see which are the accepted values.")
        sys.exit(1)

    if not no_of_batches:
        no_of_batches = NUM_BATCHES
    if not no_of_instances:
        no_of_instances = NUM_INSTANCES

    crawler = Crawler(torrc_dict, url_list, tbb_version, experiment)
    wl_log.info(sys.argv)

    # Run crawl
    try:
        crawler.crawl(no_of_batches, no_of_instances,
                      start_line=start_line - 1)
    except KeyboardInterrupt:
        wl_log.warning("Keyboard interrupt! Quitting...")
    except Exception as e:
        wl_log.error("Exception: \n%s"
                     % (traceback.format_exc()))
    finally:
        crawler.stop_crawl()
