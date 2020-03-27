#!/usr/bin/env python3

"""
Setup data directory, download raw IBTrACS CSV file, and generate database
"""

import os
# Avoid relative import problem during install
os.chdir(os.environ['HOME'])
from ibtracs import Ibtracs
from urllib.request import urlopen


I = Ibtracs()

# Download raw CSV file from NCEI
url = ('https://www.ncei.noaa.gov/data/'
        'international-best-track-archive-for-climate-stewardship-ibtracs/'
        'v04r00/access/csv/ibtracs.ALL.list.v04r00.csv')
filename = os.path.join(I.datadir, 'ibtracs.csv')
def progressbar(progress):
    print("\tProgress: [{0:50s}] {1:.1f}% ".format('#'*int(progress*50), progress*100), end='\r')
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

# Create database
I.load_all_storms(source='csv')
I.save_to_db()
