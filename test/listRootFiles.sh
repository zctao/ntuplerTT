#!/bin/bash
#####
# dump paths of root files under <topdir>xs into lists

topdir="${1:-/home/ztao/data/batch_output/NtupleTT/latest}"

prefix=mntuple
samples=( ttbar ttbar_hw_lj ttbar_hw_ll )
subcampaigns=( mc16a mc16d mc16e )
truthlevels=( parton particle )
channels=( ejets mjets )

for sample in "${samples[@]}"; do
    for subcamp in "${subcampaigns[@]}"; do
        for tl in "${truthlevels[@]}"; do
            for ch in "${channels[@]}"; do
                curdir=${topdir}/${sample}/${subcamp}
                filepattern="${prefix}_${sample}_*_${tl}_${ch}.root"
                outfile=${curdir}/ntuplelist_${tl}_${ch}.txt
                find $curdir -name $filepattern > $outfile
            done   
        done
    done
done
