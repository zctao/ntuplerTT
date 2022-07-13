#!/bin/bash

findex=${1:-000030}

# a larger sample
#findex=000002

rootfiles_reco=${HOME}/data/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16e/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r10724_p4346.TTDIFFXS361_v05.MINI362_v1_tt.root/user.mromano.25781090._${findex}.tt.root

rootfiles_truth=${HOME}/data/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16e/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r10724_p4346.TTDIFFXS361_v05.MINI362_v1_tt_truth.root/user.mromano.25781090._${findex}.tt_truth.root

rootfiles_PL=${HOME}/data/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16e/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r10724_p4346.TTDIFFXS361_v05.MINI362_v1_tt_PL.root/user.mromano.25781090._${findex}.tt_PL.root

#rootfiles_sumw=${HOME}/data/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16e/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r10724_p4346.TTDIFFXS361_v05.MINI362_v1_sumWeights.root/user.mromano.25781090._${findex}.sumWeights.root

sumw_config=${SourceDIR}/configs/datasets/ttdiffxs361/sumWeights_detNP.yaml

run_test() {
    local suffix="$1"

    # get git hash
    local tag=`git rev-parse --short HEAD`
    #local branch=`git branch --show-current`
    echo "Currently on git commit $tag"
    echo

    if [ -z "$suffix" ]; then
        local label=${tag}
    else
        local label=${tag}_${suffix}
    fi

    # parton level
    python3 scripts/processMiniNtuples.py -n ttbar \
            -r ${rootfiles_reco} \
            -t ${rootfiles_truth} \
            -w ${sumw_config} \
            -o outputs/${label} -c

    # particle level
    #python3 scripts/processMiniNtuples.py -n ttbar \
    #        -r ${rootfiles_reco} \
    #        -p ${rootfiles_PL} \
    #        -w ${sumw_config} \
    #        -o outputs/${label} -c
}

run_test ${findex}

