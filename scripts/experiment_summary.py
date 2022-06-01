# Input: Results folder with csv files or subfolders + output file
# Read csv files and create a summary file

import argparse
import os
import sys
import re

#from more_itertools import side_effect

def summarize_experiment(input_folder, output_file):
    # Print folder basename
    # print('Summarizing {}'.format(os.path.basename(input_folder)))

    # Open output file
    with open(output_file, 'w', newline='') as f:
        print('Writing to {}'.format(output_file))
        f.write(",iops,bw,slat_min,slat_max,slat_avg,slat_stdev,clat_min,clat_max,clat_avg,clat_stdev,lat_min,lat_max,lat_avg,lat_stdev,\"1,00\",\"5,00\",\"10,00\",\"20,00\",\"30,00\",\"40,00\",\"50,00\",\"60,00\",\"70,00\",\"80,00\",\"90,00\",\"95,00\",\"99,00\",\"99,50\",\"99,90\",\"99,95\",\"99,99\"" + "\n")
        # Get subdirectories excluding self
        subdirs = [x[0] for x in os.walk(input_folder)]
        # print(subdirs)
        # For each subdirectory add results to summary file
        for subfolder in subdirs:
            # Get all csv files in folder
            csv_files = [os.path.join(input_folder, subfolder, file) for file in os.listdir(os.path.join(input_folder, subfolder)) if file.endswith('.csv') and 'summary' not in file]

            if len(csv_files) == 0:
                continue

            # Get subdirectory name
            subdir_name = os.path.basename(subfolder)
            f.write(subdir_name + '\n')

            # For each csv file add results to summary file
            for csv_file in csv_files:
                if 'ebpf' in csv_file:
                    continue

                print(csv_file)
                # Get pattern name with regex (read|randread|write|randwrite)
                pattern_name = re.search('(read|randread|write|randwrite)', csv_file).group(1)

                with open(csv_file, 'r') as f_in:
                    lines = f_in.readlines()[1:]
                    for line in lines:
                        f.write(pattern_name + "," + line)
                        # print(line)
            
            f.write('\n')
        f.close()

def main():
    parser = argparse.ArgumentParser(description='Convert csv files to libreoffice sheet')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input folder with csv files')
    parser.add_argument('-m', '--multiple', action='store_true', help='Summarize all subfolders')
    args = parser.parse_args()

    # Get input folder
    input_folder = args.input
    if not os.path.isdir(input_folder):
        print('Input folder does not exist')
        sys.exit(1)

    # Get output file
    if args.multiple:
        # summary_experiment for each subfolder
        for subfolder in [x[0] for x in os.walk(input_folder) if x[0] != input_folder]:
            print(subfolder)
            if 'rocksdb' in subfolder:        
                continue
            summarize_experiment(os.path.join(input_folder, subfolder), os.path.join(input_folder, subfolder + '-summary.csv'))
    else:
        output_file = input_folder + '/summary.csv'
        summarize_experiment(input_folder, output_file)


if __name__ == '__main__':
    main()