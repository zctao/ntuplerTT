#!/bin/bash
# A script to copy sample files to local disk from eos

config="$1"
sample="$2"
sourcedir="$3" #/eos/user/g/gfalsett/ttdiffxs361.mini362_v1/directories_Gregorio
targetdir=${4:-${HOME}/dataf/ttbarDiffXs13TeV/MINI362_v1}
shift
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
    outdir=${targetdir}/${sample}/${sub}
    #echo $outdir

    # read and parse the dataset config
    dids=$(python3 -c "import yaml; dd=yaml.load(open('${config}'), yaml.FullLoader); dids=dd['${sample}']['${sub}']; print(' '.join(dids)) if isinstance(dids, list) else print(dids)")

    for s in "${suffix[@]}"; do
        for d in ${dids}; do
	    #echo "${sourcedir}/${d}_${s}"
            rsync -azP --mkpath --ignore-existing --log-file=rsync_samples_`date +"%Y%m%d"`.log ${sourcedir}/${d}_${s}/ ${outdir}/${d}_${s}.root
        done
    done
done
