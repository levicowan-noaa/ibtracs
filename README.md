# Python IBTrACS API

A Python interface to the IBTrACS tropical cyclone best track dataset. Only 6-hourly synoptic times are included. The WMO-sanctioned agency is used for each basin. Note that for the Atlantic and eastern Pacific, this data is the same as HURDAT.

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

This will download the IBTrACS v4r00 CSV file from NCEI (URL will need updating when new dataset versions get released). The file will then get parsed, and an SQLite database will be created. This database is ~44MB in size, compared to the ~297MB CSV file, and much faster to read/parse.

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
> dict_keys(['ID', 'ATCF_ID', 'name', 'season', 'basin', 'subbasin', 'genesis', 'lats', 'lons', 'times', 'wind', 'mslp', 'classifications', 'speed', 'basins', 'subbasins', 'agencies', 'R34_NE', 'R34_SE', 'R34_SW', 'R34_NW', 'R50_NE', 'R50_SE', 'R50_SW', 'R50_NW', 'R64_NE', 'R64_SE', 'R64_SW', 'R64_NW'])
```

### View units and description of TC attributes
```
print(tc.metadata)
> {'lats': {'units': 'degrees', 'description': 'TC latitude'},
>  'classifications': {'units': None, 'description': 'storm classification (see Ibtracs.possible_classifications)'},
> ...
```

### Load TCs in bulk for filtering, etc. (populates I.storms with all Storm objects)
```
I.load_all_storms()
```

### Select all North Atlantic TCs from the 2005 season passing through the box 20-30N, 80-100W
```
TCs = [tc for tc in I.storms if tc.basin == 'NA' and tc.season == 2005
       and tc.intersect_box((20, 30, 260, 280))]
```

### Sort by genesis time and print some info
```
TCs.sort(key=lambda tc: tc.genesis)
for tc in TCs:
    ace = tc.ACE(subtropical=True)
    print(f'{tc.name}, genesis={tc.genesis}, ACE={ace:.1f}')
> ARLENE, genesis=2005-06-08 18:00:00, ACE=2.6
> BRET, genesis=2005-06-28 18:00:00, ACE=0.4
> CINDY, genesis=2005-07-03 18:00:00, ACE=1.5
> DENNIS, genesis=2005-07-04 18:00:00, ACE=18.8
> EMILY, genesis=2005-07-11 00:00:00, ACE=32.9
> ...
```

### Or use the SQLite database directly! Each track point is a row in the "storm" table
```
query = 'SELECT DISTINCT name,genesis FROM storms WHERE season=2005 AND basin="NA" AND lat>20 AND lat<30 AND lon>260 AND lon<280 ORDER BY genesis'
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
