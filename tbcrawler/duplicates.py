import os
import sys
from os.path import isfile, dirname, join
from _collections import defaultdict

HS_DUPLICATES_FILE = "etc/hs_duplicates.txt"
FALLBACK_DUPS_FILE = join(dirname(dirname(os.path.realpath(__file__))), HS_DUPLICATES_FILE)


def ensure_dup_file(dup_file):
    if dup_file is None:
        dup_file = FALLBACK_DUPS_FILE
    if not isfile(dup_file):
        print("Can't find the duplicates file %s" %  dup_file)
        sys.exit(1)
    print "Will use the following duplicate file", dup_file
    return dup_file

def get_duplicate_list(dup_file=None):
    dup_file = ensure_dup_file(dup_file)
    dup_sets_arr = []
    for line in open(dup_file).readlines():
        dup_sets_arr.append(set([hs for hs in line.split()]))
    return dup_sets_arr

def is_duplicate(site1, site2, dup_file=None):
    dup_file = ensure_dup_file(dup_file)
    for line in open(dup_file).readlines():
        if site1 in line:
            return site2 in line
    else:
        return False

if __name__ == '__main__':
    # How to use:
    assert is_duplicate("en35tuzqmn4lofbk.onion", "4php6mnkteaouewp.onion")
    assert not is_duplicate("en35tuzqmn4lofbk.onion", "jsbpbdf6mpw6s2oz.onion")
    # you can also get the duplicate sets as a list and check the dups yourselves
    # this should be faster since you don't open the text file for each lookup
    dup_sets_arr = get_duplicate_list()
    for dup_set in dup_sets_arr:
        if "en35tuzqmn4lofbk.onion" in dup_set:
            assert "4php6mnkteaouewp.onion" in dup_set
