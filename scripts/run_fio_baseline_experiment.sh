#!/bin/bash
#!/bin/env python

DEVICE=nvme2n1 # sfdv0n1 = scaleflux, nvme1n1 = intel ssd
DEVICEPATH=/dev/$DEVICE 
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
PATTERN=("read" "randread" "randwrite" "write")
BASEPATH=/home/sfluxteam/ScaleFlux-Analysis/
LOGPATH=${BASEPATH}logs/
PARSEDLOGSPATH=${BASEPATH}parsedlogs/fio-$TIMESTAMP-$DEVICE/
RESULTSPATH=${BASEPATH}results/fio-$TIMESTAMP-$DEVICE/
EBPFPATH=${BASEPATH}build/ebpf/
FIOPATH=${BASEPATH}fio-testsuite/

rm -rf $LOGPATH

mkdir -p $LOGPATH
mkdir -p $PARSEDLOGSPATH
mkdir -p $RESULTSPATH

echo "Running steady state job"
fio ${FIOPATH}steadystate-${DEVICE}.fio --output=steadystate/${DEVICE}-baseline-compress.log
for pattern in ${PATTERN[@]}; do
    echo "Starting run for ${pattern}"
    # Must run with sudo rights
    # PREDATAWRITTEN=$(nvme smart-log ${DEVICEPATH} | grep "data_units_written")
    # PREDATAREAD=$(nvme smart-log ${DEVICEPATH} | grep "data_units_read")

    echo "Starting eBPF"
    # COMMAND="fio ${FIOPATH}baseline.fio --rw=${pattern} --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}fio-${pattern} --output=${LOGPATH}fio-${pattern}-results.log"
    # # Remember quotes :)
    # # FU
    # EBPFFILE="${LOGPATH}ebpf-${pattern}"
    
    # ${EBPFPATH}ebpf-ssd-analysis "${COMMAND}" "$EBPFFILE"

    fio ${FIOPATH}baseline.fio --rw=${pattern} --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}fio-${pattern} --output=${LOGPATH}fio-${pattern}-results.log

    # POSTDATAWRITTEN=$(nvme smart-log ${DEVICEPATH} | grep "data_units_written")
    # POSTDATAREAD=$(nvme smart-log ${DEVICEPATH} | grep "data_units_read")

    echo "Parsing results"
    # echo -e "Drive data written\n${PREDATAWRITTEN}\n${POSTDATAWRITTEN}" >> ${EBPFFILE}_stats.log
    # echo -e "Drive data read\n${PREDATAREAD}\n${POSTDATAREAD}" >> ${EBPFFILE}_stats.log

    # echo "Running ebpf parser"
    # python3 ebpf_parser.py --ebpf_log="${EBPFFILE}_timeline.log" --csv_log="${RESULTSPATH}ebpf-${pattern}-results-parsed.csv"
    echo "Running fio parser"
    python3 fio_parser.py "${LOGPATH}fio-${pattern}-results.log" "${RESULTSPATH}fio-${pattern}-results-parsed.csv"
    echo "Creating lat graph"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_lat.1.log" "${RESULTSPATH}"
    echo "Creating slat graph"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_slat.1.log" "${RESULTSPATH}"
    echo "Creating clat graph"
    python3 timeline_graph.py "${LOGPATH}fio-${pattern}_clat.1.log" "${RESULTSPATH}"
    # echo "Creating dlat graph"
    # python3 timeline_graph.py "${LOGPATH}ebpf-${pattern}_dlat.log" "${RESULTSPATH}"

    python3 svg_merge.py "${RESULTSPATH}fio-${pattern}_clat.1.log.svg" "${RESULTSPATH}fio-${pattern}_lat.1.log.svg" "${RESULTSPATH}fio-${pattern}_slat.1.log.svg" --output="${RESULTSPATH}${pattern}.svg"

    mv ${LOGPATH}*_stats.log $PARSEDLOGSPATH
    mv ${LOGPATH}*.log $PARSEDLOGSPATH

done

chown -R sfluxteam $PARSEDLOGSPATH
chown -R sfluxteam $RESULTSPATH
