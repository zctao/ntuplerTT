#!/usr/bin/env python3
import os
import sys
import yaml
import time

from datasets import getSystTreeNames
from writeJobFile import writeJobFile

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input-dir", type=str,
                    default="~/data/ttbarDiffXs13TeV/MINI382_v1/",
                    help="Local directory where input sample files are stored")
parser.add_argument("-o", "--output-dir", type=str,
                    default="~/data/ntuplerTT/latest/",
                    help="Output directory")
parser.add_argument("-e", "--email", type=str,
                    help="Email for slurm to send notification")
parser.add_argument("-f", "--filters", type=str, nargs='+', default=[],
                    help="Key words to filter job files to generate. If multiple key words are provided, only jobs that match to all key words are generated")

args = parser.parse_args()

##
# input sample directory
local_sample_dir = os.path.expanduser(args.input_dir)
if not os.path.isdir(local_sample_dir):
    sys.exit(f"Found no input directory: {local_sample_dir}")

##
# output directory
topoutdir = os.path.expanduser(args.output_dir).rstrip('/')

# if ends with "latest", create a new directory with timestamp and a symbolic link
if os.path.basename(topoutdir) == 'latest':
    topoutdir = os.path.join(os.path.dirname(topoutdir), f"{time.strftime('%Y%m%d')}")

if not os.path.isdir(topoutdir):
    print(f"Create a new output directory: {topoutdir}")
    os.makedirs(topoutdir)

# create a symbolic link
latest_link = os.path.join(os.path.dirname(topoutdir), 'latest')
if os.path.islink(latest_link):
    os.unlink(latest_link) # remove existing link
os.symlink(topoutdir, latest_link)

print(f"Output directory: {topoutdir}")

##
# systematics config
source_dir = os.getenv('SourceDIR')
if source_dir is None:
    sys.exit("Environment variable 'SourceDIR' is not set.")
syst_config = os.path.join(source_dir, 'configs/datasets/systematics.yaml')

##
# number of jobs for each sample
# TODO: update this
njobs_dict = {'ttbar': 10, 'ttbar_amchw': 10, 'ttbar_hdamp': 10, 'ttbar_hw': 10, 'ttbar_mt169': 10, 'ttbar_mt176': 10, 'ttbar_AFII': 10, 'ttbar_madspin': 10, 'ttbar_pthard1': 10, 'ttbar_pthard2': 10, 'ttbar_sh2212': 10, 'ttbar_recoil': 10, 'ttbar_minnlops': 10}

t_start = time.time()

# Common arguments for writeJobFile
common_args = {
    'email': args.email,
    'site': 'atlasserv',
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

dataset_config = os.path.join(source_dir, 'configs/datasets/ttdiffxs382/datasets.yaml')
print(f"Generate job files from {dataset_config}")

######
# Observed data
jobfiles_dict['obs'] = {}
jobfiles_dict['fakes'] = {}

for year in ['2015', '2016', '2017', '2018']:
    print(f"Year {year}")

    if matchFilterKeys(keywords=['obs', year], filters=args.filters):

        print("  Observed data")
        try:
            fname_obs = writeJobFile(
                'data',
                dataset_config,
                outdir = os.path.join(topoutdir,'obs',f'{year}'),
                subcampaigns = [year],
                njobs = njobs_dict.get('data', 1),
                **common_args
            )
        except Exception as e:
            print(f"Failed to generate job file: {e}")
            fname_obs = None

        jobfiles_dict['obs'][year] = fname_obs

    if matchFilterKeys(keywords=['fakes', year], filters=args.filters):

        # data-driven fakes background
        print("  Fake estimation")
        try:
            fname_fakes = writeJobFile(
                'data',
                dataset_config,
                outdir = os.path.join(topoutdir,'fakes',f'{year}'),
                subcampaigns = [year],
                njobs = njobs_dict.get('data', 1),
                extra_args = "--treename nominal_Loose",
                **common_args
            )
        except Exception as e:
            print(f"Failed to generate job file: {e}")
            fname_fakes = None

        jobfiles_dict['fakes'][year] = fname_fakes

######
samples_MC = ['ttbar', 'singleTop_sch', 'singleTop_tch', 'singleTop_tW_DR_dyn', 'Wjets', 'Zjets', 'ttV', 'VV', 'ttH']

# alternative background samples
samples_MC += ['singleTop_tW_DS_dyn']

treenames = ['nominal'] + getSystTreeNames(syst_config)

for sample in samples_MC:
    print(f"{sample}")
    if not sample in jobfiles_dict:
        jobfiles_dict[sample] = {}

    isSignal = sample.startswith('ttbar')

    for tname in treenames:
        print(f"  Tree: {tname}")

        jobfiles_dict[sample][tname] = {}

        isNominal = tname == 'nominal'

        for era in ['mc16a', 'mc16d', 'mc16e']:
            print(f"    {era}")

            if not matchFilterKeys(keywords=[sample,tname,era], filters=args.filters):
                continue

            # Process parton level only for ttbar samples
            truth_level = 'parton' if isNominal and isSignal else ''

            # extra arguments
            extra_args = f"--treename {tname}"
            if isNominal and isSignal:
                # store generator weights and unmatched truth events
                extra_args += " -g -u"

            try:
                fname_mc = writeJobFile(
                    sample,
                    dataset_config,
                    outdir = os.path.join(topoutdir, sample, tname, era),
                    subcampaigns = [era],
                    truth_level = truth_level,
                    njobs = njobs_dict.get(sample, 1),
                    extra_args = extra_args,
                    **common_args
                )
            except Exception as e:
                print(f"Failed to generate job file: {e}")
                fname_mc = None

            jobfiles_dict[sample][tname][era] = fname_mc

# Alternative signal samples
samples_alt_ttbar = ['ttbar_hw', 'ttbar_amchw', 'ttbar_mt169', 'ttbar_mt176', 'ttbar_hdamp', 'ttbar_madspin', 'ttbar_sh2212', 'ttbar_pthard1', 'ttbar_pthard2', 'ttbar_recoil']

for sample in samples_alt_ttbar:
    print(f"{sample}")
    jobfiles_dict[sample] = {}

    print("  Tree: nominal")
    tname = 'nominal'
    jobfiles_dict[sample][tname] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"    {era}")

        if not matchFilterKeys(keywords=[sample,tname,era], filters=args.filters):
            continue

        extra_args = f"--treename {tname}"

        try:
            fname_mc = writeJobFile(
                sample,
                dataset_config,
                outdir = os.path.join(topoutdir, sample, tname, era),
                subcampaigns = [era],
                truth_level = 'parton',
                njobs = njobs_dict.get(sample, 1),
                extra_args = extra_args,
                **common_args
            )
        except Exception as e:
            print(f"Failed to generate job file: {e}")
            fname_mc = None

        jobfiles_dict[sample][tname][era] = fname_mc

# FastSim ttbar
samples_AFII = 'ttbar_AFII'
print(f"{samples_AFII}")
jobfiles_dict[samples_AFII] = {}
print("  Tree: nominal")
jobfiles_dict[samples_AFII]['nominal'] = {}

# A special sum weights config for ttbar AFII
sumw_config_afii = os.path.join(os.path.dirname(dataset_config), "sumWeights_AFII.yaml")

for era in ['mc16a', 'mc16d', 'mc16e']:
    print(f"    {era}")

    if not matchFilterKeys(keywords=[samples_AFII,'nominal',era], filters=args.filters):
        continue

    try:
        fname_mc = writeJobFile(
            samples_AFII,
            dataset_config,
            outdir = os.path.join(topoutdir, samples_AFII, 'nominal', era),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get(samples_AFII, 1),
            sumw_config = sumw_config_afii,
            extra_args = "-g",
            **common_args
        )
    except Exception as e:
        print(f"Failed to generate job file: {e}")
        fname_mc = None

    jobfiles_dict[samples_AFII]['nominal'][era] = fname_mc

######
t_done = time.time()
print(f"Total time: {(t_done-t_start)/60.:.2f} min")

# write dict to disk
foutname = os.path.join(topoutdir, 'jobs_mini382_v1/jobfiles.yaml')

if not os.path.isdir(os.path.dirname(foutname)):
    os.makedirs(os.path.dirname(foutname))

print(f"Write job file config: {foutname}")
with open(foutname, 'w') as outfile:
    yaml.dump(jobfiles_dict, outfile)