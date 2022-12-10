#!/usr/bin/env python3
import os
import tracemalloc

from ntupler import Ntupler
from datasets import getInputFileNames, read_config
from acceptance import computeAccEffCorrections

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

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
parser.add_argument('-d', '--duplicate-removal', action='store_true',
                    help="If True, check for events with duplicated event IDs and remove them")
parser.add_argument('--treename', type=str, default='nominal',
                    help="Tree name of reco level input")
parser.add_argument('-v', '--verbose', action='store_true',
                    help="If True, set logging level to DEBUG, otherwise INFO")

args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# get input files
inputFiles_reco = getInputFileNames(args.reco_files)
if args.reco_files:
    logger.info(f"Get reco input files from {args.reco_files}")

if args.sumweight_config:
    logger.info(f"Get sum weights map from {args.sumweight_config}")
    sumw_dict = read_config(args.sumweight_config)
else:
    sumw_dict = None

if args.parton_files:
    # parton level
    logger.info(f"Get parton level input files from {args.parton_files}")
    inputFiles_mctruth = getInputFileNames(args.parton_files)
    truth_level = 'parton'
elif args.particle_files:
    # particle level
    logger.info(f"Get particle level input files from {args.particle_files}")
    inputFiles_mctruth = getInputFileNames(args.particle_files)
    truth_level = 'particle'
else:
    # reco only
    inputFiles_mctruth = []
    truth_level = ''

# output directory
if not os.path.isdir(args.outdir):
    logger.info("Create output directory: {}".format(args.outdir))
    os.makedirs(args.outdir)

assert(len(inputFiles_reco) > 0)

# start processing
tracemalloc.start()

ntupler = Ntupler(
    os.path.join(args.outdir, args.name),
    inputFiles_reco,
    inputFiles_mctruth,
    sumWeights_dict = sumw_dict,
    recoAlgo = args.algorithm_topreco,
    truthLevel = truth_level,
    treename = args.treename,
    makeHistograms = args.compute_corrections
)

# run
ntupler(
    maxevents = args.maxevents,
    saveUnmatchedReco = True,
    saveUnmatchedTruth = truth_level=='particle', # TODO: check this
    checkDuplicate = args.duplicate_removal
)

mcurrent, mpeak = tracemalloc.get_traced_memory()
logger.debug(f"Current memory usage is {mcurrent*1e-6:.1f} MB; Peak was {mpeak*1e-6:.1f} MB")
