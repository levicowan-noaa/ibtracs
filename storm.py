__all__ = ['Storm']

from datetime import datetime
import json
import logging
import numpy as np
from pytoolbox.geospatial import earthdist

logger = logging.getLogger(__name__)


class Storm:
    def __init__(self, data, datatype='csv'):
        """
        Class for parsing information about a specific TC from the IBTrACS database.
        Only 6-hourly synoptic times are retained due to the prevalence of missing
        or interpolated data at non-synoptic times.

        Args:
            data:     Raw storm data (see ``datatype`` for format)

            datatype: If 'csv' (default), data is a list of lines from the IBTrACS file
                      If 'json', data is a JSON representation of parsed data
                      If 'db', data is a dict mapping column names to values from the SQL database
        """
        if datatype == 'csv':
            self._parse_csv(data)
        elif datatype == 'json':
            self._parse_json(data)
        elif datatype == 'db':
            self._parse_db(data)
        else:
            raise ValueError(f'Unrecognized input datatype: {datatype}')

    def __eq__(self, other):
        # Have to compare starting TC location too since two TCs named "NOT_NAMED"
        # could form at the same time in the same basin
        comparisons = [self.name == other.name, self.basin == other.basin,
                       self.season == other.season, np.isclose(self.lons[0], other.lons[0]),
                       np.isclose(self.lats[0], other.lats[0])]
        return all(comparisons)

    def __hash__(self):
        return hash((self.name, self.basin, self.season, self.lons[0], self.lats[0]))

    def _parse_csv(self, lines):
        """Parse a list of lines from the IBTrACS CSV file associated with a single storm"""
        # Parse time-dependent attributes
        dtypes = {
            'lats': float, 'lons': float, 'times': 'datetime64[m]', 'classifications': 'U2',
            'wind': float, 'mslp': float, 'speed': float, 'basins': 'U2',
            'subbasins': 'U2', 'agencies': 'U10'
        }
        # Initialize arrays
        for arrname, dtype in dtypes.items():
            if dtype is float:
                setattr(self, arrname, np.nan*np.empty(len(lines), dtype=dtype))
            else:
                setattr(self, arrname, np.empty(len(lines), dtype=dtype))
        # Populate arrays
        for i, line in enumerate(lines):
            fields = [field.strip() for field in line.split(',')]
            self.basins[i] = fields[3]
            self.subbasins[i] = fields[4]
            self.agencies[i] = fields[12]
            self.lats[i] = float(fields[8])
            # longitude is in degrees east
            self.lons[i] = float(fields[9])
            time = datetime.strptime(fields[6], '%Y-%m-%d %H:%M:%S')
            self.times[i] = time
            # Forward speed (km/h)
            if i > 0:
               p1 = (self.lats[i-1], self.lons[i-1])
               p2 = (self.lats[i], self.lons[i])
               dx = earthdist(p1, p2)
               # Seconds since last ob
               dt = int((self.times[i] - self.times[i-1]).item().total_seconds())
               self.speed[i] = 3600*dx/dt if dt > 0 else np.nan # km/h
            # Storm classification (see Ibtracs.possible_classifications)
            self.classifications[i] = fields[7]
            # Max wind in kt
            wind = float(fields[10] or np.nan)
            self.wind[i] = wind if wind > 0 else np.nan
            # MSLP in hPa
            mslp = float(fields[11] or np.nan)
            self.mslp[i] = mslp if mslp > 0 else np.nan

        # Exclude any track point not at a standard 6-hourly time, since such points
        # almost always have missing or interpolated information
        self.remove_nonsynoptic_times()
        # Abort if there is no data at synoptic times
        if len(self.times) == 0:
            return

        # Post-process longitudes to make sure plots work correctly.
        # If track crosses prime meridian, turn 0 longitude into 360
        # The 1st condition below can be met at either prime meridian or dateline.
        # The 2nd condition ensures we only catch the prime meridian
        # (storm crossing dateline will have max lon near 180, and it can't jump
        # 40 degrees between two track points to cross that line)
        minlon, maxlon = min(self.lons), max(self.lons)
        if minlon*maxlon <= 0 and abs(maxlon) < 140:
           self.lons = [lon+360 if lon >= 0 else lon for lon in self.lons]
        # Make sure lon is defined in [0,360] not [-180,180] to avoid problems across dateline
        self.lons = [lon+360 if lon < 0 else lon for lon in self.lons]

        # Define date/time of genesis as the first track point at which the
        # classification is not 'DS' (disturbance) or 'NR' (not rated)
        for t, c in zip(self.times, self.classifications):
            if c not in ('DS','NR'):
                self.genesis = t.item() # datetime object
                break
        # Otherwise, use the first date available
        else:
            self.genesis = self.times[0].item() # datetime object

        # Parse other time-independent attributes of the storm using the first track point.
        # This only works if non-synoptic track points have been removed first
        t0str = self.times[0].item().strftime('%Y-%m-%d %H:%M:%S')
        # Need to find first line that is a synoptic time
        for line in lines:
            fields = [field.strip() for field in line.split(',')]
            if fields[6] == t0str:
                break
        self.ID = fields[0]
        self.ATCF_ID = fields[18] or None
        self.name = fields[5]
        # Take the 'basin' as the basin in which the TC formed. A storm may cross
        # basins during its lifetime. All occupied basins are collected in self.basins
        i_genesis = np.where(self.times == self.genesis)[0][0]
        self.basin = self.basins[i_genesis]
        self.subbasin = self.subbasins[i_genesis]

        # Define the season (year) of the storm as the year in which it formed
        # if it is in the northern hemisphere. If in southern hemisphere,
        # define the tropical season as July-June, with the season being
        # the latter of the two calendar years spanned by that period.
        year, month = self.genesis.year, self.genesis.month
        if self.basin in ('SP','SI','SA'):
            self.season = year+1 if month >= 7 else year
        else:
           self.season = year

    def _parse_db(self, data):
        """
        Parse a time-ordered sequence of table rows from the database table
        describing a single TC and return a Storm object.

        Args:
            data: (dict) Mapping of column names to tuples of time-sorted column values
        """
        # Assign attributes
        self.ID = data['ID'][0]
        self.ATCF_ID = data['ATCF_ID'][0]
        self.name = data['name'][0]
        self.season = data['season'][0]
        self.basin = data['basin'][0]
        self.subbasin = data['subbasin'][0]
        gstr = data['genesis'][0]
        self.genesis = datetime.strptime(gstr, '%Y-%m-%d %H:%M:%S')
        # Array datatypes
        dtypes = {
            'lats': float, 'lons': float, 'times': 'datetime64[m]', 'classifications': 'U2',
            'wind': float, 'mslp': float, 'speed': float, 'basins': 'U2',
            'subbasins': 'U2', 'agencies': 'U10'
        }
        self.lats = np.array(data['lat'], dtype=dtypes['lats'])
        self.lons = np.array(data['lon'], dtype=dtypes['lons'])
        self.times = np.array([datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
                               for tstr in data['time']], dtype=dtypes['times'])
        self.wind = np.array(data['wind'], dtype=dtypes['wind'])
        self.mslp = np.array(data['mslp'], dtype=dtypes['mslp'])
        self.classification = np.array(data['classification'], dtype=dtypes['classifications'])
        self.speed = np.array(data['speed'], dtype=dtypes['speed'])
        self.basins = np.array(data['basin'], dtype=dtypes['basins'])
        self.subbasins = np.array(data['subbasin'], dtype=dtypes['subbasins'])
        self.agencies = np.array(data['agency'], dtype=dtypes['agencies'])

    def _parse_json(self, data):
        """Parse a JSON representation of a single storm created by Storm.to_json()"""
        data = json.loads(data)
        # Array datatypes
        dtypes = {
            'lats': float, 'lons': float, 'times': 'datetime64[m]', 'classifications': 'U2',
            'wind': float, 'mslp': float, 'speed': float, 'basins': 'U2',
            'subbasins': 'U2', 'agencies': 'U10'
        }
        # Assign attributes
        for key, values in data.items():
            # Non-array attributes
            if key in ('ID','ATCF_ID','name','basin','subbasin','season'):
                setattr(self, key, values)
            elif key == 'genesis':
                setattr(self, 'genesis', datetime.fromisoformat(values))
            # Array attributes
            elif key in dtypes:
                setattr(self, key, np.array(values, dtype=dtypes[key]))
            else:
                raise ValueError(f'Unhandled JSON storm attribute: {key}')

    def to_json(self):
        def encoder(obj):
            if type(obj) is np.ndarray:
                # If date array, have to serialize each element
                if obj.dtype.kind == 'M':
                    return [dt64.item().isoformat(timespec='minutes') for dt64 in obj]
                else:
                    return list(obj)
            elif type(obj) is datetime:
                return obj.isoformat(timespec='minutes')
            else:
                return obj.__dict__
        return json.dumps(self, default=encoder)

    def remove_nonsynoptic_times(self):
        ntimes = len(self.times)
        # Keep 00Z, 06Z, 12Z, and 18Z only
        idx_keep = [i for i, t in enumerate(self.times)
                    if t.item().hour % 6 == 0 and t.item().minute == 0]
        for attr, values in self.__dict__.items():
            # Assume arrays with same length as self.times are obs data
            if type(values) is list and len(values) == ntimes:
                setattr(self, attr, [v for i, v in enumerate(values) if i in idx_keep])
            elif type(values) is np.ndarray and values.size == ntimes:
                setattr(self, attr, values[idx_keep])
        return self

    def ACE(self, subtropical=True):
        """
        Compute the Accumulated Cyclone Energy index over the storm's lifetime
        The ACE is computed for every 6-hour standard point at which the storm
        had winds >=34 kt and was not extratropical. Subtropical points may
        optionally be excluded.

        For RSMCs that use 10-minute wind, ACE is computed using an estimate
        of the corresponding 1-minute wind.

        Args:
            subtropical: If True (default), count subtropical points in
                         the ACE calculation.
        """
        # Estimate 1-minute winds if 10-minute winds are used in this basin
        # Note that RSMC New Delhi uses 3-min winds, but there is no conversion
        if self.basin not in ('EP','NA','NI','SA'):
           wind = [v/0.88 for v in self.wind]
        else:
           wind = self.wind
        v2 = []
        for i,v in enumerate(wind):
            if subtropical:
                conditions = [v >= 34, self.classifications[i] not in ('ET',),
                              self.times[i].hour % 6 == 0, self.times[i].minute == 0]
            else:
                conditions = [v >= 34, self.classifications[i] not in ('ET','SS'),
                              self.times[i].hour % 6 == 0, self.times[i].minute == 0]
            if all(conditions):
                v2.append(v**2)
        ace = 1e-4 * np.sum(v2)
        return ace

    def intersect_box(self, coords):
        """
        Determine whether a TC passed through a lat/lon bounding box
        at any point during its lifetime. Storm positions are interpolated
        to 1-hourly, and then each position tested for inside the box.
        A position exactly on the boundary is counted as inside.

        Args:
            storm:  The Storm object
            coords: Sequence of coordinates given as [lat0, lat1, lon0, lon1]
                    defining the region to test. Lons should be given in [0,360]

        Returns:
            Boolean True if storm passed through the box, False if not.
        """
        lat0, lat1, lon0, lon1 = coords
        # Interpolate positions to 1-hourly
        hourlypos = []
        for i in range(1, len(self.times)):
            # Start with the previous known position
            hourlypos.append((self.lats[i-1], self.lons[i-1]))
            # Time difference in hours:
            dt = int((self.times[i] - self.times[i-1]).total_seconds()/3600)
            # Position change
            dlat = self.lats[i] - self.lats[i-1]
            dlon = self.lons[i] - self.lons[i-1]
            # Interpolate for each hour up until the following known position.
            for h in range(1,dt):
                ilat = self.lats[i-1] + h*(dlat/dt)
                ilon = self.lons[i-1] + h*(dlon/dt)
                hourlypos.append((ilat, ilon))

        # Determine if any hourly position was inside the bounding box
        for lat, lon in hourlypos:
            if (lat0 <= lat <= lat1) and (lon0 <= lon <= lon1):
                intersect = True
                break
        else:
            intersect = False
        return intersect
