#!/usr/bin/env python3

from distutils.core import setup
from distutils.command.install import install
import os
from urllib.request import urlopen


class Install(install):
    def run(self):
        install.run(self)
        self.post_install()

    def post_install(self):
        """Download raw IBTrACS CSV file and set up data directory"""
        datadir = os.path.join(self.install_lib, 'ibtracs/data')
        if not os.path.exists(datadir):
            os.makedirs(datadir, 0o755)
        url = ('https://www.ncei.noaa.gov/data/'
               'international-best-track-archive-for-climate-stewardship-ibtracs/'
               'v04r00/access/csv/ibtracs.ALL.list.v04r00.csv')
        filename = os.path.join(datadir, 'ibtracs.csv')
        def progressbar(progress):
            print("\tProgress: [{0:50s}] {1:.1f}% ".format('#'*int(progress*50), progress*100), end='\r')
        # Download
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


setup(
    name='ibtracs',
    version='1.0',
    author='Levi Cowan',
    license='MIT',
    packages=['ibtracs'],
    cmdclass={'install': Install}
)
