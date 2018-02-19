#!/bin/bash
URL_FILE=$1
OUTPUT_FILE=$2
for hs in `cat ${URL_FILE}`; do
  torsocks curl $hs -s -f -o /dev/null || echo "$hs is down.";
done | grep "down" > $OUTPUT_FILE
