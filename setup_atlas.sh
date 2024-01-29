#!/bin/bash
lcgVersion=${1:-LCG_105}

hostname=$(uname -n)
echo $hostname

# setupATLAS
export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase
source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh

arch=x86_64-el9-gcc11-opt
lsetup "views $lcgVersion $arch"
#source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh ${lcgVersion} ${arch}

# lsetup rucio
# NOTE: rucio client is only needed for listing input files
# It messes up the environment for reading remote files via xrootd
# Type "letup rucio" manually when generating job files or listing inputs
# DO NOT set up rucio during actual running
# unless all inputs are on local storage and xrootd is not needed

#lsetup xcache xrootd

export SourceDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# cf. https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself

export PYTHONPATH=$SourceDIR/python:$SourceDIR/scripts:$SourceDIR:$PYTHONPATH
