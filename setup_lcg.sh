#!/bin/bash
lcgVersion=${1:-LCG_106}

hostname=$(uname -n)
echo $hostname

arch=x86_64-el9-gcc13-opt

if command -v lsetup &> /dev/null
then
    lsetup "views $lcgVersion $arch"
else
    source /cvmfs/sft.cern.ch/lcg/views/setupViews.sh ${lcgVersion} ${arch}
fi

export SourceDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# cf. https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself

export PYTHONPATH=$SourceDIR/python:$SourceDIR/scripts:$SourceDIR:$PYTHONPATH
