#!/bin/bash

rootfiles_reco=/data/ztao/ttbarDiffXs13TeV/MINI382_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4514.274_vv01.MINI382_tt.root/user.mromano.42890957._000001.tt.root

rootfiles_truth=/data/ztao/ttbarDiffXs13TeV/MINI382_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4514.274_vv01.MINI382_tt_truth.root/user.mromano.42890957._000001.tt_truth.root

rootfiles_PL=/data/ztao/ttbarDiffXs13TeV/MINI382_v1/ttbar/mc16a/user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4514.274_vv01.MINI382_tt_PL.root/user.mromano.42890957._000001.tt_PL.root

sumw_config=${SourceDIR}/configs/datasets/ttdiffxs382/sumWeights.yaml

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
            -o outputs/${label} -g -v -u

    # particle level
    #python scripts/processMiniNtuples.py -n ttbar \
    #        -r ${rootfiles_reco} \
    #        -p ${rootfiles_PL} \
    #        -w ${sumw_config} \
    #        -o outputs/${label} -g -v -u
}

run_test

