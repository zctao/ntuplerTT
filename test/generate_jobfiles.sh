#!/bin/bash
site=${1:-flashy}
outdir=${2:-}

dataset_config=configs/datasets/datasets_ttdiffxs361_mini362.yaml

if [ -z "$outdir" ]; then
    if [[ $site == "cedar" ]]; then
        outdir=/home/ztao/work/batch_output/NtupleTT/latest
    else
        outdir=/home/ztao/data/batch_output/NtupleTT/latest
    fi
fi

generate_files() {
    local sample="$1"
    local subcampaign="$2"
    shift 2
    local extra_args="$@"

    echo $sample
    echo $subcampaign

    python3 scripts/writeJobFile.py ${sample} -d ${dataset_config} \
            -o ${outdir}/${sample}/${subcampaign} -c ${subcampaign} \
            -s ${site} -q ${extra_args}
}

# ttbar
generate_files ttbar mc16a -t parton
generate_files ttbar mc16d -t parton
generate_files ttbar mc16e -t parton

# ttbar_hw_lj
generate_files ttbar_hw mc16a -t parton
generate_files ttbar_hw mc16d -t parton
generate_files ttbar_hw mc16e -t parton

# data
generate_files data 2015
generate_files data 2016
generate_files data 2017
generate_files data 2018
