#!/bin/bash
outdir=/home/ztao/data/batch_output/NtupleTT/latest
dataset_config=configs/datasets/datasets_ttdiffxs361v8_mini362v1_klf.yaml

echo mc16a
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16a -c mc16a -n 6

echo mc16d
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16d -c mc16d -n 7

echo mc16e
python3 scripts/writeJobFile.py ttbar -d $dataset_config \
        -o $outdir/ttbar/mc16e -c mc16e -n 8
        
