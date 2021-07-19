#!/bin/bash
site=${1:-flashy}

outdir=/home/ztao/data/batch_output/NtupleTT/latest
if [[ $site == "cedar" ]]; then
    outdir=/home/ztao/work/batch_output/NtupleTT/latest
fi

dataset_config=configs/datasets/datasets_ttdiffxs361v8_mini362v1_klf.yaml

echo mc16a
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16a -c mc16a -s $site -q

echo mc16d
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16d -c mc16d -s $site -q

echo mc16e
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16e -c mc16e -s $site -q
