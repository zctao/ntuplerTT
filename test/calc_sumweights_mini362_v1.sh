#!/bin/bash
config_dir=${1:-configs/datasets/ttdiffxs361}
data_dir=${2:-${HOME}/dataf/ttbarDiffXs13TeV/MINI362_v1}

dataset_configs=$(ls ${config_dir}/datasets_*.yaml)
for fconfig in ${dataset_configs[@]}; do
    if [[ -f ${fconfig} ]]; then
        echo ${fconfig}
        if [[ "${fconfig}" == *"klf"* ]]; then
            python scripts/computeSumWeights.py ${fconfig} -l ${data_dir}_klf -v
        else
            python scripts/computeSumWeights.py ${fconfig} -l ${data_dir} -v
        fi
    fi
done
