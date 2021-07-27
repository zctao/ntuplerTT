#!/bin/bash
site=${1:-flashy}
outdir=${2:-}
dataset_config=${3:-configs/datasets/datasets_ttdiffxs361v8_mini362v1_klf.yaml}

if [ -z "$outdir" ]; then
    if [[ $site == "cedar" ]]; then
        outdir=/home/ztao/work/batch_output/NtupleTT/latest
    else
        outdir=/home/ztao/data/batch_output/NtupleTT/latest
    fi
fi

generate_files() {
    sample="$1"
    subcampaign="$2"
    echo $sample
    echo $subcampaign

    python3 scripts/writeJobFile.py ${sample} -d ${dataset_config} \
            -o ${outdir}/${sample}/${subcampaign} -c ${subcampaign} \
            -s ${site} -q
}

# ttbar
generate_files ttbar mc16a
generate_files ttbar mc16d
generate_files ttbar mc16e

# ttbar_hw_lj
generate_files ttbar_hw_lj mc16a
generate_files ttbar_hw_lj mc16d
generate_files ttbar_hw_lj mc16e

# ttbar_hw_ll
generate_files ttbar_hw_ll mc16a
generate_files ttbar_hw_ll mc16d
generate_files ttbar_hw_ll mc16e
