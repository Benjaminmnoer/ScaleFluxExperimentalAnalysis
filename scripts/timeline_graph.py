# Input: log file
# Input file format: Id, time(msec), Bandwidth(KiB/sec), direction, blocksize(bytes)
# Output: graph of results

# import modules
import sys
import os
import re
import matplotlib.pyplot as plt
import pandas as pd

# define constants
metrics: dict = {
    'bw': 'Bandwidth(MB/s)',
    'iops': 'IOPS',
    'lat': 'Latency(msec)',
    'clat': 'Completion Latency(msec)',
    'slat': 'Submission Latency(msec)',
    'dlat': 'Device Latency(msec)',
}

# define functions
def get_metric(log):
    """
    Get metric from log file
    """
    return re.findall(r'(?<=_).*?(?![^.])', log)[0]


def get_job(log):
    """
    Get job from log file
    """
    return re.findall(r'[ \w-]+?(?=\_)', log)[0]



def generate_graph(log, metric, x_label, y_label, title):
    """
    Get data from log file
    """
    # data format: time, bandwidth, direction, blocksize
    
    # get dataframe from csv
    df = pd.read_csv(log, sep=',', header=None, names=['time', metric, 'direction', 'blocksize', 'fisk'], iterator=False, chunksize=1_000_000)

    i = 0
    for data_chunk in df:
        data_chunk = data_chunk[['time', metric]].astype(float)
        # if (metric == 'Bandwidth(MB/sec)'):
        #     data_chunk[metric] = data_chunk[metric].apply(lambda x: x / 977) # KiB to MB conversion.
    
        if ("Lat" in metric):
            data_chunk[metric] = data_chunk[metric].apply(lambda x: x / 1000000) # ns to ms

        data_chunk['time'] = data_chunk['time'].apply(lambda x: x / 1000) # ms to s

        data_chunk.set_index('time', inplace=True)
        
        plt.plot(data_chunk.index, data_chunk[metric], linewidth=1, color="C0")

        i += 1
    
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    return df
    
def main():
    """
    Main function
    """
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python timeline_graph.py path/to/experiment/file.log path/to/experiment/output/directory")
        exit(0)

    # get log file data
    log_path = sys.argv[1]
    log_filename = os.path.basename(log_path)
    job_name = get_job(log_filename)
    metric = metrics[get_metric(log_filename)]

    if len(sys.argv) == 4:
        plt.ylim(top=float(sys.argv[3]))
    
    # generate/save graph
    generate_graph(log_path, metric, 'Time(s)', metric, job_name)
    output_dir = sys.argv[2]

    plt.rcParams['svg.fonttype'] = 'none' # Save text as text not path
    plt.savefig(f'{output_dir}{log_filename}.svg')
    plt.show()

# run main function
if __name__ == '__main__':
    main()