#!/bin/bash
INPUT_DIR=$1
OUTPUT_DIR=$2

# FILES=$(find $INPUT_DIR -name "*clat*")
mkdir "/home/sfluxteam/timelines/bandwidth/${OUTPUT_DIR}/"
for entry in "$INPUT_DIR"/64*write_clat*
do
    echo $entry
    python3 fio_lat_to_bandwidth_timeline.py --lat_log $entry
done
for entry in "$INPUT_DIR"/64*write_bw*
do
    echo $entry
    python3 timeline_graph.py "$entry" "/home/sfluxteam/timelines/bandwidth/${OUTPUT_DIR}/" 1400
done