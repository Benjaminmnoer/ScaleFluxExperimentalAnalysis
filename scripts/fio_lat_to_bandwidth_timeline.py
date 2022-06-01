# Input: fio lat timeline log  
# Output: parsed csv and bandwidth timeline log

import os
import re
import pandas as pd
import numpy as np
import argparse
import csv

def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='Parse ebpf log')
    parser.add_argument('--lat_log', type=str, help='input log log file', required=True)
    parser.add_argument('--bw_log', type=str, help='output dlat log file', required=False)

    args = parser.parse_args()

    # get lat log path
    lat_log = args.lat_log
    # get bw log path
    bw_log = args.bw_log 
    if bw_log is None:
        filename = re.search(r'(?<=^).*?(?=[_])', os.path.basename(lat_log)).group(0) + '_bw.log'
        path = lat_log.replace(os.path.basename(lat_log), '')
        bw_log = path + filename

    # open lat log
    with open(lat_log, 'r') as f:
        lines = f.readlines()

    # data
    data = []

    # non job related lines
    count = 0
    bracket = 1
    unrelated_count = 0
    size = 0
    brackets = {}

    # For each line extract the data (0, 16417508296525, 16417508308557, 4096, fio)
    for line in lines:
        # try extract data to ints
        match = re.search(r'\s*([\d]+),\s*([\d]+),\s*([\d]+),\s*([\d]+)', line)
        if match:
            count += 1

            ts = int(match.group(1))
            size = int(match.group(4))

            if ts >= (bracket * 1000):
                bracket = bracket + 1


            # add to data and convert to int
            if bracket not in brackets:
                brackets[bracket] = 1
            else:
                brackets[bracket] = brackets[bracket] + 1 
            
        else:
            print("No match: " + line)

    print(f"Total non job related ts entries: {str(unrelated_count)} ({str(round(unrelated_count / count, 4))}%)" )

    for bracket in brackets:
        data.append([bracket * 1000, int(brackets[bracket]*size)])

    # convert data to pandas dataframe
    data = np.array(data)
    data = pd.DataFrame(data, columns=['time', 'bw'])

    # Convert bw bytes to MB
    data['bw'] = data['bw'].apply(lambda x: x / 1_000_000)

    # open timeline output file and write
    print("Writing to timeline file")
    with open(bw_log, 'w') as f:
        # format: completion ts, bw, 0, 0
        for i in range(0, data.shape[0]):
            f.write(str(data['time'].iloc[i]) + ',' + str(data['bw'].iloc[i]) + ',0,0\n')


if __name__ == "__main__":
    main()