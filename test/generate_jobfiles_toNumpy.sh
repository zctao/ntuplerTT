#!/bin/bash
site=${1:-flashy}
outdir=${2:-}

if [ -z "$outdir" ]; then
    if [[ $site == "cedar" ]]; then
        outdir=/home/ztao/work/batch_output/NtupleTT/latest
    else
        outdir=/home/ztao/data/batch_output/NtupleTT/latest
    fi
fi

klfitter_LLcut=-50
dummy_value=-99

# convert from root trees to numpy arrays
generate_files_tonumpy() {
    sample="$1"
    subcampaign="$2"
    njobs="$3"
    echo $sample
    echo $subcampaign

    workdir=${outdir}/${sample}/${subcampaign}
    
    for truth in parton particle; do
        for channel in ejets mjets; do
            python3 scripts/writeJobFile_toNumpy.py \
                    ${workdir}/ntuplelist_${truth}_${channel}.txt \
                    -o ${workdir}/npz \
                    -k ${klfitter_LLcut} -p ${dummy_value} -s ${site} \
                    -n ${njobs} -q
        done
    done
}

# ttbar
generate_files_tonumpy ttbar mc16a 6
generate_files_tonumpy ttbar mc16d 7
generate_files_tonumpy ttbar mc16e 7

# ttbar_hw
generate_files_tonumpy ttbar_hw_lj mc16a 6
generate_files_tonumpy ttbar_hw_lj mc16d 7
generate_files_tonumpy ttbar_hw_lj mc16e 7

generate_files_tonumpy ttbar_hw_ll mc16a 4
generate_files_tonumpy ttbar_hw_ll mc16d 6
generate_files_tonumpy ttbar_hw_ll mc16e 6
