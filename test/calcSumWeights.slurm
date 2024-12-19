#!/bin/bash
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH --export=All
#SBATCH --output=%j.%x.out
#SBATCH --job-name=calcSumWeights

echo HOSTNAME=$HOSTNAME

# set up environment
source ${HOME}/ntuplerTT/setup_atlas.sh

echo "SourceDIR = $SourceDIR"

DataDir=${HOME}/data/ttbarDiffXs13TeV/MINI382_v1
Config=${SourceDIR}/configs/datasets/ttdiffxs382/datasets.yaml

python ${SourceDIR}/scripts/computeSumWeights.py ${Config} -l ${DataDir} -v

echo exit code $?