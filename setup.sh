#!/bin/bash

export SourceDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# cf. https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself

lcgVersion=LCG_98python3_ATLAS_10
arch=x86_64-centos7-gcc8-opt

source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh ${lcgVersion} ${arch}

export PYTHONPATH=$SourceDIR/python:$SourceDIR:$PYTHONPATH
