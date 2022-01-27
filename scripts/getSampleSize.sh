#!/bin/bash

# A script to compute and print sample size
# Usage:
# source scripts/getSampleSize.sh <sample_config.yaml> <sample_name>
# Example:
# source scripts/getSampleSize.sh configs/datasets/datasets_ttdiffxs361_mini362.yaml singleTop

config="$1"
sample="$2"
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
if [[ "$sample" == "ttbar" || "$sample" == "ttbar_hw" ]]; then
    suffix+=('tt_truth' 'tt_PL')
fi

#echo "Suffix: ${suffix[*]}"

echo "$sample"

for sub in "${subcampaigns[@]}"; do
    echo " $sub"

    # read and parse the dataset config
    dids=$(python3 -c "import yaml; dd=yaml.load(open('${config}'), yaml.FullLoader); dids=dd['${sample}']['${sub}']; print(' '.join(dids)) if isinstance(dids, list) else print(dids)")

    for s in "${suffix[@]}"; do
        fnames=()
        for d in ${dids}; do
            fnames+=("${d}_${s}.root")
        done
        python3 -c "import sys; from datasets import listFiles_rucio; filesizes = listFiles_rucio(sys.argv[1:])[1]; print(f'  ${s}: {sum(filesizes)/1e6:.2f} MB ({len(filesizes)} files)')" "${fnames[@]}"
    done
done
