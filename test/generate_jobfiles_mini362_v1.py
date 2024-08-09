#!/usr/bin/env python3
import os
import sys
import yaml
import time

from datasets import getSystTreeNames
from writeJobFile import writeJobFile

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--site", choices=["atlasserv", "flashy", "cedar"],
                    default="atlasserv",
                    help="Site to run jobs on")
parser.add_argument("-i", "--input-dir", type=str,
                    default="~/dataf/ttbarDiffXs13TeV/MINI362_v1",
                    help="Local directory where input sample files are stored")
parser.add_argument("-o", "--output-dir", type=str,
                    default="~/data/NtupleTT/latest",
                    help="Output directory")
parser.add_argument("-e", "--email", type=str,
                    help="Email for slurm to send notification")
parser.add_argument("-f", "--filters", type=str, nargs='+',
                    help="Key words to filter job files to generate. If multiple key words are provided, only jobs that match to all key words are generated")

args = parser.parse_args()

##
# input sample directory
local_sample_dir = os.path.expanduser(args.input_dir)
if not os.path.isdir(local_sample_dir):
    sys.exit(f"Found no input directory: {local_sample_dir}")

##
# output directory
topoutdir = os.path.expanduser(args.output_dir)
if not os.path.isdir(topoutdir):
    os.makedirs(topoutdir)

##
# systematics config
syst_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/systematics.yaml')

##
# number of jobs for each sample
# TODO: update this
njobs_dict = {'ttbar': 10, 'ttbar_amc': 15, 'ttbar_hdamp': 10, 'ttbar_hw': 15, 'ttbar_mt169': 10, 'ttbar_mt176': 10, 'ttbar_sh': 10, 'ttbar_AFII': 10, 'ttbar_madspin': 10, 'ttbar_pthard1': 10, 'ttbar_sh2212': 10}

t_start = time.time()

# Common arguments for writeJobFile
common_args = {
    'email': args.email,
    'site': args.site,
    'local_dir': local_sample_dir,
    #'max_task': 8,
    'verbosity': 0
}

def matchFilterKeys(keywords, filters):
    all_matched = True

    for kw_filter in filters:
        amatch = False
        for kw in keywords:
            if kw_filter in kw:
                amatch = True
                break

        all_matched &= amatch

    return all_matched

jobfiles_dict = {}

######
# Observed data
dataset_obs_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_obs.yaml')
print(f"Generate job files from {dataset_obs_config}")

jobfiles_dict['obs'] = {}
jobfiles_dict['fakes'] = {}

for year in ['2015', '2016', '2017', '2018']:
    print(f"Year {year}")

    if matchFilterKeys(keywords=['obs', year], filters=args.filters):

        print("  Observed data")
        fname_obs = writeJobFile(
            'data',
            dataset_obs_config,
            outdir = os.path.join(topoutdir,'obs',f'{year}'),
            subcampaigns = [year],
            njobs = njobs_dict.get('data', 1),
            **common_args
        )

        jobfiles_dict['obs'][year] = fname_obs

    if matchFilterKeys(keywords=['fakes', year], filters=args.filters):

        # data-driven fakes background
        print("  Fake estimation")
        fname_fakes = writeJobFile(
            'data',
            dataset_obs_config,
            outdir = os.path.join(topoutdir,'fakes',f'{year}'),
            subcampaigns = [year],
            njobs = njobs_dict.get('data', 1),
            extra_args = "--treename nominal_Loose",
            **common_args
        )

        jobfiles_dict['fakes'][year] = fname_fakes

######
# With detector systematic NP
dataset_detNP_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_detNP.yaml')
print(f"Generate job files from {dataset_detNP_config}")

jobfiles_dict['detNP'] = {}

treenames = ['nominal'] + getSystTreeNames(syst_config)

# ttbar
print("ttbar")
jobfiles_dict['detNP']['ttbar'] = {}
for tname in treenames:
    print(f"  Tree: {tname}")

    jobfiles_dict['detNP']['ttbar'][tname] = {}

    extra_args = f"--treename {tname}"

    for era in ['mc16a', 'mc16d', 'mc16e']:

        print(f"    {era}")

        if not matchFilterKeys(keywords=['detNP','ttbar',tname,era], filters=args.filters):
            continue

        fname_tt = writeJobFile(
            'ttbar',
            dataset_detNP_config,
            outdir = os.path.join(topoutdir,'detNP',f'ttbar_{tname}',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get('ttbar', 1),
            extra_args = extra_args,
            **common_args
        )

        jobfiles_dict['detNP']['ttbar'][tname][era] = fname_tt

# MC backgrounds
for bkg in ['VV', 'singleTop', 'ttH', 'ttV']:
    print(f"{bkg}")

    jobfiles_dict['detNP'][bkg] = {}

    for tname in treenames:
        print(f"  Tree: {tname}")

        jobfiles_dict['detNP'][bkg][tname] = {}

        for era in ['mc16a', 'mc16d', 'mc16e']:
            print(f"    {era}")

            if not matchFilterKeys(keywords=['detNP',bkg,tname,era], filters=args.filters):
                continue

            fname_bkg = writeJobFile(
                bkg,
                dataset_detNP_config,
                outdir = os.path.join(topoutdir,'detNP',f'{bkg}_{tname}',f'{era}'),
                subcampaigns = [era],
                njobs = njobs_dict.get(bkg, 1),
                extra_args = f"--treename {tname}",
                **common_args
            )

            jobfiles_dict['detNP'][bkg][tname][era] = fname_bkg

######
# With SF systematics and CR loose selection
dataset_systCRL_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_systCRL.yaml')
print(f"Generate job files from {dataset_systCRL_config}")

jobfiles_dict['systCRL'] = {}

for sample in ['ttbar', 'VV', 'Wjets', 'Zjets', 'singleTop', 'ttH', 'ttV']:
    print(f"{sample}")

    jobfiles_dict['systCRL'][sample] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"  {era}")

        if not matchFilterKeys(keywords=['systCRL',sample,era], filters=args.filters):
            continue

        fname_mc = writeJobFile(
            sample,
            dataset_systCRL_config,
            outdir = os.path.join(topoutdir,'systCRL',f'{sample}_nominal',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton' if sample=='ttbar' else '',
            njobs = njobs_dict.get(sample, 1),
            **common_args
        )

        jobfiles_dict['systCRL'][sample][era] = fname_mc

######
# MC weights and alternative samples
dataset_mcWAlt_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_mcWAlt.yaml')
print(f"Generate job files from {dataset_mcWAlt_config}")

jobfiles_dict['mcWAlt'] = {}

# ttbar
for signal in ['ttbar', 'ttbar_amc', 'ttbar_hdamp', 'ttbar_hw', 'ttbar_mt169', 'ttbar_mt176', 'ttbar_sh', 'ttbar_madspin', 'ttbar_pthard1', 'ttbar_sh2212']:
    print(f"{signal}")

    # include MC generator weight variations
    # also save the unmatched truth events for efficiency calculation later if signal sample
    extra_args = "-g -u" if sample=='ttbar' else "-g"

    jobfiles_dict['mcWAlt'][signal] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"  {era}")

        if not matchFilterKeys(keywords=['mcWAlt',signal,era], filters=args.filters):
            continue

        fname_tt = writeJobFile(
            signal,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir,'mcWAlt',f'{signal}_nominal',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get(signal, 1),
            extra_args = extra_args,
            **common_args
        )

        jobfiles_dict['mcWAlt'][signal][era] = fname_tt

# ttbar FastSim
sample_name = "ttbar_AFII"
print(sample_name)
jobfiles_dict['mcWAlt'][sample_name] = {}

# A special sum weights config for ttbar AFII
sumw_config_afii = os.path.join(os.path.dirname(dataset_mcWAlt_config), "sumWeights_mcWAlt_AFII.yaml")

for era in ['mc16a', 'mc16d', 'mc16e']:
    print(f"  {era}")

    if not matchFilterKeys(keywords=['mcWAlt',sample_name,era], filters=args.filters):
        continue

    fname_tt = writeJobFile(
        sample_name,
        dataset_mcWAlt_config,
        outdir = os.path.join(topoutdir,'mcWAlt',f'{sample_name}_nominal',f'{era}'),
        subcampaigns = [era],
        truth_level = 'parton',
        njobs = njobs_dict.get(sample_name, 1),
        sumw_config = sumw_config_afii,
        extra_args = "-g",
        **common_args
    )

    jobfiles_dict['mcWAlt'][sample_name][era] = fname_tt

# MC backgrounds
for bkg in ['VV', 'VV_syst', 'singleTop', 'singleTop_DS', 'singleTop_amc', 'singleTop_hw', 'ttH', 'ttV', 'ttV_syst']:
    print(f"{bkg}")

    jobfiles_dict['mcWAlt'][bkg] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"  {era}")

        if not matchFilterKeys(keywords=['mcWAlt',bkg,era], filters=args.filters):
            continue

        fname_bkg = writeJobFile(
            bkg,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir, 'mcWAlt', f'{bkg}_nominal',f'{era}'),
            subcampaigns = [era],
            njobs = njobs_dict.get(bkg, 1),
            extra_args = "-g", # include MC generator weight variations
            **common_args
        )

        jobfiles_dict['mcWAlt'][bkg][era] = fname_bkg

t_done = time.time()
print(f"Total time: {(t_done-t_start)/60.:.2f} min")

# write dict to disk
foutname = os.path.join(topoutdir, 'jobs_mini362_v1/jobfiles.yaml')

if not os.path.isdir(os.path.dirname(foutname)):
    os.makedirs(os.path.dirname(foutname))

print(f"Write job file config: {foutname}")
with open(foutname, 'w') as outfile:
    yaml.dump(jobfiles_dict, outfile)
