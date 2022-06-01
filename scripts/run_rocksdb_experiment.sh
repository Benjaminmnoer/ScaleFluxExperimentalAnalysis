#!/bin/bash
TIMESTAMP=$(date "+%Y-%m-%d-%H-%M")
COMPENGINES=("none" "zlib")
COMPRATIOS=("1.0" "0.5")

IFS="" # Fixes readwhilewriting --threads=2 being split in 2
BENCHMARKS=("overwrite"
            "readseq"
            "readrandom"
            "readwhilewriting --threads=2"
            "readwhilewriting --threads=4"
            "readwhilewriting --threads=6" 
            "readwhilewriting --threads=8")


TARGET=optane
DEVICE=nvme2n1
BASEPATH=/home/sfluxteam/ScaleFlux-Analysis/
LOGPATH=${BASEPATH}logs/
PARSEDLOGSPATH=${BASEPATH}parsedlogs/rocksdb-${DEVICE}-${TIMESTAMP}/
RESULTSPATH=${BASEPATH}results/${TARGET}/rocksdb-${DEVICE}-${TIMESTAMP}/
EBPFPATH=${BASEPATH}build/ebpf/
ROCKSPATH=${BASEPATH}third-party/rocksdb/
DBPATH=/${TARGET}

rm -rf $LOGPATH
# rm $DBPATH/*

mkdir -p $LOGPATH
mkdir -p $PARSEDLOGSPATH
mkdir -p $RESULTSPATH

mkdir steadystate

for compengine in ${COMPENGINES[@]}; do
    echo "$(date "+%Y-%m-%d-%H-%M"): Starting runs for ${compengine}"
    for compratio in ${COMPRATIOS[@]}; do
        # if [ "$compengine" == "none" ] && [ "$compratio" == "0.5"  ]; then
        #     echo "Skipping $compengine $compratio"
        #     continue
        # fi

        # echo "$(date "+%Y-%m-%d-%H-%M"): (Re)Building filesystem"
        umount /dev/$DEVICE
        mkfs.xfs -f /dev/$DEVICE
        mount /dev/$DEVICE $DBPATH 

        echo "$(date "+%Y-%m-%d-%H-%M"): Running with ratio ${compratio} (${compengine})"
        # echo "$(date "+%Y-%m-%d-%H-%M"): Starting steady state"
        # 5497558138 = sfdv0n1 80 %
        # 593750000 = nvme2n1 80 %
        # 209715200 = 100 gb
        ${ROCKSPATH}db_bench -benchmarks=fillseq,stats -cache_size=-43 -compression_type=${compengine} -compression_ratio=$compratio -num=593750000 -statistics -memtable_bloom_size_ratio=0 -value_size=496 -db=$DBPATH -open_files=1000 -use_direct_io_for_flush_and_compaction=true -use_direct_reads=true > steadystate/rocksdb-${compengine}-${compratio}-steady.log
        mv steadystate/* $RESULTSPATH

        for benchmark in ${BENCHMARKS[@]}; do
            echo "$(date "+%Y-%m-%d-%H-%M"): Running benchmark ${benchmark}"

            # Split command if applicable
            IFS=" " read benchmark_ optional <<< $benchmark

            echo "$(date "+%Y-%m-%d-%H-%M"): Starting RocksDB"
            # -num=20000000
            ${ROCKSPATH}db_bench -benchmarks=stats,${benchmark_} -use_existing_db -cache_size=-43 -compression_type=${compengine} -compression_ratio=$compratio -statistics -memtable_bloom_size_ratio=0 -value_size=496 -db=$DBPATH -open_files=1000 -use_direct_io_for_flush_and_compaction=true -duration=600 -use_direct_reads=true ${optional} > ${LOGPATH}rocksdb-${compengine}-${compratio}-"${benchmark}"-results.log &
            rockspid=$!
            python3 ../ebpf/cachetop.py --pid=$rockspid --output=${RESULTSPATH}${compengine}-${compratio}-"${benchmark}"-cache.log > /dev/null
            wait ${rockspid}

            echo "$(date "+%Y-%m-%d-%H-%M"): Parsing results"
            python3 rocksdb_parser.py "${LOGPATH}rocksdb-${compengine}-${compratio}-${benchmark}-results.log"

            mv ${LOGPATH}*.json $RESULTSPATH
            mv ${LOGPATH}*.log $PARSEDLOGSPATH

            IFS=""
        done
    done
done

chown -R sfluxteam:sfluxteam $PARSEDLOGSPATH
chown -R sfluxteam:sfluxteam $RESULTSPATH