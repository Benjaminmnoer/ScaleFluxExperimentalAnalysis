# Input: ebpf log  
# Output: parsed csv and dlat timeline log

import json
import sys
import os
import re
import pprint
import pandas as pd
import numpy as np
import argparse
import csv

def pretty_print(data):
    print("EBPF --")
    print("iops: {},  bw: {}".format(data[0], data[1]))
    print("slat_min: {},  slat_max: {}, slat_avg: {}, slat_stdev: {}".format(data[2], data[3], data[4], data[5]))
    print("dlat_min: {},  dlat_max: {}, dlat_avg: {}, dlat_stdev: {}".format(data[6], data[7], data[8], data[9]))
    print("lat_min: {},  lat_max: {}, lat_avg: {}, lat_stdev: {}".format(data[10], data[11], data[12], data[13]))
    print("1.00th: {}, 5.00th: {}, 10.00th: {}, 20.00th: {}".format(data[14], data[15], data[16], data[17]))
    print("30.00th: {}, 40.00th: {}, 50.00th: {}, 60.00th: {}".format(data[18], data[19], data[20], data[21]))
    print("70.00th: {}, 80.00th: {}, 90.00th: {}, 95.00th: {}".format(data[22], data[23], data[24], data[25]))
    print("99.00th: {}, 99.50th: {}, 99.90th: {}, 99.95th: {}".format(data[26], data[27], data[28], data[29]))
    print("99.99th: {}".format(data[30]))
    print("EBPF --")

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='Parse ebpf log')
    parser.add_argument('--ebpf_log', type=str, help='input ebpf log file', required=True)
    parser.add_argument('--csv_log', type=str, help='ouput csv log file', required=False)
    parser.add_argument('--dlat_log', type=str, help='output dlat log file', required=False)

    args = parser.parse_args()

    # get ebpf log path
    ebpf_log = args.ebpf_log
    # get csv log path
    csv_log = args.csv_log
    if csv_log is None:
        csv_log = ebpf_log + '.csv'
    # get dlat log path
    dlat_log = args.dlat_log 
    if dlat_log is None:
        filename = re.search(r'(?<=^).*?(?=[_])', os.path.basename(ebpf_log)).group(0) + '_dlat.log'
        path = ebpf_log.replace(os.path.basename(ebpf_log), '')
        dlat_log = path + filename

    # open ebpf log
    with open(ebpf_log, 'r') as f:
        lines = f.readlines()

    # data
    data = []

    # non job related lines
    count = 0
    unrelated_count = 0

    # For each line extract the data (0, 16417508296525, 16417508308557, 4096, fio)
    for line in lines:
        # try extract data to ints
        match = re.search(r'\s*([\d]+),\s*([\d]+),\s*([\d]+),\s*([\d]+),\s*(\(*[\w]+\)*)', line)
        if match:
            count += 1

            insert = int(match.group(1))
            issue = int(match.group(2))
            complete = int(match.group(3))
            size = match.group(4)
            comm = match.group(5)
         
            if comm.lower() not in ['fio', 'rocksdb']:
                unrelated_count += 1
                continue

            slat = issue - insert
            dlat = complete - issue
            lat = slat + dlat

            # if no insert ts then we can't compute slat and lat.
            if insert == 0:
                slat = 0
                lat = 0

            # add to data and convert to int
            data.append([int(complete), int(slat), int(dlat), int(lat), int(size)])
        else:
            print("No match: " + line)

    print(f"Total non job related ts entries: {str(unrelated_count)} ({str(round(unrelated_count / count, 4))}%)" )

    # convert data to pandas dataframe
    data = np.array(data)
    data = pd.DataFrame(data, columns=['completion ts', 'slat', 'dlat', 'lat', 'size'])

    # Convert slat, dlat, lat to usec
    data['slat'] = data['slat'].apply(lambda x: x / 1000)
    data['dlat'] = data['dlat'].apply(lambda x: x / 1000)
    data['lat'] = data['lat'].apply(lambda x: x / 1000)

    # Sort by completion ts
    data = data.sort_values('completion ts')

    # slat average, min, max, stdev
    slat_avg = data['slat'].mean()
    slat_min = data['slat'].min()
    slat_max = data['slat'].max()
    slat_stdev = data['slat'].std()

    # dlat average, min, max, stdev
    dlat_avg = data['dlat'].mean()
    dlat_min = data['dlat'].min()
    dlat_max = data['dlat'].max()
    dlat_stdev = data['dlat'].std()

    # lat average, min, max, stdev
    lat_avg = data['lat'].mean()
    lat_min = data['lat'].min()
    lat_max = data['lat'].max()
    lat_stdev = data['lat'].std()

    # Take smallest and highest element
    first_completion = data.iloc[0]['completion ts']
    last_completion = data.iloc[-1]['completion ts']

    # elapsed time in nanoseconds
    elapsed_time = last_completion - first_completion
    # elapsed time in seconds
    elapsed_time_s = elapsed_time / 1_000_000_000

    # total size in MB
    total_size = data['size'].sum() / 1_000_000

    # throughput in MB/s
    throughput = total_size / elapsed_time_s

    # iops
    iops = data.shape[0] / elapsed_time_s

    # get dlat percentiles
    dlat_percentiles = data['dlat'].quantile([0.01, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99, 0.995, 0.999, 0.9995, 0.9999]).tolist()

    # Map all completion ts to elapsed time in ms (completion ts - first_completion) / 1_000_000
    data['completion ts'] = data['completion ts'].apply(lambda x: (x - first_completion) / 1_000_000)

    # Convert dlat back to nsec (conversions are  handled by graph tool)
    data['dlat'] = data['dlat'].apply(lambda x: x * 1000)

    # Define csv columns
    header = ['iops', 'bw','slat_min', 'slat_max', 'slat_avg', 'slat_stdev', 
                'dlat_min', 'dlat_max', 'dlat_avg', 'dlat_stdev', 
                'lat_min', 'lat_max', 'lat_avg', 'lat_stdev',
                '1,00', '5,00', '10,00', '20,00',
                 '30,00', '40,00', '50,00', '60,00',
                  '70,00', '80,00', '90,00', '95,00',
                   '99,00', '99,50', '99,90', '99,95',
                    '99,99']
    
    data_to_write = [iops, throughput, slat_min, slat_max, slat_avg, slat_stdev, dlat_min, dlat_max, dlat_avg, dlat_stdev, lat_min, lat_max, lat_avg, lat_stdev]
    data_to_write.extend(dlat_percentiles)

    for i in range(len(data_to_write)):
        data_to_write[i] = "{}".format(round(float(data_to_write[i]),2)).replace('.', ',')

    pretty_print(data_to_write)
 
    print("Writing to csv file")
    # open csv output file and write
    with open(csv_log, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(data_to_write)

    # open timeline output file and write
    print("Writing to timeline file")
    with open(dlat_log, 'w') as f:
        # format: completion ts, dlat, 0, 0
        for i in range(0, data.shape[0]):
            f.write(str(data['completion ts'].iloc[i]) + ',' + str(data['dlat'].iloc[i]) + ',0,0\n')


if __name__ == "__main__":
    main()