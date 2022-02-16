#!/bin/bash
dataconfig_dir=${1:-configs/datasets/ttdiffxs361}

samples='ttbar ttbar_hw ttbar_amc ttbar_sh ttbar_alt singleTop singleTop_alt singleTop_hw singleTop_amc Wjets Zjets ttV ttV_alt VV VV_alt ttH'

for file in ${dataconfig_dir}/*.yaml; do
    echo "Processing $file"
    python3 scripts/getSampleSize.py ${file} -s ${samples} -v
done
