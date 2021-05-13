import os
import time
import tracemalloc

from ROOT import TChain, TFile

from extra_variables import varsExtra

def getTrees(infiles, treename, buildIndex=True):
    # read trees into TChain
    tree = TChain(treename)
    for infile in infiles:
        tree.Add(infile)

    # build index
    if buildIndex:
        tstart = time.time()
        status = tree.BuildIndex('runNumber', 'eventNumber')
        tdone = time.time()

        # A return code less than 0 indicates failure.
        if status < 0:
            raise RuntimeError("Could not build index for tree {}".format(treename))
        else:
            print("Building index took {:.2f} seconds".format(tdone-tstart))

    return tree

def prepareOutputTree(input_tree, new_name, extra_branches=[]):
    newtree = input_tree.CloneTree(0)
    newtree.SetName(new_name)

    # add extra branches
    for branch_args in extra_branches:
        newtree.Branch(branch_args[0], branch_args[1], branch_args[2])

    return newtree

def isEJets(tree):
    if hasattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid'):
        # parton tree
        decayIDs = [abs(getattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay1_from_t_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_t_afterFSR_pdgid'))]
        if 11 in decayIDs:
            return True
        elif 13 in decayIDs:
            return False
        else:
            # arbitrarily assign it to a category
            return tree.eventNumber%2

    elif hasattr(tree, 'lep_pdgid'):
        if abs(tree.lep_pdgid) == 11:
            return True
        elif abs(tree.lep_pdgid) == 13:
            return False
        else:
            # arbitrarily assign it to a category
            return tree.eventNumber%2

    # cannot decide which category this event is
    # arbitrarily assign it to one
    return tree.eventNumber%2

def getSumWeights(tree_sumw):
    sumw = 0
    for w in tree_sumw:
        sumw += w.totalEventsWeighted

    return sumw

def matchAndSplitTrees(inputFiles_reco, inputFiles_truth, inputFiles_sumw, outputName, truthLevel ='parton', treename='nominal', saveUnmatchedReco=True, saveUnmatchedTruth=True):

    ##########
    print("Read input trees and build index")
    # Reco
    print("Reco level")
    try:
        tree_reco = getTrees(inputFiles_reco, treename, True)
    except RuntimeError as err:
        #tree_reco = None
        print("Failed to get reco level trees: {}".format(err))
        return

    # MC truth level
    print(truthLevel.capitalize()+" level")
    try:
        tree_truth = getTrees(inputFiles_truth, treename, True)
    except RuntimeError as err:
        print("Failed to get parton level trees: {}".format(err))
        return

    # Sum weights
    print("Read sumWeights")
    try:
        tree_sumw = getTrees(inputFiles_sumw, 'sumWeights', False)
    except RuntimeError as err:
        print("Failed to get sumWeights: {}".format(err))
        return

    sumWeights = getSumWeights(tree_sumw)

    ##########
    # Output trees
    print("Create output trees")
    #####
    # reco branches
    if truthLevel == "parton":
        reco_prefix_thad = "klfitter_bestPerm_topHad"
        reco_prefix_tlep = "klfitter_bestPerm_topLep"
        reco_prefix_ttbar = "klfitter_bestPerm_ttbar"
    else: # particle level
        reco_prefix_thad = "PseudoTop_Reco_top_had"
        reco_prefix_tlep = "PseudoTop_Reco_top_lep"
        reco_prefix_ttbar = "PseudoTop_Reco_ttbar"

    # truth branches
    if truthLevel == "parton":
        truth_prefix_thad = "MC_thad_afterFSR"
        truth_prefix_tlep = "MC_tlep_afterFSR"
        truth_prefix_ttbar = "MC_ttbar_afterFSR"
    else: # particle levels
        truth_prefix_thad = "PseudoTop_Particle_top_had"
        truth_prefix_tlep = "PseudoTop_Particle_top_lep"
        truth_prefix_ttbar = "PseudoTop_Particle_ttbar"

    #####
    # e+jets
    outfile_ej = TFile('{}_{}_ejets.root'.format(outputName, truthLevel), 'recreate')
    print("Create output file: {}".format(outfile_ej.GetName()))

    # add extra branches
    # reco
    extra_variables_reco_ej = varsExtra(
        reco_prefix_thad, reco_prefix_tlep, reco_prefix_ttbar,
        compute_energy=True, sum_weights=sumWeights
    )

    newtree_reco_ej = prepareOutputTree(tree_reco, 'reco')
    extra_variables_reco_ej.set_up_branches(newtree_reco_ej)

    # truth
    extra_variables_truth_ej = varsExtra(
        truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar,
        compute_energy = truthLevel!="parton"
    )

    newtree_truth_ej = prepareOutputTree(tree_truth, truthLevel)
    extra_variables_truth_ej.set_up_branches(newtree_truth_ej)

    #####
    # mu+jets
    outfile_mj = TFile('{}_{}_mjets.root'.format(outputName, truthLevel), 'recreate')
    print("Create output file: {}".format(outfile_mj.GetName()))

    # add extra branches
    # reco
    extra_variables_reco_mj = varsExtra(
        reco_prefix_thad, reco_prefix_tlep, reco_prefix_ttbar,
        compute_energy=True, sum_weights=sumWeights
    )

    newtree_reco_mj = prepareOutputTree(tree_reco, 'reco')
    extra_variables_reco_mj.set_up_branches(newtree_reco_mj)

    # truth
    extra_variables_truth_mj = varsExtra(
        truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar,
        compute_energy = truthLevel!="parton"
    )

    newtree_truth_mj = prepareOutputTree(tree_truth, truthLevel)
    extra_variables_truth_mj.set_up_branches(newtree_truth_mj)

    ##########
    print("Iterate through events in reco trees")
    unmatched_reco_entries = []

    for i in range(tree_reco.GetEntries()):
        if not i%10000:
            print("processing event #{}".format(i))
        tree_reco.GetEntry(i)

        eventID = (tree_reco.runNumber, tree_reco.eventNumber)

        ####
        # try matching truth level events
        truth_entry = tree_truth.GetEntryNumberWithIndex(*eventID)
        if truth_entry < 0:
            # found no matched event
            unmatched_reco_entries.append(i)
        else:
            # found matched event
            # write reco events
            isEle = isEJets(tree_reco)
            if isEle:
                extra_variables_reco_ej.set_match_flag(1)
                newtree_reco_ej.Fill()
            else:
                extra_variables_reco_mj.set_match_flag(1)
                newtree_reco_mj.Fill()

            # write truth events
            tree_truth.GetEntry(truth_entry)
            if isEle:
                extra_variables_truth_ej.set_match_flag(1)
                newtree_truth_ej.Fill()
            else:
                extra_variables_truth_mj.set_match_flag(1)
                newtree_truth_mj.Fill()

    if saveUnmatchedReco:
        # append unmatched reco events
        print("Append unmatched reco events")
        for ievt, ireco_unmatched in enumerate(unmatched_reco_entries):
            if not ievt%10000:
                print("processing unmatched reco event {}".format(ievt))
            tree_reco.GetEntry(ireco_unmatched)
            isEle = isEJets(tree_reco)
            if isEle:
                extra_variables_reco_ej.set_match_flag(0)
                newtree_reco_ej.Fill()
            else:
                extra_variables_reco_mj.set_match_flag(0)
                newtree_reco_mj.Fill()

    if saveUnmatchedTruth:
        # append unmatched truth events
        print("Append unmatched {} events".format(truthLevel))
        for j in range(tree_truth.GetEntries()):
            if not j%10000:
                print("processing {} event {}".format(truthLevel, j))

            tree_truth.GetEntry(j)
            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)
            if reco_entry >= 0:
                # found matched reco event.
                # skip since it has already been written.
                continue

            if isEJets(tree_truth):
                extra_variables_truth_ej.set_match_flag(0)
                newtree_truth_ej.Fill()
            else:
                extra_variables_truth_mj.set_match_flag(0)
                newtree_truth_mj.Fill()

    # Write and close output files
    outfile_ej.Write()
    outfile_ej.Close()

    outfile_mj.Write()
    outfile_mj.Close()

########
#import uproot
#import numpy as np
#import time

#def buildEventIndex(events):
#    # TODO: better methods?
#    tstart = time.time()
#
#    eventIDs = events.arrays(['runNumber', 'eventNumber'])
#    indexHash = {(evtid['runNumber'], evtid['eventNumber']) : i for i, evtid in enumerate(eventIDs)}
#
#    tdone = time.time()
#    print("Building index took {:.2f} seconds".format(tdone-tstart))
#
#    return indexHash
#
#def processMiniNtuples_uproot(inputFiles_reco, inputFiles_truth, inputFiles_PL,
#                                outputname, treename = 'nominal'):
#    # WIP
#    ##########
#    print("Read input trees")
#    # for now
#    print("Reco level")
#    events_reco = uproot.open(inputFiles_reco[0]+":"treename)
#    indexMap_reco = buildEventIndex(events_reco)
#
#    print("Parton level")
#    events_truth = uproot.open(inputFiles_truth[0]+":"+treename)
#    indexMap_truth = buildEventIndex(events_truth)
#
#    print("Particle level")
#    events_PL = uproot.open(inputFiles_PL[0]+":"+treename)
#    indexMap_PL = buildEventIndex(events_PL)

def getInputFileNames(input_list):
    rootFiles = []

    for fp in input_list:
        if not os.path.isfile(fp):
            print(fp, "is not a valid file. Skip!")
            continue

        # check extension
        ext = os.path.splitext(fp)[-1].lower()
        if ext == ".root":
            rootFiles.append(fp)
        elif ext == ".txt":
            # read the list of root files in the txt
            with open(fp) as f:
                lines = f.readlines()
            lines = [l.rstrip() for l in lines]
            files = getInputFileNames(lines)
            rootFiles += files
        else:
            print("Don't know how to handle input file". fp)
            continue

    return rootFiles

if __name__ == "__main__":
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

    # check input files
    if len(args.parton_files)==0 and len(args.particle_files)==0:
        print("Neither parton or particle level truth trees are provided!")
        print("Do nothing")
        exit()

    inputFiles_reco = getInputFileNames(args.reco_files)
    inputFiles_parton = getInputFileNames(args.parton_files)
    inputFiles_particle = getInputFileNames(args.particle_files)
    inputFiles_sumw = getInputFileNames(args.sumweight_files)

    # output directory
    if not os.path.isdir(args.outdir):
        print("Create output directory: {}".format(args.outdir))
        os.makedirs(args.outdir)

    tracemalloc.start()

    if len(inputFiles_parton) > 0:
        print("Match reco and parton level events")
        tstart = time.time()
        matchAndSplitTrees(inputFiles_reco, inputFiles_parton, inputFiles_sumw,
                            outputName = os.path.join(args.outdir, args.name),
                            truthLevel = 'parton',
                            saveUnmatchedReco = True,
                            saveUnmatchedTruth = False)
        tdone = time.time()
        print("matchAndSplitTrees took {:.2f} seconds".format(tdone - tstart))

        mcurrent, mpeak = tracemalloc.get_traced_memory()
        print("Current memory usage is {:.1f} MB; Peak was {:.1f} MB".format(mcurrent * 10**-6, mpeak * 10**-6))

    if len(inputFiles_particle) > 0:
        print("Match reco and particle level events")
        tstart = time.time()
        matchAndSplitTrees(inputFiles_reco, inputFiles_particle, inputFiles_sumw,
                            outputName = os.path.join(args.outdir, args.name),
                            truthLevel = 'particle',
                            saveUnmatchedReco = True,
                            saveUnmatchedTruth = True)
        tdone = time.time()
        print("matchAndSplitTrees took {:.2f} seconds".format(tdone - tstart))

        mcurrent, mpeak = tracemalloc.get_traced_memory()
        print("Current memory usage is {:.1f} MB; Peak was {:.1f} MB".format(mcurrent * 10**-6, mpeak * 10**-6))
