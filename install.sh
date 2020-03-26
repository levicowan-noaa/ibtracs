#!/bin/sh

workdir=$(dirname $(readlink -f $0))
echo "using working directory ${workdir}"

echo "setting up directories..."
mkdir -p ${workdir}/data

if [ ! -e ${workdir}/data/ibtracs.csv ]; then
    echo "downloading IBTrACS v04r00 CSV file..."
    wget https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/csv/ibtracs.ALL.list.v04r00.csv -O ${workdir}/data/ibtracs.ALL.list.v04r00.csv
    echo "symlinking CSV file to ibtracs.csv for convenience"
    ln -s ${workdir}/data/ibtracs.ALL.list.v04r00.csv ${workdir}/data/ibtracs.csv
fi

modulepath=$(dirname ${workdir})
echo "adding ${modulepath} to \$PYTHONPATH to allow importing"
export PYTHONPATH=$PYTHONPATH:${modulepath}
