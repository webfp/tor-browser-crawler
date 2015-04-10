import os
import platform
from tempfile import gettempdir

if 'x86_64' in platform.processor():
    arch = '64'
else:
    arch = '32'

# shortcuts
path = os.path
join = path.join
dirname = os.path.dirname
expanduser = os.path.expanduser

# GLOBALS
# separator for craeating indexation keys
SEP = '-'

# timeouts and pauses
WAIT_IN_SITE = 5             # time to wait after the page loads
PAUSE_BETWEEN_INSTANCES = 4  # pause before visiting the same site (instances)
HARD_VISIT_TIMEOUT = 120     # in case a visit takes longer than finish it

# max dumpcap size in KB
MAX_DUMP_SIZE = 30000

# max filename length
MAX_FNAME_LENGTH = 200

# Wang et al's crawl parameters
DEFAULT_NUM_BATCHES = 10
DEFAULT_NUM_WEBSTIES = 100
DEFAULT_NUM_TRIALS = 40

# Tor browser version suffixes

# The version used by Wang & Goldberg
TBB_V_2_4_7_A1 = "2.4.7-alpha-1"
TBB_WANG_ET_AL = TBB_V_2_4_7_A1

TBB_V_3_5 = "3.5"
TBB_V_4_0_8 = "4.0.8"
TBB_DEFAULT_VERSION = TBB_V_4_0_8

TBB_KNOWN_VERSIONS = [TBB_V_2_4_7_A1, TBB_V_3_5, TBB_V_4_0_8]

# Default paths
TEMP_DIR = gettempdir()
BASE_DIR = path.abspath(os.path.dirname(__file__))
DATASET_DIR = join(BASE_DIR, "datasets")
ALEXA_DIR = join(DATASET_DIR, "alexa")
TEST_DIR = join(BASE_DIR, 'test')
RESULTS_DIR = join(BASE_DIR, 'results')
ETC_DIR = join(BASE_DIR, 'etc')
PERMISSIONS_DB = join(ETC_DIR, 'permissions.sqlite')
HOME_PATH = expanduser('~')
TBB_BASE_DIR = join(BASE_DIR, 'tbb')

# Directory structure and paths depend on TBB versions
# Path to Firefox binary in TBB dir
TBB_V2_FF_BIN_PATH = join('App', 'Firefox', 'firefox')
TBB_V3_FF_BIN_PATH = join('Browser', 'firefox')
TBB_V4_FF_BIN_PATH = join('Browser', 'firefox')

TBB_FF_BIN_PATH_DICT = {"2": TBB_V2_FF_BIN_PATH,
                        "3": TBB_V3_FF_BIN_PATH,
                        "4": TBB_V4_FF_BIN_PATH,
                        }

# Path to Firefox profile in TBB dir
TBB_V2_PROFILE_PATH = join('Data', 'profile')
TBB_V3_PROFILE_PATH = join('Data', 'Browser', 'profile.default')
TBB_V4_PROFILE_PATH = join('Browser', 'TorBrowser', 'Data',
                           'Browser', 'profile.default')

TBB_PROFILE_DIR_DICT = {"2": TBB_V2_PROFILE_PATH,
                        "3": TBB_V3_PROFILE_PATH,
                        "4": TBB_V4_PROFILE_PATH,
                        }

# Path to Tor binary in TBB dir
TOR_V2_BINARY_PATH = join('App', 'tor')
TOR_V3_BINARY_PATH = join('Tor', 'tor')
TOR_V4_BINARY_PATH = join('Browser', 'TorBrowser', 'Tor', 'tor')

TOR_BINARY_PATH_DICT = {"2": TOR_V2_BINARY_PATH,
                        "3": TOR_V3_BINARY_PATH,
                        "4": TOR_V4_BINARY_PATH,
                        }
# Path to Tor binary in TBB dir
TOR_V2_DATA_DIR = join('Data', 'Tor')
TOR_V3_DATA_DIR = join('Data', 'Tor')
TOR_V4_DATA_DIR = join('Browser', 'TorBrowser', 'Data', 'Tor')

TOR_DATA_DIR_DICT = {"2": TOR_V2_DATA_DIR,
                     "3": TOR_V3_DATA_DIR,
                     "4": TOR_V4_DATA_DIR,
                     }

# Top URLs localized (DE) to prevent the effect of localization
LOCALIZED_DATASET = join(ETC_DIR, "localized-urls-100-top.csv")

# Experiment types determines what to do during the visits
EXP_TYPE_WANG_ET_AL = 1  # Tao's experiments
EXP_TYPE_MULTITAB_ALEXA = 2  # open Alexa sites in multiple tabs
EXP_TYPE_MULTITAB_FIXED_BG_SITE = 3  # have a fixed site (e.g. Twitter) in
# the background and open Alexa sites in multiple tabs

# Tor ports
SOCKS_PORT = 9050
CONTROLLER_PORT = 9051
MAX_ENTRY_GUARDS = "1"

# torrc dictionaries
TORRC_DEFAULT = {'SocksPort': str(SOCKS_PORT),
                 'ControlPort': str(CONTROLLER_PORT)}

TORRC_WANG_AND_GOLDBERG = {'SocksPort': str(SOCKS_PORT),
                           'ControlPort': str(CONTROLLER_PORT),
                           'MaxCircuitDirtiness': '600000',
                           'UseEntryGuards': '0'
                           }


def get_tbb_major_version(version):
    """Return major version of TBB."""
    return version.split(".")[0]


def get_tbb_dirname(version, os_name="linux", lang="en-US"):
    """Return path for Tor Browser Bundle for given version and bits."""
    return "tor-browser-%s%s-%s_%s" % (os_name, arch, version, lang)


def get_tbb_path(version, os_name="linux", lang="en-US"):
    """Return path for Tor Browser Bundle for given version and bits."""
    dirname = get_tbb_dirname(version, os_name, lang)
    return join(TBB_BASE_DIR, dirname)


def get_tb_bin_path(version, os_name="linux", lang="en-US"):
    """Return a binary path for Tor Browser."""
    major = get_tbb_major_version(version)
    # bin_path = TBB_V3_FF_BIN_PATH if major is "3" else TBB_V2_FF_BIN_PATH
    bin_path = TBB_FF_BIN_PATH_DICT[major]
    dir_path = get_tbb_path(version, os_name, lang)
    return join(dir_path, bin_path)


def get_tor_bin_path(version, os_name="linux", lang="en-US"):
    """Return a binary path for Tor."""
    major = get_tbb_major_version(version)
    bin_path = TOR_BINARY_PATH_DICT[major]
    dir_path = get_tbb_path(version, os_name, lang)
    return join(dir_path, bin_path)


def get_tbb_profile_path(version, os_name="linux", lang="en-US"):
    """Return profile path for Tor Browser Bundle."""
    major = get_tbb_major_version(version)
    profile = TBB_PROFILE_DIR_DICT[major]
    dir_path = get_tbb_path(version, os_name, lang)
    return join(dir_path, profile)


def get_tor_data_path(version, os_name="linux", lang="en-US"):
    """Return the path for Data dir of Tor."""
    major = get_tbb_major_version(version)
    data_path = TOR_DATA_DIR_DICT[major]
    tbb_path = get_tbb_path(version, os_name, lang)
    return join(tbb_path, data_path)
