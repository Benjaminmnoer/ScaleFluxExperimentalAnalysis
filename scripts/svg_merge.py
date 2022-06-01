# Input: 2..n svg files
# Output: 1 merged svg file
# Join svg files horizontally

import sys
import os
import re
import argparse
import xml.etree.ElementTree as ET

def main():
    parser = argparse.ArgumentParser(description='Join svg files horizontally')
    parser.add_argument('files', nargs='+', help='svg files to join')
    parser.add_argument('-o', '--output', help='output file')
    args = parser.parse_args()
    files = args.files

    if len(files) < 2:
        print('Please specify at least 2 files')
        sys.exit(1)

    if args.output:
        output_file = args.output
    else:
        output_file = "merged.svg"

    # Check if files exist
    for file in files:
        if not os.path.isfile(file):
            print('File ' + file + ' does not exist')
            sys.exit(1)

    # Read files
    svg = ET.Element('svg')
    for file in files:
        tree = ET.parse(file)
        svg.append(tree.getroot())

    # Write output
    tree = ET.ElementTree(svg)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    

if __name__ == '__main__':
    main()