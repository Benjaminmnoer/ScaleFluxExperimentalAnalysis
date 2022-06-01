import sys
import csv
import os
import re

def pretty_print(data):
    print("iops: {},  bw: {}".format(data[0], data[1]))
    print("slat_min: {},  slat_max: {}, slat_avg: {}, slat_stdev: {}".format(data[2], data[3], data[4], data[5]))
    print("clat_min: {},  clat_max: {}, clat_avg: {}, clat_stdev: {}".format(data[6], data[7], data[8], data[9]))
    print("lat_min: {},  lat_max: {}, lat_avg: {}, lat_stdev: {}".format(data[10], data[11], data[12], data[13]))
    print("1.00th: {}, 5.00th: {}, 10.00th: {}, 20.00th: {}".format(data[14], data[15], data[16], data[17]))
    print("30.00th: {}, 40.00th: {}, 50.00th: {}, 60.00th: {}".format(data[18], data[19], data[20], data[21]))
    print("70.00th: {}, 80.00th: {}, 90.00th: {}, 95.00th: {}".format(data[22], data[23], data[24], data[25]))
    print("99.00th: {}, 99.50th: {}, 99.90th: {}, 99.95th: {}".format(data[26], data[27], data[28], data[29]))
    print("99.99th: {}".format(data[30]))


def fix_fio_format(string):
    match = re.search('[.](\d)k$', string)
    if match:
        string = string.split('.')[0] + match.group(1) + "00" 
    
    string = string.replace('.k', "000")
    string = string.replace('k', "000")

    return string

def get_scale(unit):
    if "usec" in unit:
        return 1
    if "msec" in unit:
        return 1000
    
    return 0.001

def get_latency(keyword, line):
    data = []
    # Amazing regex skills
    # try get keyword latency
    match = re.match(f'\s*(?:{keyword})\s+(?:[(])([^)]*)(?:.*)(?:min=)([^,]*)(?:.*(?:max=))([^,]*)(?:.*(?:avg=))([^,]*)(?:.*(?:stdev=))([^,]*)', line)
    if match:
        unit = match.group(1)
        scale = get_scale(unit)
        
        lat_min = float(fix_fio_format(match.group(2))) * scale
        lat_max = float(fix_fio_format(match.group(3))) * scale
        lat_avg = float(fix_fio_format(match.group(4))) * scale
        lat_stdev = float(fix_fio_format(match.group(5).replace("\n", ""))) * scale
            
        data.append(str(lat_min))
        data.append(str(lat_max))
        data.append(str(lat_avg))
        data.append(str(lat_stdev))

    return data

###############################################################################
# PARAMS: Input filepath, Output filepath
# Example usage:
# python fio_parser.py fio-test.log fio-test-parsed.csv
#
def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2] 

    if not os.path.isfile(input_file):
        print("File path {} does not exist. Exiting...".format(input_file))
        sys.exit()

    print("Parsing {}".format(input_file))
    f_in = open(input_file, 'r')

    percentiles = ['1.00th', '5.00th', '10.00th', '20.00th',
                 '30.00th', '40.00th', '50.00th', '60.00th',
                  '70.00th', '80.00th', '90.00th', '95.00th',
                   '99.00th', '99.50th', '99.90th', '99.95th',
                    '99.99th']

    lines = iter(f_in.readlines())
    i = 0
    data = []
    for line in lines:
        # try get iops
        match = re.search('(?:IOPS=)([^,]*)', line)
        if match:
            iops = match.group(1)
            data = [iops]
        
        # try get bw
        match = re.search('(?:BW=[^(]*[(])([\d.]*)', line)
        if match:
            bw = match.group(1)
            data.append(bw)
        
        # try get slat
        tmp = get_latency('slat', line)
        if tmp:
            data.extend(tmp)

        # try get clat
        tmp = get_latency('clat', line)
        if tmp:
            data.extend(tmp)

        # try get lat
        tmp = get_latency('lat', line)
        if tmp:
            data.extend(tmp)

        # try get percentiles     clat percentiles (nsec):
        match = re.search('(?:.*)(?:clat percentiles )([^,]*):(?:.*)', line)
        if match:
            scale = get_scale(match.group(1))
            line = next(lines)
            for percentile in percentiles:
                match = re.search(f'(?:{percentile}=[\[]\s*)([^\]]*)', line)
                if not match:
                    line = next(lines)
                    match = re.search(f'(?:{percentile}=[\[]\s*)([^\]]*)', line)

                data.append(str(float(match.group(1)) * scale))                    

                
    for i in range(len(data)):
        # Handle fio formatting
        data[i] = fix_fio_format(data[i])

        # Excel/Libre friendly formatting
        data[i] = "{}".format(round(float(data[i]),2)).replace('.', ',')

    pretty_print(data)

    # define header
    header = ['iops', 'bw','slat_min', 'slat_max', 'slat_avg', 'slat_stdev', 
                'clat_min', 'clat_max', 'clat_avg', 'clat_stdev', 
                'lat_min', 'lat_max', 'lat_avg', 'lat_stdev',
                '1,00', '5,00', '10,00', '20,00',
                 '30,00', '40,00', '50,00', '60,00',
                  '70,00', '80,00', '90,00', '95,00',
                   '99,00', '99,50', '99,90', '99,95',
                    '99,99']

    # open output file and write
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(data)

    f_in.close()
    print("Wrote to {}".format(output_file))


if __name__ == '__main__':
    main()