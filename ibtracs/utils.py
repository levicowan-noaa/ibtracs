#!/usr/bin/env python3

import os, sys
from ibtracs import Ibtracs
import numpy as np
from urllib.request import urlopen


def earthdist(p1, p2):
    """
    Calculate the great circle distance between two points on the Earth's surface.

    Args:
         p1 and p2 are tuples given as (lat,lon) pairs in degrees.
         lat and lon may be numbers or arrays of multiple points.

    Returns:
         The distance between the two points in km. If lat and lon
         are arrays, the return value is an array of the same length
         containing the distances between each pair of points.
    """
    # Mean radius of the Earth in km
    R = 6371
    # Given coordinates in radians
    lat1, lon1 = np.radians(p1[0]), np.radians(p1[1])
    lat2, lon2 = np.radians(p2[0]), np.radians(p2[1])
    # Compute distance
    arg = np.sin(lat1)*np.sin(lat2) + np.cos(lat1)*np.cos(lat2)*np.cos(np.abs(lon2-lon1))
    # Floating-point error may result in a slightly out-of-bounds
    # argument for arccos (domain -1 to +1). Round all incorrect arguments
    if type(arg) is np.ndarray:
        arg[arg > 1] = 1
        arg[arg < -1] = -1
    else:
        if arg > 1:
            arg = 1
        elif arg < -1:
            arg = -1
    central_angle = np.arccos(arg)
    d = R*central_angle
    return d


def download_data():
    """Setup data directory, download raw IBTrACS CSV file, and generate database"""
    I = Ibtracs()
    # Download raw CSV file from NCEI if it doesn't exist
    url = ('https://www.ncei.noaa.gov/data/'
           'international-best-track-archive-for-climate-stewardship-ibtracs/'
           'v04r00/access/csv/ibtracs.ALL.list.v04r00.csv')
    filename = os.path.join(I.datadir, 'ibtracs.csv')
    def progressbar(progress):
        print("\tProgress: [{0:50s}] {1:.1f}% ".format('#'*int(progress*50), progress*100), end='\r')
    if not os.path.exists(filename):
        with urlopen(url) as rf:
            with open(filename, 'w') as lf:
                size = int(rf.getheader('Content-length'))
                retrieved = 0
                chunksize = 1024
                print(f'Downloading raw IBTrACS CSV file from NCEI ({size/(1024*1024):.1f} MB)...')
                while True:
                    chunk = rf.read(chunksize)
                    if not chunk:
                        break
                    retrieved += len(chunk)
                    lf.write(chunk.decode('utf-8'))
                    progressbar(retrieved/size)
                print()
    # Create database
    I.load_all_storms(source='csv')
    I.save_to_db()
