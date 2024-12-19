#!/bin/bash
dataconfig_dir=${1:-configs/datasets/ttdiffxs382}

samples=$(python -c "import os; from datasets import read_config; dsgen_dict = read_config('configs/datasets/general_ttDiffXSRun2.yaml'); print(' '.join(list(dsgen_dict['dsid'].keys())))")

for file in ${dataconfig_dir}/*.yaml; do
    echo "Processing $file"
    python3 scripts/getSampleSize.py ${file} -s ${samples} -v
done
