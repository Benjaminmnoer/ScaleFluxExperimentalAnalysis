#!/bin/bash
#!/bin/env python

DEVICE=sfdv0n1 # sfdv0n1 = scaleflux, nvme1n1 = intel ssd, nvme2n1 = optane
DEVICEPATH=/dev/$DEVICE 
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
PATTERN=("randread" "read" "randwrite" "write")
BLOCKSIZES=("4k" "16k" "32k" "64k")
# IODEPTHS=("2" "4" "6" "8")
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

for blocksize in ${BLOCKSIZES[@]}; do
# for iodepth in ${IODEPTHS[@]}; do
    BSRESULTSPATH=${RESULTSPATH}${blocksize}/
    mkdir -p $BSRESULTSPATH
    echo "Starting runs for blocksize: ${blocksize}"

#      ScaleFlux only!!
#     echo "Resetting scaleflux device"
#     echo y | sfx-nvme sfx set-feature /dev/sfxv0 -f 0xdc
#     sleep 30
    
    echo "Running steady state job"
    fio ${FIOPATH}steadystate-${DEVICE}.fio --output=steadystate/${DEVICE}-${blocksize}.log
    for pattern in ${PATTERN[@]}; do
        ts=$(date "+%Y-%m-%d-%H-%M")
        echo "${ts}: Starting run for pattern: ${pattern}"
        # Must run with sudo rights
        # PREDATAWRITTEN=$(nvme smart-log ${DEVICEPATH} | grep "data_units_written")
        # PREDATAREAD=$(nvme smart-log ${DEVICEPATH} | grep "data_units_read")

        echo "Starting fio"
        # COMMAND="fio ${FIOPATH}advanced.fio --blocksize=${blocksize} --rw=${pattern} --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}${blocksize}-fio-${pattern} --output=${LOGPATH}${blocksize}-fio-${pattern}-results.log"
        # Remember quotes :)
        # FU
        # EBPFFILE="${LOGPATH}${blocksize}-ebpf-${pattern}"
        
        # ${EBPFPATH}ebpf-ssd-analysis "${COMMAND}" "$EBPFFILE"

        fio ${FIOPATH}advanced.fio --bs=${blocksize} --rw=${pattern} --filename=${DEVICEPATH} --write_lat_log=${LOGPATH}${blocksize}-fio-${pattern} --output=${LOGPATH}${blocksize}-fio-${pattern}-results.log

        # POSTDATAWRITTEN=$(nvme smart-log ${DEVICEPATH} | grep "data_units_written")
        # POSTDATAREAD=$(nvme smart-log ${DEVICEPATH} | grep "data_units_read")

        # echo "Parsing results"
        # echo -e "Drive data written\n${PREDATAWRITTEN}\n${POSTDATAWRITTEN}" >> ${EBPFFILE}_stats.log
        # echo -e "Drive data read\n${PREDATAREAD}\n${POSTDATAREAD}" >> ${EBPFFILE}_stats.log

	# echo "Parsing ebpf"
        # python3 ebpf_parser.py --ebpf_log="${EBPFFILE}_timeline.log" --csv_log="${BSRESULTSPATH}${blocksize}-ebpf-${pattern}-results-parsed.csv"
	echo "Parsing fio"
        python3 fio_parser.py "${LOGPATH}${blocksize}-fio-${pattern}-results.log" "${BSRESULTSPATH}${blocksize}-fio-${pattern}-results-parsed.csv"
	echo "Creating lat graph"
        python3 timeline_graph.py "${LOGPATH}${blocksize}-fio-${pattern}_lat.1.log" "${BSRESULTSPATH}"
	echo "Creating slat graph"
        python3 timeline_graph.py "${LOGPATH}${blocksize}-fio-${pattern}_slat.1.log" "${BSRESULTSPATH}"
	echo "Creating clat graph"
        python3 timeline_graph.py "${LOGPATH}${blocksize}-fio-${pattern}_clat.1.log" "${BSRESULTSPATH}"
	# echo "Creating dlat graph"
        # python3 timeline_graph.py "${LOGPATH}${blocksize}-ebpf-${pattern}_dlat.log" "${BSRESULTSPATH}"

        # "${BSRESULTSPATH}${blocksize}-ebpf-${pattern}_dlat.log.svg"
        python3 svg_merge.py "${BSRESULTSPATH}${blocksize}-fio-${pattern}_clat.1.log.svg" "${BSRESULTSPATH}${blocksize}-fio-${pattern}_lat.1.log.svg" "${BSRESULTSPATH}${blocksize}-fio-${pattern}_slat.1.log.svg" --output="${RESULTSPATH}${blocksize}-${pattern}.svg"

        # mv ${LOGPATH}*_stats.log $PARSEDLOGSPATH
        mv ${LOGPATH}*.log $PARSEDLOGSPATH
    done
done

chown -R sfluxteam:sfluxteam $PARSEDLOGSPATH
chown -R sfluxteam:sfluxteam $RESULTSPATH
