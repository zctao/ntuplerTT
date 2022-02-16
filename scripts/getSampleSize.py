#!/usr/bin/env python3
import yaml
from datasets import listFiles_rucio

import argparse

parser = argparse.ArgumentParser(
    description="A script to compute and report sample sizes"
    )

parser.add_argument('config', type=str,
                    help='Path to dataset config yaml file')
parser.add_argument('-s', '--samples', nargs='+', default=['ttbar'],
                    help='List of sample labels')
parser.add_argument('-e', '--era', nargs='*', type=str,
                    help='List of subcampaigns for MC or run years for data')
parser.add_argument('-v', '--verbosity', action='count', default=0,
                    help="Verbosity level")

args = parser.parse_args()

# read dataset config file
datasets_d = yaml.load(open(args.config), yaml.FullLoader)

totalsize = 0. # MB
nfiles = 0

for sample in args.samples:
    # check if sample in the config
    if not sample in datasets_d:
        if args.verbosity > 0:
            print(f"Cannot find sample {sample} in the config")
        continue
    else:
        if args.verbosity > 0:
            print(f"Processing sample {sample}")

    # Sub-campaigns or years
    if not args.era:
        if sample == 'data':
            era = ['2015', '2016', '2017', '2018']
        else:
            era = ['mc16a', 'mc16d', 'mc16e']
    else:
        era = args.era

    # Suffix
    if sample == 'data':
        # collision data
        suffix = ['tt']
    elif 'ttbar' in sample:
        # signal MC
        suffix = ['tt', 'sumWeights', 'tt_truth', 'tt_PL']
    else:
        # other MC
        suffix =['tt', 'sumWeights']

    for e in era:
        if args.verbosity > 1:
            print(f"{e}")

        dids = datasets_d[sample][e]
        if isinstance(dids, str):
            dids = [dids]

        for suf in suffix:
            fnames = [f"{d}_{suf}.root" for d in dids]
            filesizes = listFiles_rucio(fnames)[1]

            if args.verbosity > 1:
                print(f"  {suf}: {sum(filesizes)/1e6:.2f} MB ({len(filesizes)} files)")

            totalsize += sum(filesizes)/1e6
            nfiles += len(filesizes)

print(f"Total file size: {totalsize/1e3:.2f} GB ({nfiles} files)")
            
