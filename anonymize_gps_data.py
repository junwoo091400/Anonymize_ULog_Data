import argparse
from pathlib import Path
import numpy as np
from pyulog import ULog

'''
Processes given ulog file and saves the new ulog in the output_dir specified
Output file name will be : "<ulog-file-name>_anonymized.ulg"
'''

# [deg] GPS Lat / Lon Anonymize addition values (pseudo-random)
GPS_ANONYMIZE_LAT = np.random.uniform(-90, 90)
GPS_ANONYMIZE_LON = np.random.uniform(-180, 180)

# ------------------------------------------------------------------- #
# GLOBAL FLAG
verbose = False

if verbose:
    print('Anonymize GPS Offset Lat / Lon :', GPS_ANONYMIZE_LAT, GPS_ANONYMIZE_LON)

"""
Return single pair of anonymized GPS location (lat, lon) in degrees
"""
def anonymize_gps_lat_lon(lat, lon):
    global GPS_ANONYMIZE_LAT_OFFSET, GPS_ANONYMIZE_LON_OFFSET

    new_lat = lat + GPS_ANONYMIZE_LAT
    new_lon = lon + GPS_ANONYMIZE_LON

    # Wrap the angles to be in range lat [-90, 90], lon [-180, 180]
    if new_lat > 90.0:
        new_lat -= 180.0
    elif new_lat < -90.0:
        new_lat += 180.0

    if new_lon > 180.0:
        new_lon -= 360.0
    elif new_lon < -180.0:
        new_lon += 360.0

    # Data can be either NAN or must be in range
    assert (new_lat >= -90.0 and new_lat <= 90.0) or np.isnan(new_lat), 'Latitude out of range! {}'.format(new_lat)
    assert (new_lon >= -180.0 and new_lon <= 180.0) or np.isnan(new_lon), 'Longitude out of range! {}'.format(new_lon)

    return (new_lat, new_lon)

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
        lat, lon = anonymize_gps_lat_lon(lat, lon)
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

            if verbose:
                print('Lat list:', lat_list)
                print('Lon list:', lon_list)
                print('Length:', len(lat_list))
                field_data = ulog_obj._data_list[topic_idx].field_data
                for field in field_data:
                    if field.field_name == lat_name or field.field_name == lon_name:
                        print('Field {} : {}'.format(field.field_name, field.type_str))
                        print('Field encoding: {}'.format(ulog_obj._UNPACK_TYPES[field.type_str]))
            
            # Convert the floating point data back to integer type if the unit is integer
            if integer_unit:
                lat_list = [int(lat * LAT_LON_INTEGER_MULTIPLIER) for lat in lat_list]
                lon_list = [int(lon * LAT_LON_INTEGER_MULTIPLIER) for lon in lon_list]

            ulog_obj._data_list[topic_idx].data[lat_name] = lat_list
            ulog_obj._data_list[topic_idx].data[lon_name] = lon_list
            
            print('{} instance {} anonymized!'.format(topic_name, multi_idx))

        except Exception as error:
            print('Error while modifying {} instance {}!'.format(topic_name, multi_idx))
            print(error)
            return
        
        multi_idx += 1

"""
Anonymize the ULog object's content and output the anonymized file
"""
def anonymize_ulog_gps(ulog_file : Path, output_dir : Path):
    # absolute() returns PosixPath() object for example, which isn't processable by pyulog. Change it to string object.
    print('Reading the ULog ...')
    ulog = ULog(str(ulog_file.absolute()))

    ## Anonymize GPS lat/lon data
    anonymize_topic_gps(ulog, 'home_position')

    anonymize_topic_gps(ulog, 'vehicle_local_position', 'ref_lat', 'ref_lon')
    anonymize_topic_gps(ulog, 'estimator_local_position', 'ref_lat', 'ref_lon')

    anonymize_topic_gps(ulog, 'estimator_global_position')
    anonymize_topic_gps(ulog, 'vehicle_global_position')

    # These two topics have lat / lon in integer form (1E-7 degrees).
    anonymize_topic_gps(ulog, 'vehicle_gps_position', integer_unit=True)
    anonymize_topic_gps(ulog, 'sensor_gps', integer_unit=True)

    ## Add the Information message with the 'postprocessing.anonymized' flag
    print('Adding anonymized information message ...')
    ANONYMIZED_INFORMATION_KEY = 'postprocessing.anonymized'
    ANONYMIZED_INFORMATION_VALUE = True
    ANONYMIZED_INFORMATION_UNIT_TYPE = 'bool'
    ulog._msg_info_dict[ANONYMIZED_INFORMATION_KEY] = ANONYMIZED_INFORMATION_VALUE
    ulog._msg_info_dict_types[ANONYMIZED_INFORMATION_KEY] = ANONYMIZED_INFORMATION_UNIT_TYPE

    print('Writing anonymized ULog ...')
    output_file_name = ulog_file.name[:-len(ulog_file.suffix)] + '_anonymized' + ulog_file.suffix
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