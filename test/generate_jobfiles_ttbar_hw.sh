#!/bin/bash
site=${1:-flashy}

outdir=/home/ztao/data/batch_output/NtupleTT/latest
if [[ $site == "cedar" ]]; then
    outdir=/home/ztao/work/batch_output/NtupleTT/latest
fi

dataset_config=configs/datasets/datasets_ttdiffxs361v8_mini362v1_klf.yaml

echo ttbar_hw_lj
echo mc16a
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16a -c mc16a -s $site -q
echo mc16d
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16d -c mc16d -s $site -q
echo mc16e
python3 scripts/writeJobFile.py ttbar_hw_lj -d $dataset_config \
        -o $outdir/ttbar_hw_lj/mc16e -c mc16e -s $site -q

echo ttbar_hw_ll
echo mc16a
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16a -c mc16a -s $site -q
echo mc16d
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16d -c mc16d -s $site -q
echo mc16e
python3 scripts/writeJobFile.py ttbar_hw_ll -d $dataset_config \
        -o $outdir/ttbar_hw_ll/mc16e -c mc16e -s $site -q
