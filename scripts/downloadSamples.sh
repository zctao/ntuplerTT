#!/bin/bash
# A script to download sample files to local disk via rucio
# Usage:
# ./downloadSamples.sh <dataset_config.yaml> <sample_label> [output directory] [era1, era2, ...]
# Example:
# ./downloadSamples.sh ../configs/datasets/ttdiffxs361/datasets_detNP.yaml ttbar

config="$1"
sample="$2"
localdir=${3:-${HOME}/data/ttbarDiffXs13TeV/MINI362_v1}
shift
shift
shift
subcampaigns=("$@")

if [ -z "$subcampaigns" ]; then
    if [[ "$sample" == "data" ]]; then
        subcampaigns=(2015 2016 2017 2018)
    else
        subcampaigns=(mc16a mc16d mc16e)
    fi
fi

# Suffix
suffix=('tt')

# MC samples
if [[ "$sample" != "data" ]]; then
    suffix+=('sumWeights')
fi

# Truth level for signal MC samples
if [[ "$sample" == ttbar* ]]; then
    suffix+=('tt_truth' 'tt_PL')
fi

echo "Suffix: ${suffix[*]}"

for sub in "${subcampaigns[@]}"; do
    #echo $sub
    outdir=${localdir}/${sample}/${sub}

    # read and parse the dataset config
    dids=$(python3 -c "import yaml; dd=yaml.load(open('${config}'), yaml.FullLoader); dids=dd['${sample}']['${sub}']; print(' '.join(dids)) if isinstance(dids, list) else print(dids)")

    mkdir -p ${outdir}

    for s in "${suffix[@]}"; do
        for d in ${dids}; do
            rucio download --dir ${outdir} ${d}_${s}.root
        done
    done
done
