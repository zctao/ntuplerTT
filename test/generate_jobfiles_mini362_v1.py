#!/usr/bin/env python3
import os
import yaml

from datasets import read_config
from writeJobFile import writeJobFile

# TODO: update this
njobs_dict = {'ttbar': 10, 'ttbar_amc': 10, 'ttbar_hdamp': 10, 'ttbar_hw': 10, 'ttbar_mt169': 10, 'ttbar_mt176': 10, 'ttbar_sh': 10}

# local directory where input sample files are stored
local_sample_dir = os.path.join(
    os.getenv("HOME"), 'data/ttbarDiffXs13TeV/MINI362_v1')

# systematics config
syst_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/systematics.yaml')
syst_dict = read_config(syst_config)

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

# output directory
topoutdir = os.path.join(os.getenv("HOME"), 'data/batch_output/NtupleTT/latest')
if not os.path.isdir(topoutdir):
    os.makedirs(topoutdir)

# Common arguments for writeJobFile
common_args = {
    'email': os.getenv('USER')+'@phas.ubc.ca',
    'site': 'flashy',
    'local_dir': local_sample_dir,
    'max_task': 8,
    'verbosity': 0
}

######
# Observed data
dataset_obs_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_obs.yaml')

for year in ['2015', '2016', '2017', '2018']:
    writeJobFile(
        'data',
        dataset_obs_config,
        outdir = os.path.join(topoutdir,'obs',f'{year}'),
        subcampaigns = [year],
        njobs = njobs_dict.get('data', 1),
        **common_args
    )

    # data-driven fakes background
    writeJobFile(
        'data',
        dataset_obs_config,
        outdir = os.path.join(topoutdir,'fakes',f'{year}'),
        subcampaigns = [year],
        njobs = njobs_dict.get('data', 1),
        extra_args = "--treename nominal_Loose",
        **common_args
    )

######
# With detector systematic NP
dataset_detNP_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_detNP.yaml')

# ttbar
for era in ['mc16a', 'mc16d', 'mc16e']:

    treenames = ['nominal'] + getSystTreeNames()

    for tname in treenames:
        if tname == 'nominal':
            extra_args = "-c"
        else:
            extra_args = f"--treename {tname}"

        writeJobFile(
            'ttbar',
            dataset_detNP_config,
            outdir = os.path.join(topoutdir,'detNP',f'ttbar_{tname}',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get('ttbar', 1),
            extra_args = extra_args,
            **common_args
        )

# MC backgrounds
for bkg in ['VV', 'singleTop', 'ttH', 'ttV']:
    for era in ['mc16a', 'mc16d', 'mc16e']:
        treenames = ['nominal'] + getSystTreeNames()
        for tname in treenames:
            writeJobFile(
                bkg,
                dataset_detNP_config,
                outdir = os.path.join(topoutdir,'detNP',f'{bkg}_{tname}',f'{era}'),
                subcampaigns = [era],
                njobs = njobs_dict.get(bkg, 1),
                extra_args = f"--treename {tname}",
                **common_args
            )

######
# With SF systematics and CR loose selection
dataset_systCRL_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_systCRL.yaml')

for sample in ['ttbar', 'VV', 'Wjets', 'Zjets', 'singleTop', 'ttH', 'ttV']:
    for era in ['mc16a', 'mc16d', 'mc16e']:
        writeJobFile(
            sample,
            dataset_systCRL_config,
            outdir = os.path.join(topoutdir,'systCRL',f'{sample}_nominal',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton' if sample=='ttbar' else '',
            njobs = njobs_dict.get(sample, 1),
            **common_args
        )

######
# MC weights and alternative samples
dataset_mcWAlt_config = os.path.join(
    os.getenv('SourceDIR'), 'configs/datasets/ttdiffxs361/datasets_mcWAlt.yaml')

# ttbar
for signal in ['ttbar', 'ttbar_amc', 'ttbar_hdamp', 'ttbar_hw', 'ttbar_mt169', 'ttbar_mt176', 'ttbar_sh']:
    for era in ['mc16a', 'mc16d', 'mc16e']:
        writeJobFile(
            signal,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir,'mcWAlt',f'{signal}_nominal',f'{era}'),
            subcampaigns = [era],
            truth_level = 'parton',
            njobs = njobs_dict.get(signal, 1),
            **common_args
        )

# MC backgrounds
for bkg in ['VV', 'VV_syst', 'singleTop', 'singleTop_DS', 'singleTop_amc', 'singleTop_hw', 'ttH', 'ttV', 'ttV_syst']:
    for era in ['mc16a', 'mc16d', 'mc16e']:
        writeJobFile(
            bkg,
            dataset_mcWAlt_config,
            outdir = os.path.join(topoutdir, 'mcWAlt', f'{bkg}_nominal',f'{era}'),
            subcampaigns = [era],
            njobs = njobs_dict.get(bkg, 1),
            **common_args
        )
