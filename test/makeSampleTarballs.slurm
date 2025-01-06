#!/bin/bash
#SBATCH --mem=4G
#SBATCH --time=6:00:00
#SBATCH --export=All
#SBATCH --output=%j.%x.out
#SBATCH --job-name=makeSampleTarballs

echo HOSTNAME=$HOSTNAME

# set up environment
source ${HOME}/ntuplerTT/setup_atlas.sh

echo "SourceDIR = ${SourceDIR}"

DataDir=${HOME}/data/ntuplerTT/latest/
echo "DataDir = ${DataDir}"

python ${SourceDIR}/scripts/makeTarballs.py -i ${DataDir} -v

echo exit code $?