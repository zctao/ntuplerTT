#!/usr/bin/env python3
import os
import tracemalloc

from ntupler import matchAndSplitTrees
from datasets import getInputFileNames, read_config
from acceptance import computeAccEffCorrections

import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-r', '--reco-files', required=True, nargs='+', type=str,
                    help="Input root files containing reco trees")
#
# either parton level or particle level input files, but not both
mgroup = parser.add_mutually_exclusive_group()
mgroup.add_argument('-t', '--parton-files', nargs='+', type=str,
                    help="Input root files containing parton level trees")
mgroup.add_argument('-p', '--particle-files', nargs='+', type=str,
                    help="Input root files containing particle level trees")
#
parser.add_argument('-w', '--sumweight-config', type=str,
                    help="Config file to read sum weight from")
parser.add_argument('-o', '--outdir', default='.',
                    help="Output directory")
parser.add_argument('-n', '--name', type=str, default='ntuple',
                    help="Prefix of the output file names")
parser.add_argument('-m', '--maxevents', type=int,
                    help="Max number of events to process")
parser.add_argument('-c', '--compute-corrections', action='store_true',
                    help="Compute acceptance and efficiency correction factors")
parser.add_argument('-a', '--algorithm-topreco',
                    choices=['pseudotop', 'klfitter'], default='pseudotop',
                    help="Top reconstruction algorithm")
parser.add_argument('--treename', type=str, default='nominal',
                    help="Tree name of reco level input")

args = parser.parse_args()

# get input files
inputFiles_reco = getInputFileNames(args.reco_files)
if args.reco_files:
    print(f"Get reco input files from {args.reco_files}")

if args.sumweight_config:
    print(f"Get sum weights map from {args.sumweight_config}")
    sumw_dict = read_config(args.sumweight_config)
else:
    sumw_dict = None

if args.parton_files:
    # parton level
    print(f"Get parton level input files from {args.parton_files}")
    inputFiles_mctruth = getInputFileNames(args.parton_files)
    truth_level = 'parton'
elif args.particle_files:
    # particle level
    print(f"Get particle level input files from {args.particle_files}")
    inputFiles_mctruth = getInputFileNames(args.particle_files)
    truth_level = 'particle'
else:
    # reco only
    inputFiles_mctruth = []
    truth_level = ''

# output directory
if not os.path.isdir(args.outdir):
    print("Create output directory: {}".format(args.outdir))
    os.makedirs(args.outdir)

assert(len(inputFiles_reco) > 0)

# start processing
tracemalloc.start()

matchAndSplitTrees(
    os.path.join(args.outdir, args.name),
    inputFiles_reco,
    inputFiles_mctruth,
    sumWeights_dict = sumw_dict,
    recoAlgo = args.algorithm_topreco,
    truthLevel = truth_level,
    treename = args.treename,
    saveUnmatchedReco = True,
    saveUnmatchedTruth = truth_level=='particle', # TODO: check this
    maxevents = args.maxevents
)

mcurrent, mpeak = tracemalloc.get_traced_memory()
print(f"Current memory usage is {mcurrent*1e-6:.1f} MB; Peak was {mpeak*1e-6:.1f} MB")

if inputFiles_mctruth and args.compute_corrections:
    computeAccEffCorrections(
        os.path.join(args.outdir, args.name),
        inputFiles_reco,
        inputFiles_mctruth,
        recoAlgo = args.algorithm_topreco,
        truthLevel = truth_level
    )

    mcurrent, mpeak = tracemalloc.get_traced_memory()
    print(f"Current memory usage is {mcurrent*1e-6:.1f} MB; Peak was {mpeak*1e-6:.1f} MB")
