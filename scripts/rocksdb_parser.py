# Input: rocksdb statistics file
# Output: parsed statistics

# Extract:
# fillrandom   :       8.370 micros/op 118357 ops/sec;   57.8 MB/s
# Uptime(secs): 0.0 total, 0.0 interval
# Level 0 read latency histogram (micros):
# rocksdb.bytes.written COUNT : 528000
# rocksdb.db.write.micros P50 : 0.651890 P95 : 1.953125 P99 : 2.861111 P100 : 84.000000 COUNT : 1000 SUM : 1360

import json
import sys
import os
import re
import pprint

# Lines:
# Count: 2323213 Average: 0.8250  StdDev: 0.99
# Min: 0  Median: 0.5239  Max: 38
# Percentiles: P50: 0.52 P75: 0.79 P99: 1.86 P99.9: 17.55 P99.99: 29.98
def TryMatchHistogramLines(line, lines):
    data = {}
    # next line
    line = next(lines)
    match = re.search(r'Count:\s+([\d\.]+)\s+Average:\s+([\d\.]+)\s+StdDev:\s+([\d\.]+)', line)
    if match:
        data['Count'] = match.group(1)
        data['Average'] = match.group(2)
        data['StdDev'] = match.group(3)
    # next line
    line = next(lines)

    match = re.search(r'Min:\s+([\d\.]+)\s+Median:\s+([\d\.]+)\s+Max:\s+([\d\.]+)', line)
    if match:
        data['Min'] = match.group(1)
        data['Median'] = match.group(2)
        data['Max'] = match.group(3)
    # next line
    line = next(lines)

    match = re.search(r'Percentiles:\s+P50:\s+([\d\.]+)\s+P75:\s+([\d\.]+)\s+P99:\s+([\d\.]+)\s+P99\.9:\s+([\d\.]+)\s+P99\.99:\s+([\d\.]+)\s*', line)
    if match:
        data['P50'] = match.group(1)
        data['P75'] = match.group(2)
        data['P99'] = match.group(3)
        data['P99.9'] = match.group(4)
        data['P99.99'] = match.group(5)

    return data

def main():
    """
    Main function
    """
    if len(sys.argv) != 2:
        print("Usage: python rocksdb_parser.py path/to/rocksdb/file.log")
        exit(0)
    
    # get rocksdb file
    rocksdb_file = sys.argv[1]

    # get rocksdb data
    rocksdb_data = []
    with open(rocksdb_file, 'r') as f:
        lines = iter(f.readlines())
        for line in lines:
            # try extract benchmark
            match = re.search(r'(\w+)\s+:\s+([\d\.]+)\s+micros/op\s+([\d\.]+)\s+ops/sec;\s+([\d\.]+)\s+MB/s', line)
            if match:
                rocksdb_data.append({
                    match.group(1): {
                        'micros/op': match.group(2),
                        'ops/sec': match.group(3),
                        'MB/s': match.group(4)
                    }
                })

            # try extract uptime
            match2 = re.search(r'Uptime\(secs\):\s+([\d\.]+)\s+total,\s+([\d\.]+)\s+interval', line)
            if match2:
                rocksdb_data.append({
                    'uptime (secs)': {
                        'total': match2.group(1),
                        'interval': match2.group(2)
                    }
                })

            # try extract level x read latency histogram
            match3 = re.search(r'Level\s+([\d]+)\s+read\s+latency\s+histogram\s+\(micros\):', line)
            if match3:
                data = TryMatchHistogramLines(line, lines)
                rocksdb_data.append({
                    'level_' + match3.group(1) + '_read_latency_histogram (micros)': data
                })


            # try extract rocksdb.bytes.written
            match4 = re.search(r'rocksdb\.bytes\.written\s+COUNT\s+:\s+([\d\.]+)', line)
            if match4:
                rocksdb_data.append({
                    'rocksdb.bytes.written (bytes)': {
                        'COUNT': match4.group(1)
                    }
                })

            # try extract rocksdb.write.micros
            match5 = re.search(r'rocksdb\.db\.write\.micros\s+P50\s+:\s+([\d\.]+)\s+P95\s+:\s+([\d\.]+)\s+P99\s+:\s+([\d\.]+)\s+P100\s+:\s+([\d\.]+)\s+COUNT\s+:\s+([\d\.]+)\s+SUM\s+:\s+([\d\.]+)', line)
            if match5:
                rocksdb_data.append({
                    'rocksdb.db.write.micros (micros)': {
                        'P50': match5.group(1),
                        'P95': match5.group(2),
                        'P99': match5.group(3),
                        'P100': match5.group(4),
                        'COUNT': match5.group(5),
                        'SUM': match5.group(6)
                    }
                })
            
            # try extract rocksdb.bytes.read
            match6 = re.search(r'rocksdb\.bytes\.read\s+COUNT\s+:\s+([\d\.]+)', line)
            if match6:
                rocksdb_data.append({
                    'rocksdb.bytes.read (bytes)': {
                        'COUNT': match6.group(1)
                    }
                })

            # try extract rocksdb.get.micros
            match7 = re.search(r'rocksdb\.db\.get\.micros\s+P50\s+:\s+([\d\.]+)\s+P95\s+:\s+([\d\.]+)\s+P99\s+:\s+([\d\.]+)\s+P100\s+:\s+([\d\.]+)\s+COUNT\s+:\s+([\d\.]+)\s+SUM\s+:\s+([\d\.]+)', line)
            if match7:
                rocksdb_data.append({
                    'rocksdb.db.get.micros (micros)': {
                        'P50': match7.group(1),
                        'P95': match7.group(2),
                        'P99': match7.group(3),
                        'P100': match7.group(4),
                        'COUNT': match7.group(5),
                        'SUM': match7.group(6)
                    }
                })

    # pretty print rocksdb data
    pprint.pprint(rocksdb_data)

    # write rocksdb data to file in json format
    with open(os.path.splitext(rocksdb_file)[0] + '.json', 'w') as f:
        f.write(json.dumps(rocksdb_data))

if __name__ == '__main__':
    main()