import argparse
from pathlib import Path

from pyulog import ULog

'''
    Processes given ulog file and saves the new ulog in the output_dir specified
    Output file name will be : "<ulog-file-name>_anonymized.ulg"
'''
def anonymize_gps_data(ulog_file : Path, output_dir : Path):
    ulog = ULog(ulog_file.absolute())
    print(ulog)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Anonymize the GPS location in the ULog')
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory you want the modified ulog to be stored')
    parser.add_argument('ulog_path', help='Path to the ulog you want to process')
    args = parser.parse_args()

    # Check if ulog path is valid
    ulog_path = Path(args.ulog_path)
    if (not ulog_path.exists()) or (ulog_path.suffix != '.ulg'):
        print('Error! {} is not a valid, existing ulog file!'.format(ulog_path))
        exit(-1)

    # Check if output directory is valid, if specified
    if args.output_dir is not None:
        output_dir = Path(args.output_dir)
        if not output_dir.is_dir():
            print('Error! {} is not a valid output dir!'.format(output_dir))
            exit(-1)
        anonymize_gps_data(ulog_path, output_dir)

    # User didn't specify output directory, default to the same directory of the ulog_path
    anonymize_gps_data(ulog_path, ulog_path.parent)