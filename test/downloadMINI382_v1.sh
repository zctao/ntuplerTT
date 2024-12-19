#!/bin/bash

datadir=${HOME}/data/ttbarDiffXs13TeV/MINI382_v1/
if [ ! -d ${datadir} ]; then
    echo "Create directory ${datadir}"
    mkdir -p ${datadir}
fi

config_datasets='configs/datasets/ttdiffxs382/datasets.yaml'

# Observed data
./scripts/downloadSamples.sh ${config_datasets} data ${datadir}

# Signal MC
# nominal
./scripts/downloadSamples.sh ${config_datasets} ttbar ${datadir}
# fastsim
./scripts/downloadSamples.sh ${config_datasets} ttbar_AFII ${datadir}
# alternative ttbar samples
./scripts/downloadSamples.sh ${config_datasets} ttbar_hw ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_amchw ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_mt169 ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_mt176 ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_hdamp ${datadir}
./scripts/downloadSamples.sh ${config_datasets} tthar_sh2212 ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_madspin ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_pthard1 ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_pthard2 ${datadir}
./scripts/downloadSamples.sh ${config_datasets} ttbar_recoil ${datadir}

# Background MC
# single top
./scripts/downloadSamples.sh ${config_datasets} singleTop_sch ${datadir}
./scripts/downloadSamples.sh ${config_datasets} singleTop_tch ${datadir}
./scripts/downloadSamples.sh ${config_datasets} singleTop_tW_DR_dyn ${datadir}
./scripts/downloadSamples.sh ${config_datasets} singleTop_tW_DS_dyn ${datadir}

# W+jets
./scripts/downloadSamples.sh ${config_datasets} Wjets ${datadir}

# Z+jets
./scripts/downloadSamples.sh ${config_datasets} Zjets ${datadir}

# ttV
./scripts/downloadSamples.sh ${config_datasets} ttV ${datadir}

# diboson
./scripts/downloadSamples.sh ${config_datasets} VV ${datadir}

# ttH
./scripts/downloadSamples.sh ${config_datasets} ttH ${datadir}