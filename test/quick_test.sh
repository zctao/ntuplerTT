#!/bin/bash

rootfiles_reco=/home/ztao/datah/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4346.TTDIFFXS361_v06.MINI362_v1_tt.root/user.mromano.25781110._000023.tt.root

rootfiles_truth=/home/ztao/datah/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4346.TTDIFFXS361_v06.MINI362_v1_tt_truth.root/user.mromano.25781110._000023.tt_truth.root

rootfiles_PL=/home/ztao/datah/ttbarDiffXs13TeV/MINI362_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4346.TTDIFFXS361_v06.MINI362_v1_tt_PL.root/user.mromano.25781110._000023.tt_PL.root

sumw_config=${SourceDIR}/configs/datasets/ttdiffxs361/sumWeights_systCRL.yaml

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
    python scripts/processMiniNtuples.py -n ttbar \
            -r ${rootfiles_reco} \
            -t ${rootfiles_truth} \
            -w ${sumw_config} \
            -o outputs/${label} -c

    # particle level
    #python scripts/processMiniNtuples.py -n ttbar \
    #        -r ${rootfiles_reco} \
    #        -p ${rootfiles_PL} \
    #        -w ${sumw_config} \
    #        -o outputs/${label} -c
}

run_test

