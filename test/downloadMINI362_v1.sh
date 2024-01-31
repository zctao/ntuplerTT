#!/bin/bash

datadir=${HOME}/dataf/ttbarDiffXs13TeV/MINI362_v1
if [ ! -d ${datadir} ]; then
    echo "Create directory ${datadir}"
    mkdir -p ${datadir}
fi

# Observed data
config_obs=configs/datasets/ttdiffxs361/datasets_obs.yaml
./scripts/downloadSamples.sh ${config_obs} data ${datadir}

# Monte Carlo
# With detector systematic NP
config_detNP=configs/datasets/ttdiffxs361/datasets_detNP.yaml
./scripts/downloadSamples.sh ${config_detNP} ttbar ${datadir}
./scripts/downloadSamples.sh ${config_detNP} ttV ${datadir}
./scripts/downloadSamples.sh ${config_detNP} ttH ${datadir}
./scripts/downloadSamples.sh ${config_detNP} singleTop ${datadir}
./scripts/downloadSamples.sh ${config_detNP} VV ${datadir}

#  With SF systematics and CR loose selection
config_systCRL=configs/datasets/ttdiffxs361/datasets_systCRL.yaml
./scripts/downloadSamples.sh ${config_systCRL} ttbar ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} ttV ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} ttH ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} singleTop ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} Zjets ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} Wjets ${datadir}
./scripts/downloadSamples.sh ${config_systCRL} VV ${datadir}

#  MC weights and alternative samples
config_mcWAlt=configs/datasets/ttdiffxs361/datasets_mcWAlt.yaml
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_amc ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_hdamp ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_hw ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_mt169 ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_mt176 ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttbar_sh ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttV ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttV_syst ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} ttH ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} singleTop ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} singleTop_DS ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} singleTop_amc ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} singleTop_hw ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} VV ${datadir}
./scripts/downloadSamples.sh ${config_mcWAlt} VV_syst ${datadir}
