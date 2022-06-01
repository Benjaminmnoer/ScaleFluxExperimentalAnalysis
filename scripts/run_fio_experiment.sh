#!/bin/bash
#!/bin/env python

DEVICE=/dev/sfdv0n1 # sfdv0n1 = scaleflux, nvme1n1 = intel ssd
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
PATTERN=("read" "randread" "randwrite" "write")
BASEPATH=/home/sfluxteam/ScaleFlux-Analysis/
LOGPATH=${BASEPATH}logs/
PARSEDLOGSPATH=${BASEPATH}parsedlogs/fio-$TIMESTAMP/
RESULTSPATH=${BASEPATH}results/fio-$TIMESTAMP/
EBPFPATH=${BASEPATH}build/ebpf/
FIOPATH=${BASEPATH}fio-testsuite/

rm -rf $LOGPATH

mkdir -p $LOGPATH
mkdir -p $PARSEDLOGSPATH
mkdir -p $RESULTSPATH

for pattern in ${PATTERN[@]}; do
    echo "Starting run for ${pattern}"
    # Must run with sudo rights
    PREDATAWRITTEN=$(nvme smart-log ${DEVICE} | grep "data_units_written")

    echo "Starting eBPF"
    COMMAND="fio ${FIOPATH}baseline.fio --rw=${pattern} --filename=${DEVICE} --write_lat_log=${LOGPATH}fio-${pattern} --output=${LOGPATH}fio-${pattern}-results.log"
    # Remember quotes :)
    # FU
    EBPFFILE="${LOGPATH}ebpf-${pattern}"
    
    ${EBPFPATH}ebpf-ssd-analysis "${COMMAND}" "$EBPFFILE"

    POSTDATAWRITTEN=$(nvme smart-log ${DEVICE} | grep "data_units_written")

    echo "Parsing results"
    echo -e "Drive data written\n${PREDATAWRITTEN}\n${POSTDATAWRITTEN}" >> ${EBPFFILE}_stats.log

    python3 ebpf_parser.py --ebpf_log="${EBPFFILE}_timeline.log" --csv_log="${RESULTSPATH}ebpf-${pattern}-results-parsed.csv"
    python3 fio_parser.py "${LOGPATH}fio-${pattern}-results.log" "${RESULTSPATH}fio-${pattern}-results-parsed.csv"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_lat.1.log" "${RESULTSPATH}"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_slat.1.log" "${RESULTSPATH}"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_clat.1.log" "${RESULTSPATH}"
    python3 timeline_graph.py "${LOGPATH}ebpf-${pattern}_dlat.log" "${RESULTSPATH}"

    python3 svg_merge.py "${RESULTSPATH}ebpf-${pattern}_dlat.log.svg" "${RESULTSPATH}fio-${pattern}_clat.1.log.svg" "${RESULTSPATH}fio-${pattern}_lat.1.log.svg" "${RESULTSPATH}fio-${pattern}_slat.1.log.svg" --output="${RESULTSPATH}${pattern}.svg"

    mv ${LOGPATH}*_stats.log $PARSEDLOGSPATH
    mv ${LOGPATH}*.log $PARSEDLOGSPATH

done

chown -R sfluxteam $PARSEDLOGSPATH
chown -R sfluxteam $RESULTSPATH