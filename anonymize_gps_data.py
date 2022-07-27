import argparse
from pathlib import Path

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

# This flag will be set to True once we find a valid GPS data, then the
# Necessary GPS offset value will be calculated
FOUND_FIRST_GPS_DATA = False
GPS_ANONYMIZE_LAT_OFFSET = 0.
GPS_ANONYMIZE_LON_OFFSET = 0.

def anonymize_gps_lat_lon(lat, lon):
    """
    Return: anonymized GPS location (lat, lon) in degrees
    """
    global FOUND_FIRST_GPS_DATA, GPS_ANONYMIZE_LAT_OFFSET, GPS_ANONYMIZE_LON_OFFSET
    global GPS_ANONYMIZE_LAT, GPS_ANONYMIZE_LON

    # Automatically calculate offset with the first data supplied
    # The offset when added, maps raw data into anonymized data.
    if not FOUND_FIRST_GPS_DATA:
        GPS_ANONYMIZE_LAT_OFFSET = GPS_ANONYMIZE_LAT - lat
        GPS_ANONYMIZE_LON_OFFSET = GPS_ANONYMIZE_LON - lon
        FOUND_FIRST_GPS_DATA = True
    
    return (lat + GPS_ANONYMIZE_LAT_OFFSET, lon + GPS_ANONYMIZE_LON_OFFSET)

def anonymize_gps_lat_lon_list(lat_list: list, lon_list: list):
    """
    Take in two list of lattitudes / longitutdes each, and return the anonymized lists in the same foramt.
    
    Input : [list(lattitudes), list(longitutdes)]
    Output : [list(lattitudes), list(longitutdes)]
    """
    if len(lat_list) != len(lon_list):
        print('Length of lat / lon array supplied does not match! {} : {}'.format(len(lat_list), len(lon_list)))
        raise Exception
    
    new_lat = []
    new_lon = []

    for (lat, lon) in zip(lat_list, lon_list):
        print('Pre lat/lon :', lat, lon)
        lat, lon = anonymize_gps_lat_lon(lat, lon)
        print('Post lat/lon :', lat, lon)
        new_lat.append(lat)
        new_lon.append(lon)

    return (new_lat, new_lon)

def get_topic_index(ulog_obj, name, multi_instance=0):
    """
    This is almost the same as 'get_dataset' function in ULog. However,
    it returns the index of the topic, not the topic's dataset itself.

    Example:
    gyro_data_index = get_topic_index(ulog, 'sensor_gyro', 1)
    > This would return sensor_gyro instance 1's dataset index, which can be used like this:
    
    gyro_dataset = ulog._data_list[gyro_data_index]
    """
    for idx in range(len(ulog_obj._data_list)):
        if (ulog_obj._data_list[idx].name == name
             and ulog_obj._data_list[idx].multi_id == multi_instance):
             return idx
    
    # Didn't find the index, raise exception
    return Exception

def anonymize_topic_gps(ulog_obj, topic_name):
    """
    Anonymizes the ULog content of the GPS data of topic with a given name (including it's multi instances)
    """


def anonymize_ulog_gps(ulog_file : Path, output_dir : Path):
    # absolute() returns PosixPath() object for example, which isn't processable by pyulog. Change it to string object.
    ulog = ULog(str(ulog_file.absolute()))

    '''
    ULog dataset has the following structure:
    - data (dictionary) {
        'timestamp' : [ts1, ts2, ... ],
        'lat' : [lat1, lat2, ... ],
        'lon' : {lon1, lon2, ... ]}
    - multi_id
    - timestamp_idx : Index of the timestamp?!

    To modify each dataset, we need to access the internal _data_list member of ULog object,
    and find the instance index ourselves.
    '''
    # 'home_position'
    try:
        topic_idx = get_topic_index(ulog, 'home_position')
        home_position_data = ulog._data_list[topic_idx]
        lat_list = home_position_data.data['lat']
        lon_list = home_position_data.data['lon']
        # Anonymize data
        lat_list, lon_list = anonymize_gps_lat_lon_list(lat_list, lon_list)
        ulog._data_list[topic_idx].data['lat'] = lat_list
        ulog._data_list[topic_idx].data['lon'] = lon_list
        print('home_position GPS offset applied!')
    except:
        print('Error while modifying home_position!')
    
    # 'vehicle_local_position'
    try:
        topic_idx = get_topic_index(ulog, 'vehicle_local_position')
        vehicle_local_position_data = ulog._data_list[topic_idx]
        lat_list = vehicle_local_position_data.data['ref_lat']
        lon_list = vehicle_local_position_data.data['ref_lon']
        # Anonymize data
        lat_list, lon_list = anonymize_gps_lat_lon_list(lat_list, lon_list)
        ulog._data_list[topic_idx].data['ref_lat'] = lat_list
        ulog._data_list[topic_idx].data['ref_lon'] = lon_list
        print('vehicle_local_position GPS offset applied!')
    except:
        print('Error while modifying vehicle_local_position!')
    
    # 'estimator_local_position'
    # 'estimator_global_position'
    # 'vehicle_global_position'
    # 'vehicle_gps_position'
    # 'sensor_gps'

    # Write ULog to the new file
    output_file_name = ulog_file.name + '_anonymized' + ulog_file.suffix
    ulog.write_ulog(Path.joinpath(output_dir, output_file_name))

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
        anonymize_ulog_gps(ulog_path, output_dir)

    # User didn't specify output directory, default to the same directory of the ulog_path
    anonymize_ulog_gps(ulog_path, ulog_path.parent)