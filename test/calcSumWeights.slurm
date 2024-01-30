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

data_dir=${HOME}/dataf/ttbarDiffXs13TeV/MINI362_v1

python ${SourceDIR}/scripts/computeSumWeights.py -h


python ${SourceDIR}/scripts/computeSumWeights.py ${SourceDIR}/configs/datasets/ttdiffxs361/datasets_mcWAlt.yaml -l ${data_dir} -v

echo exit code $?