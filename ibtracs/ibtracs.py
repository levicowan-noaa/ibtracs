__all__ = ['Ibtracs']

from .storm import Storm
import logging
import os, sys
import sqlite3

# Default working directory is the parent directory of this file (package root)
workdir = os.path.dirname(__file__)
# Setup logging
logger = logging.getLogger(__name__)
logfile = os.path.join(workdir, 'ibtracs.log')
logging.basicConfig(filename=logfile, level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
# Create custom hook for uncaught exceptions
def exc_hook(Type, value, tb):
    logger.exception(msg='', exc_info=(Type, value, tb))
sys.excepthook = exc_hook


class Ibtracs:
    ############################################################
    #                     Useful metadata                      #
    ############################################################
    possible_classifications = {
        'TS': 'Tropical', 'SS': 'Subtropical', 'ET': 'Extratropical',
        'DS': 'Distrubance', 'NR': 'Not Reported', 'MX': 'Mixture (Agencies Contradict)'
    }

    possible_basins = {
        'NA': 'North Atlantic',
        'EP': 'Eastern Pacific',
        'WP': 'Western North Pacific',
        'NI': 'North Indian',
        'SI': 'South Indian',
        'SP': 'South Pacific',
        'SA': 'South Atlantic'
    }

    possible_subbasins = {
        'CS': 'Caribbean Sea',
        'GM': 'Gulf of Mexico',
        'CP': 'Central Pacific',
        'BB': 'Bay of Bengal',
        'AS': 'Arabian Sea',
        'WA': 'Western Australia',
        'EA': 'Eastern Australia',
        'NA': 'North Atlantic',
        'MM': 'Missing'
    }

    possible_agencies = ['atcf', 'bom', 'cphc', 'hurdat_atl', 'hurdat_epa', 'nadi',
                        'newdelhi', 'reunion', 'tokyo', 'wellington']

    def __init__(self):
        self.logfile = logfile
        self.datadir = os.path.join(workdir, 'data')
        if not os.path.exists(self.datadir):
            os.makedirs(self.datadir, 0o755)
        self.db_filename = os.path.join(self.datadir, 'storms.db')
        self.db = sqlite3.connect(self.db_filename)
        self.tablename = 'storms' # SQL table name
        self.storms = [] # To hold ibtracs.storm.Storm objects

    def resolve_duplicates(self):
        """
        Resolve duplicate storms in the IBTrACS database. This is currently done by
        simply taking the storm with the longest record
        """
        # Group TCs by basin, name, and season, which together are uniquely identifying
        TCs_by_ID = {}
        for tc in self.storms:
            TCs_by_ID.setdefault((tc.basin, tc.name, tc.season), []).append(tc)
        # Find "duplicate" TCs
        duplicates_to_remove = []
        for tcID in TCs_by_ID:
            # Exclude "NOT_NAMED" since this leads to false duplicates
            TCs = [tc for tc in TCs_by_ID[tcID] if tc.name != 'NOT_NAMED']
            TCs.sort(key=lambda tc: len(tc.time), reverse=True)
            # Mark all but the TC with the longest record for removal
            duplicates_to_remove.extend(TCs[1:])
        # Remove duplicates
        self.storms = list(set(self.storms) - set(duplicates_to_remove))

    def load_from_csv(self):
        """Parse raw CSV database and create Storm objects"""
        logger.info('Parsing raw IBTrACS CSV file...')
        self.storms.clear()
        with open(os.path.join(self.datadir, 'ibtracs.csv')) as f:
            # Group lines with the same storm ID. Construct Storm objects
            # on the fly to avoid loading the entire file at once
            stormlines = []
            linenum = 0
            # Skip first two header lines
            for i in range(3):
                line = f.readline()
                linenum += 1
            oldID = None
            while True:
                print(f'Parsing line {linenum}', end='\r')
                line = line.strip()
                if len(line) == 0:
                    continue
                fields = [field.strip() for field in line.split(',')]
                ID = fields[0]
                # If ID is the same as the last line, add to this storm's set
                if ID == oldID:
                    stormlines.append(line.strip())
                # If ID is different than before, then this is a new storm
                else:
                    if stormlines:
                        tc = Storm(stormlines)
                        if len(tc.time) > 0:
                            self.storms.append(tc)
                    stormlines = [line.strip()]
                    oldID = ID
                line = f.readline()
                # End of file
                if line == '':
                    if stormlines:
                        tc = Storm(stormlines)
                        if len(tc.time) > 0:
                            self.storms.append(tc)
                    break
                linenum += 1
        print()
        self.resolve_duplicates()

    def load_from_db(self):
        """Parse SQL database and (re)construct Storm objects"""
        logger.info('Loading all TCs from database...')
        self.storms.clear()
        rows = list(self.db.execute(f'SELECT * FROM {self.tablename} ORDER BY ID,time'))
        # Group rows by TC ID
        rows_by_TC = {}
        for row in rows:
            rows_by_TC.setdefault(row[0], []).append(row)
        # Format into mapping of column names to column data
        colnames = [info[1] for info in self.db.execute(f'PRAGMA table_info("{self.tablename}")')]
        for storm_rows in rows_by_TC.values():
            values = list(zip(*storm_rows))
            data = {colname: values for colname, values in zip(colnames, values)}
            self.storms.append(Storm(data, datatype='db'))
        self.resolve_duplicates()

    def load_from_json(self):
        """Parse JSON files generated by Storm.to_json() and (re)construct Storm objects"""
        logger.info('Loading all TCs from JSON files...')
        self.storms.clear()
        for dirname, subdirs, filenames in os.walk(os.path.join(self.datadir, 'json')):
            for fname in filenames:
                print(f'Loading {fname}'+' '*20, end='\r')
                with open(os.path.join(dirname, fname)) as f:
                    data = f.read()
                self.storms.append(Storm(data, datatype='json'))
        print()
        self.resolve_duplicates()

    def load_all_storms(self, source='db'):
        """
        Load all Storm objects into self.storms

        Args:
            source: If 'db': load from SQL database generated by self.save_to_db()
                    If 'json': load from JSON files generated by self.save_to_json()
                    If 'csv': load from the raw IBTrACS CSV file
        """
        if source == 'db':
            assert os.path.exists(self.db_filename), 'database file does not exist'
            self.load_from_db()
        elif source == 'json':
            assert os.path.exists(os.path.join(workdir, 'data/json')), 'JSON files do not exist'
            self.load_from_json()
        elif source == 'csv':
            assert os.path.exists(os.path.join(self.datadir, 'ibtracs.csv'))
            self.load_from_csv()
        else:
            raise ValueError(f'Unrecognized source: {source}')
        # Sort storm list by genesis time
        self.storms.sort(key=lambda tc: tc.genesis)

    def save_to_json(self):
        """
        Save the IBTrACS database to JSON representations, organized by
        basin, year, and storm
        """
        if not self.storms:
            self.load_from_csv()
        for i, tc in enumerate(self.storms):
            print(f'Serializing storm {i+1}/{len(self.storms)}', end='\r')
            data = tc.to_json()
            savedir = os.path.join(self.datadir, f'json/{tc.basin}/{tc.season}')
            if not os.path.exists(savedir):
                os.makedirs(savedir, 0o755)
            with open(os.path.join(savedir, f'{tc.name.lower()}_{tc.ID}.json'), 'w') as f:
                f.write(data)
        print()

    def save_to_db(self):
        """
        Save all storm objects to an sqlite3 database
        """
        if not self.storms:
            logger.info('Parsing storm data...')
            self.load_all_storms(source='csv')
        c = self.db.cursor()
        # Create storm table. If it already exists, replace it.
        c.execute(f'DROP TABLE IF EXISTS {self.tablename}')
        c.execute(f"""
            CREATE TABLE {self.tablename}(
                ID CHAR(13),      ATCF_ID CHAR(8),
                name VARCHAR,     season INT,
                basin CHAR(2),    subbasin CHAR(2),
                lat FLOAT,        lon FLOAT,
                time DATETIME,    wind INT,
                mslp INT,         classification CHAR(2),
                speed FLOAT,      dist2land INT,
                genesis DATETIME, agency VARCHAR,
                rmw INT,
                R34_SE FLOAT,     R34_NE FLOAT,
                R34_SW FLOAT,     R34_NW FLOAT,
                R50_SE FLOAT,     R50_NE FLOAT,
                R50_SW FLOAT,     R50_NW FLOAT,
                R64_SE FLOAT,     R64_NE FLOAT,
                R64_SW FLOAT,     R64_NW FLOAT
        )""")
        self.db.commit()

        # Insert each track point as a row
        rows = []
        radii_attrs = [f'R{v}_{q}' for v in (34,50,64) for q in ('NE','SE','SW','NW')]
        for tc in self.storms:
            genesis = tc.genesis.strftime('%Y-%m-%d %H:%M:%S')
            for i in range(len(tc.time)):
                t = tc.time[i].item().strftime('%Y-%m-%d %H:%M:%S')
                vals = (
                    tc.ID, tc.ATCF_ID, tc.name, tc.season, tc.basins[i], tc.subbasins[i],
                    tc.lat[i], tc.lon[i], t, tc.wind[i], tc.mslp[i],
                    tc.classification[i], tc.speed[i], tc.dist2land[i], genesis, tc.agencies[i], tc.rmw[i]
                )
                # Wind radii values
                rvals = tuple(getattr(tc, attr)[i] for attr in radii_attrs)
                row = vals + rvals
                rows.append(row)
        logger.info(f'Inserting {len(rows)} rows into database...')
        c.executemany(f'INSERT INTO {self.tablename} VALUES ({",".join("?"*len(rows[0]))})', rows)
        self.db.commit()

    def get_storm_from_name(self, name, season, basin):
        """
        Fetch a TC from the SQL database based on its name, season, and basin
        and construct a Storm object. Note that this cannot work for storms
        with name="NOT_NAMED".
        """
        rows = list(self.db.execute(f'SELECT * FROM {self.tablename} WHERE name = "{name.upper()}" AND season = {season} AND basin = "{basin}" ORDER BY time'))
        if not rows:
            raise ValueError(f'Storm not found in database: name={name}, season={season}, basin={basin}')
        colnames = [info[1] for info in self.db.execute(f'PRAGMA table_info("{self.tablename}")')]
        values = list(zip(*rows))
        data = {colname: values for colname, values in zip(colnames, values)}
        return Storm(data, datatype='db')

    def get_storm_from_atcfid(self, ATCF_ID):
        """
        Fetch a TC from the SQL database based on its ATCF ID and construct
        a Storm object. Note that some TCs may not have an ATCF ID in the
        database.
        """
        rows = list(self.db.execute(f'SELECT * FROM {self.tablename} WHERE ATCF_ID = "{ATCF_ID}" ORDER BY time'))
        if not rows:
            raise ValueError(f'ATCF ID not found in database: {ATCF_ID}')
        colnames = [info[1] for info in self.db.execute(f'PRAGMA table_info("{self.tablename}")')]
        values = list(zip(*rows))
        data = {colname: values for colname, values in zip(colnames, values)}
        return Storm(data, datatype='db')
