#!/bin/bash
#!/bin/env python

DEVICE=sfdv0n1 # sfdv0n1 = scaleflux, nvme1n1 = intel ssd, nvme2n1 = optane
DEVICEPATH=/dev/$DEVICE 
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
WRITETHREADS=("1" "2" "4" "6")
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

mkdir steadystate

# ScaleFlux only!!
# echo "Resetting scaleflux device"
# echo y | sfx-nvme sfx set-feature /dev/sfxv0 -f 0xdc

echo "$(date "+%Y-%m-%d-%H-%M"): Running steady state job"
fio ${FIOPATH}steadystate-${DEVICE}.fio --output=steadystate/${DEVICE}.log
for writethreads in ${WRITETHREADS[@]}; do
    BSRESULTSPATH=${RESULTSPATH}w${writethreads}/
    ts=$(date "+%Y-%m-%d-%H-%M")
    mkdir -p $BSRESULTSPATH
    echo "${ts}: Starting runs for number of write threads: ${writethreads}"


    echo "$(date "+%Y-%m-%d-%H-%M"): Starting fio read job"
    fio ${FIOPATH}advanced.fio --iodepth=2 --numjobs=7 --rw=randread --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}${writethreads}-fio-read --output=${LOGPATH}${writethreads}-fio-read-results.log &

    echo "$(date "+%Y-%m-%d-%H-%M"): Starting fio write job"
    fio ${FIOPATH}advanced.fio --iodepth=2 --numjobs=${writethreads} --rw=randwrite --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}${writethreads}-fio-write --output=${LOGPATH}${writethreads}-fio-write-results.log
    wait

	echo "$(date "+%Y-%m-%d-%H-%M"): Parsing fio read files"
    python3 fio_parser.py "${LOGPATH}${writethreads}-fio-read-results.log" "${BSRESULTSPATH}${writethreads}-fio-read-results-parsed.csv"
	echo "Creating lat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-read_lat.1.log" "${BSRESULTSPATH}"
	echo "Creating slat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-read_slat.1.log" "${BSRESULTSPATH}"
	echo "Creating clat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-read_clat.1.log" "${BSRESULTSPATH}"

    python3 svg_merge.py "${BSRESULTSPATH}${writethreads}-fio-read_clat.1.log.svg" "${BSRESULTSPATH}${writethreads}-fio-read_lat.1.log.svg" "${BSRESULTSPATH}${writethreads}-fio-read_slat.1.log.svg" --output="${RESULTSPATH}${writethreads}-read.svg"

    echo "$(date "+%Y-%m-%d-%H-%M"): Parsing fio write files"
    python3 fio_parser.py "${LOGPATH}${writethreads}-fio-write-results.log" "${BSRESULTSPATH}${writethreads}-fio-write-results-parsed.csv"
	echo "Creating lat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-write_lat.1.log" "${BSRESULTSPATH}"
	echo "Creating slat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-write_slat.1.log" "${BSRESULTSPATH}"
	echo "Creating clat graph"
    python3 timeline_graph.py "${LOGPATH}${writethreads}-fio-write_clat.1.log" "${BSRESULTSPATH}"

    python3 svg_merge.py "${BSRESULTSPATH}${writethreads}-fio-write_clat.1.log.svg" "${BSRESULTSPATH}${writethreads}-fio-write_lat.1.log.svg" "${BSRESULTSPATH}${writethreads}-fio-write_slat.1.log.svg" --output="${RESULTSPATH}${writethreads}-write.svg"

    mv ${LOGPATH}*.log $PARSEDLOGSPATH
done

chown -R sfluxteam:sfluxteam $PARSEDLOGSPATH
chown -R sfluxteam:sfluxteam $RESULTSPATH
