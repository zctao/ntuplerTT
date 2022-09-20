#!/usr/bin/env python3
import os
import sys
import yaml
import time

from datasets import read_config
from writeJobFile import writeJobFile

# Usage
def printHelp():
    print("Usage: python generate_jobfiles_mini362_v1.py [site]")

site = 'atlasserv' # default, options: atlasserv, flashy, cedar
if len(sys.argv) == 1:
    pass
elif len(sys.argv) == 2:
    if sys.argv[1] in ['-h', '-?', 'help']:
        printHelp()
        sys.exit()
    else:
        site = sys.argv[1]
else:
    printHelp()
    sys.exit()

##
# local directory where input sample files are stored
local_sample_dir = os.path.join(
    os.getenv("HOME"), 'data/ttbarDiffXs13TeV/MINI362_v1')

##
# output directory
topoutdir = os.path.join(os.getenv("HOME"), 'data/NtupleTT/latest')

if not os.path.isdir(topoutdir):
    os.makedirs(topoutdir)

##
# systematics config
syst_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/systematics.yaml')
syst_dict = read_config(syst_config)

##
# number of jobs for each sample
# TODO: update this
njobs_dict = {'ttbar': 10, 'ttbar_amc': 10, 'ttbar_hdamp': 10, 'ttbar_hw': 10, 'ttbar_mt169': 10, 'ttbar_mt176': 10, 'ttbar_sh': 10, 'ttbar_AFII': 10}

def getSystTreeNames():
    trees = []
    for key in syst_dict:
        if syst_dict[key]['type'] != 'Branch':
            continue

        prefix = syst_dict[key]['prefix']

        for syst in syst_dict[key]['uncertainties']:
            for va in syst_dict[key]['variations']:
                trees.append(f"{prefix}_{syst}_{va}")
    return trees

t_start = time.time()

# Common arguments for writeJobFile
common_args = {
    'email': os.getenv('USER')+'@phas.ubc.ca',
    'site': site,
    'local_dir': local_sample_dir,
    #'max_task': 8,
    'verbosity': 0
}

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

treenames = ['nominal'] + getSystTreeNames()

# ttbar
print("ttbar")
jobfiles_dict['detNP']['ttbar'] = {}
for tname in treenames:
    print(f"  Tree: {tname}")

    jobfiles_dict['detNP']['ttbar'][tname] = {}
    if tname == 'nominal':
        extra_args = "-c"
    else:
        extra_args = f"--treename {tname}"

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"    {era}")

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
for signal in ['ttbar', 'ttbar_amc', 'ttbar_hdamp', 'ttbar_hw', 'ttbar_mt169', 'ttbar_mt176', 'ttbar_sh']:
    print(f"{signal}")

    jobfiles_dict['mcWAlt'][signal] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"  {era}")

        fname_tt = writeJobFile(
            signal,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir,'mcWAlt',f'{signal}_nominal',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get(signal, 1),
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

    fname_tt = writeJobFile(
        sample_name,
        dataset_mcWAlt_config,
        outdir = os.path.join(topoutdir,'mcWAlt',f'{sample_name}_nominal',f'{era}'),
        subcampaigns = [era],
        truth_level = 'parton',
        njobs = njobs_dict.get(sample_name, 1),
        sumw_config = sumw_config_afii,
        **common_args
    )

# MC backgrounds
for bkg in ['VV', 'VV_syst', 'singleTop', 'singleTop_DS', 'singleTop_amc', 'singleTop_hw', 'ttH', 'ttV', 'ttV_syst']:
    print(f"{bkg}")

    jobfiles_dict['mcWAlt'][bkg] = {}

    for era in ['mc16a', 'mc16d', 'mc16e']:
        print(f"  {era}")

        fname_bkg = writeJobFile(
            bkg,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir, 'mcWAlt', f'{bkg}_nominal',f'{era}'),
            subcampaigns = [era],
            njobs = njobs_dict.get(bkg, 1),
            **common_args
        )

        jobfiles_dict['mcWAlt'][bkg][era] = fname_bkg

t_done = time.time()
print(f"Total time: {(t_done-t_start)/60.:.2f} min")

# write dict to disk
foutname = 'configs/jobs_mini362_v1/jobfiles.yaml'

if not os.path.isdir(os.path.dirname(foutname)):
    os.makedirs(os.path.dirname(foutname))

print(f"Write job file config: {foutname}")
with open(foutname, 'w') as outfile:
    yaml.dump(jobfiles_dict, outfile)
