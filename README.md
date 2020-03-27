# Python IBTrACS API

A Python interface to the IBTrACS tropical cyclone best track dataset.

## Dependencies
- Numpy >= 1.7
- Python >= 3.6

## Installation

Ensure your desired Python environment is activated, then:
```
git clone https:/www.github.com/levicowan/ibtracs /tmp/ibtracs
cd /tmp/ibtracs
python setup.py install
```

This will download the IBTrACS v4r00 CSV file from NCEI (URL will need updating when new dataset versions get released). The file will then get parsed, and an SQlite database will be created. This database is ~44MB in size, compared to the ~297MB CSV file, and much faster to read/parse.

## Usage in a Python script or interactive interpreter

```
from ibtracs import Ibtracs
I = Ibtracs()
```

### Load a single TC from the SQL database into a Storm object
```
tc = I.get_storm(name='katrina', season=2005, basin='NA')
```

### View some data from the TC:
```
for t, vmax in zip(tc.times, tc.wind):
    print(t, vmax)
> 2011-08-21T00:00 45.0
> 2011-08-21T06:00 45.0
> 2011-08-21T12:00 45.0
> 2011-08-21T18:00 50.0
> 2011-08-22T00:00 60.0
> 2011-08-22T06:00 65.0
> ...
```

### See all attributes and data variables available from the Storm object (using tc.{varname})
```
print(vars(tc).keys())
> dict_keys(['ID', 'ATCF_ID', 'name', 'season', 'basin', 'subbasin', 'genesis', 'lats', 'lons', 'times', 'wind', 'mslp', 'classification', 'speed', 'basins', 'subbasins', 'agencies'])
```

### Load TCs in bulk for filtering, etc. (populates I.storms with Storm objects)
```
I.load_all_storms()
```

### Select all North Atlantic TCs from the 2005 season
```
TCs = [tc for tc in I.storms if tc.basin == 'NA' and tc.season == 2005]
```

### Sort by genesis time and print some info
```
TCs.sort(key=lambda tc: tc.genesis)
for tc in TCs:
    print(tc.name, tc.genesis)
> ARLENE 2005-06-08 18:00:00
> BRET 2005-06-28 18:00:00
> CINDY 2005-07-03 18:00:00
> DENNIS 2005-07-04 18:00:00
> EMILY 2005-07-11 00:00:00
> ...
```

### Or use the SQLite database directly! Each track point is a row in the "storm" table
```
query = 'SELECT DISTINCT name,genesis FROM storms WHERE season=2005 AND basin="NA" ORDER BY genesis'
for row in I.db.execute(query):
    print(row)
> ('ARLENE', '2005-06-08 18:00:00')
> ('BRET', '2005-06-28 18:00:00')
> ('CINDY', '2005-07-03 18:00:00')
> ('DENNIS', '2005-07-04 18:00:00')
> ('EMILY', '2005-07-11 00:00:00')
> ...
```

### The IBTrACS database can also be written out into JSON files, stored in {I.datadir}/json.
These can be easily read by javascript in web applications, and provide a readable serialization format for the TC objects.
```
I.save_to_json()
```

### TCs can also be read in from the JSON files if they've been generated
```
I.load_all_storms(source='json')
```

### If you need to remake the SQL database or re-parse the CSV file for any reason
```
I.load_all_storms(source='csv')
I.save_to_db()
```

### If you ever want to read/modify/replace the data files directly
```
print(I.datadir)
# Will be something similar to this
> ${workdir}/anaconda3/envs/${envname}/lib/python3.7/site-packages/ibtracs/data
```

### View all attributes and methods available on the Ibtracs object (I)
```
print([a for a in dir(I) if not a.startswith('_')])
> ['datadir', 'db', 'db_filename', 'get_storm', 'load_all_storms', 'load_from_csv', 'load_from_db', 'load_from_json', 'possible_agencies', 'possible_basins', 'possible_classifications', 'possible_subbasins', 'resolve_duplicates', 'save_to_db', 'save_to_json', 'seasonACE', 'storms', 'tablename']
```

### Get log file path
```
print(I.logfile)
```
