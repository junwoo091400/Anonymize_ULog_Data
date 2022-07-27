import argparse
from pathlib import Path
from numpy import integer

from pyulog import ULog

'''
Processes given ulog file and saves the new ulog in the output_dir specified
Output file name will be : "<ulog-file-name>_anonymized.ulg"
'''

# <<USER SETTING>>
# GPS coordinates will be shifted so that initial arming point (home-position)
# will equal to this latitude / longitude point
GPS_ANONYMIZE_LAT = 0
GPS_ANONYMIZE_LON = 0

# ------------------------------------------------------------------- #
# GLOBAL FLAG
verbose = False

# This flag will be set to True once we find a valid GPS data, then the
# Necessary GPS offset value will be calculated
FOUND_FIRST_GPS_DATA = False
GPS_ANONYMIZE_LAT_OFFSET = 0.
GPS_ANONYMIZE_LON_OFFSET = 0.

"""
Return single pair of anonymized GPS location (lat, lon) in degrees
"""
def anonymize_gps_lat_lon(lat, lon):
    global FOUND_FIRST_GPS_DATA, GPS_ANONYMIZE_LAT_OFFSET, GPS_ANONYMIZE_LON_OFFSET
    global GPS_ANONYMIZE_LAT, GPS_ANONYMIZE_LON

    # Automatically calculate offset with the first data supplied
    # The offset when added, maps raw data into anonymized data.
    if not FOUND_FIRST_GPS_DATA:
        GPS_ANONYMIZE_LAT_OFFSET = GPS_ANONYMIZE_LAT - lat
        GPS_ANONYMIZE_LON_OFFSET = GPS_ANONYMIZE_LON - lon
        FOUND_FIRST_GPS_DATA = True
    
    return (lat + GPS_ANONYMIZE_LAT_OFFSET, lon + GPS_ANONYMIZE_LON_OFFSET)


"""
Take in two list of latitudes / longitudes each, and return the anonymized lists in the same foramt.

Input : [list(latitudes), list(longitudes)]
Output : [list(latitudes), list(longitudes)]
"""
def anonymize_gps_lat_lon_list(lat_list: list, lon_list: list):
    if len(lat_list) != len(lon_list):
        print('Length of lat / lon array supplied does not match! {} : {}'.format(len(lat_list), len(lon_list)))
        raise Exception
    
    new_lat = []
    new_lon = []

    for (lat, lon) in zip(lat_list, lon_list):
        if verbose: print('Pre lat/lon :', lat, lon)
        lat, lon = anonymize_gps_lat_lon(lat, lon)
        if verbose: print('Post lat/lon :', lat, lon)
        new_lat.append(lat)
        new_lon.append(lon)

    return (new_lat, new_lon)

"""
Return the index of the data in ULog object matching the name and instance index

Example:
# Get 'sensor_gyro1' topic's index
gyro_data_index = get_topic_index(ulog, 'sensor_gyro', 1)
gyro_data = ulog._data_list[gyro_data_index]
"""
def get_topic_index(ulog_obj, name, multi_instance=0):
    for idx in range(len(ulog_obj._data_list)):
        if (ulog_obj._data_list[idx].name == name
             and ulog_obj._data_list[idx].multi_id == multi_instance):
             if verbose: print(idx, 'found as index for', name, multi_instance)
             return idx
    
    # Didn't find the index, raise exception
    raise Exception


"""
Anonymize all the instances of the specified topic (by name)

@param integer_unit : If True, lat/lon is in 1E-7 degrees unit in integer, so modify accordingly
"""
LAT_LON_INTEGER_MULTIPLIER = 1E7

def anonymize_topic_gps(ulog_obj, topic_name, lat_name='lat', lon_name='lon', integer_unit = False):
    # Go through all the multi instances to anonymize all of them.
    multi_idx = 0
    while True:
        try:
            '''
            ULog dataset (e.g. ulog._data_list[0]) has the following structure:
            - data (dictionary) {
                'timestamp' : [ts1, ts2, ... ],
                'lat' : [lat1, lat2, ... ],
                'lon' : {lon1, lon2, ... ]}
            - multi_id
            - timestamp_idx : Index of the timestamp?!

            To modify each dataset, we need to access the internal _data_list member of ULog object,
            and find the instance index ourselves.
            '''
            topic_idx = get_topic_index(ulog_obj, topic_name, multi_idx)
        except:
            # We couldn't find the multi instance of this topic, so we don't have any more instances to anonymize
            return

        try:
            home_position_data = ulog_obj._data_list[topic_idx]
            lat_list = home_position_data.data[lat_name]
            lon_list = home_position_data.data[lon_name]

            if integer_unit:
                lat_list = [lat / LAT_LON_INTEGER_MULTIPLIER for lat in lat_list]
                lon_list = [lon / LAT_LON_INTEGER_MULTIPLIER for lon in lon_list]
            
            # Anonymize data
            lat_list, lon_list = anonymize_gps_lat_lon_list(lat_list, lon_list)

            # Convert the floating point data back to integer type if the unit is integer
            if integer_unit:
                lat_list = [int(lat * LAT_LON_INTEGER_MULTIPLIER) for lat in lat_list]
                lon_list = [int(lon * LAT_LON_INTEGER_MULTIPLIER) for lon in lon_list]

            ulog_obj._data_list[topic_idx].data[lat_name] = lat_list
            ulog_obj._data_list[topic_idx].data[lon_name] = lon_list
            print('{} instance {} anonymized!'.format(topic_name, multi_idx))
        except:
            print('Error while modifying {} instance {}!'.format(topic_name, multi_idx))
            return
        
        multi_idx += 1

"""
Anonymize the ULog object's content and output the anonymized file
"""
def anonymize_ulog_gps(ulog_file : Path, output_dir : Path):
    # absolute() returns PosixPath() object for example, which isn't processable by pyulog. Change it to string object.
    print('Reading the ULog ...')
    ulog = ULog(str(ulog_file.absolute()))

    anonymize_topic_gps(ulog, 'home_position')

    anonymize_topic_gps(ulog, 'vehicle_local_position', 'ref_lat', 'ref_lon')
    anonymize_topic_gps(ulog, 'estimator_local_position', 'ref_lat', 'ref_lon')

    anonymize_topic_gps(ulog, 'estimator_global_position')
    anonymize_topic_gps(ulog, 'vehicle_global_position')

    # These two topics have lat / lon in integer form (1E-7 degrees).
    anonymize_topic_gps(ulog, 'vehicle_gps_position', integer_unit=True)
    anonymize_topic_gps(ulog, 'sensor_gps', integer_unit=True)

    print('Writing anonymized ULog ...')
    output_file_name = ulog_file.name + '_anonymized' + ulog_file.suffix
    ulog.write_ulog(Path.joinpath(output_dir, output_file_name))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Anonymize the GPS location in the ULog')
    parser.add_argument('-o', '--output_dir', dest='output_dir', help='Output directory you want the modified ulog to be stored')
    parser.add_argument('-v', '--verbose', dest='verbose')
    parser.add_argument('ulog_path', help='Path to the ulog you want to process')
    args = parser.parse_args()

    if args.verbose is not None:
        vebose = True

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
        anonymize_ulog_gps(ulog_path, output_dir)
    else:
        # User didn't specify output directory, default to the same directory of the ulog_path
        anonymize_ulog_gps(ulog_path, ulog_path.parent)