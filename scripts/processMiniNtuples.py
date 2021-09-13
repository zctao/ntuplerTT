#!/usr/bin/env python3

import os
import time
import tracemalloc

from ntupler import matchAndSplitTrees
from datasets import getInputFileNames

import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-r', '--reco-files', required=True, nargs='+', type=str,
                    help="Input root files containing reco trees")
parser.add_argument('-t', '--parton-files', nargs='+', type=str,
                    help="Input root files containing parton level trees")
parser.add_argument('-p', '--particle-files', nargs='+', type=str,
                    help="Input root files containing particle level trees")
parser.add_argument('-w', '--sumweight-files', nargs='+', type=str,
                    help="Input root files containing sum weights")
parser.add_argument('-o', '--outdir', default='.',
                    help="Output directory")
parser.add_argument('-n', '--name', type=str, default='ntuple',
                    help="Suffix of the output file names")

args = parser.parse_args()

# get input files
inputFiles_reco = getInputFileNames(args.reco_files)
inputFiles_parton = getInputFileNames(args.parton_files)
inputFiles_particle = getInputFileNames(args.particle_files)
inputFiles_sumw = getInputFileNames(args.sumweight_files)

# output directory
if not os.path.isdir(args.outdir):
    print("Create output directory: {}".format(args.outdir))
    os.makedirs(args.outdir)

assert(len(inputFiles_reco) > 0)

tracemalloc.start()

if len(inputFiles_parton) == 0 and len(inputFiles_particle) == 0:
    # reco only
    print("Process reco events only")
    tstart = time.time()
    matchAndSplitTrees(
        os.path.join(args.outdir, args.name),
        inputFiles_reco, inputFiles_sumw = inputFiles_sumw
    )
else:
    if len(inputFiles_parton) > 0:
        print("Match reco and parton level events")
        tstart = time.time()
        matchAndSplitTrees(
            os.path.join(args.outdir, args.name),
            inputFiles_reco, inputFiles_parton, inputFiles_sumw,
            truthLevel = 'parton',
            saveUnmatchedReco = True,
            saveUnmatchedTruth = False
        )
        tdone = time.time()
        print("matchAndSplitTrees took {:.2f} seconds".format(tdone - tstart))

        mcurrent, mpeak = tracemalloc.get_traced_memory()
        print("Current memory usage is {:.1f} MB; Peak was {:.1f} MB".format(mcurrent * 10**-6, mpeak * 10**-6))

    if len(inputFiles_particle) > 0:
        print("Match reco and particle level events")
        tstart = time.time()
        matchAndSplitTrees(
            os.path.join(args.outdir, args.name),
            inputFiles_reco, inputFiles_particle, inputFiles_sumw,
            truthLevel = 'particle',
            saveUnmatchedReco = True,
            saveUnmatchedTruth = True
        )
        tdone = time.time()
        print("matchAndSplitTrees took {:.2f} seconds".format(tdone - tstart))

        mcurrent, mpeak = tracemalloc.get_traced_memory()
        print("Current memory usage is {:.1f} MB; Peak was {:.1f} MB".format(mcurrent * 10**-6, mpeak * 10**-6))
