#!/usr/bin/env python3

import numpy as np


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
