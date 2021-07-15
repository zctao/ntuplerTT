#!/bin/bash
outdir=/home/ztao/data/batch_output/NtupleTT/latest
dataset_config=configs/datasets/datasets_ttdiffxs361v8_mini362v1_klf.yaml

echo ttbar_hw_lj
echo mc16a
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16a -c mc16a -n 5
echo mc16d
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16d -c mc16d -n 7
echo mc16e
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16e -c mc16e -n 7

echo ttbar_hw_ll
echo mc16a
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16a -c mc16a -n 4
echo mc16d
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16d -c mc16d -n 7
echo mc16e
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16e -c mc16e -n 7
