import os
import time
import numpy as np

from ROOT import TChain, TTree, TFile

from extra_variables import varsExtra
import selections as sel

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def buildTreeIndex(tree):
    tstart = time.time()
    status = tree.BuildIndex('runNumber', 'eventNumber')
    tdone = time.time()

    # A return code less than 0 indicates failure.
    if status < 0:
        raise RuntimeError(f"Could not build index for tree {tree.GetName()}")
    else:
        logger.info(f"Building index took {tdone-tstart:.2f} seconds")

    return tree

def buildHashMapFromTTree(tree, check_duplicate=False, fname_eventID=None):
    # build a dictionary using ('runNumber', 'eventNumber') as the key and the index as the value
    # also try to look for duplicated event IDs if check_duplicate is True
    tstart = time.time()

    hmap = dict()
    duplicates = set()

    nentries = tree.GetEntries()
    progress_mark = 0.1

    for i, ev in enumerate(tree):
        # print progress
        if i >= (nentries-1) * progress_mark:
            logger.info(f"processing {i}/{nentries}")
            progress_mark += 0.1

        # key for hmap
        key = (getattr(ev, 'runNumber'), getattr(ev, 'eventNumber'))

        if check_duplicate and key in hmap:
            # this is a duplicate
            duplicates.add(key)
        else:
            # add this event index to hmap
            hmap[key] = i

    # Remove duplicate events from the map if there are any
    for dk in duplicates:
        hmap.pop(dk)

    tdone = time.time()

    logger.info(f"Build index: {tdone-tstart:.2f} seconds")
    if check_duplicate:
        logger.info(f"Found {len(duplicates)} duplicated event IDs")

        if len(duplicates) > 0 and fname_eventID:
            # write the duplicate event IDs to a file
            logger.info(f"Write duplicate event IDs to {fname_eventID}")
            with open(fname_eventID, 'w') as fid:
                #fid.write(f"{keys}\n")
                for dk in duplicates:
                    fid.write(" ".join(str(x) for x in dk) + "\n")

    return hmap, duplicates

def prepareOutputTree(input_tree, new_name, extra_branches=[]):
    newtree = input_tree.CloneTree(0)
    newtree.SetName(new_name)

    # add extra branches
    for branch_args in extra_branches:
        newtree.Branch(branch_args[0], branch_args[1], branch_args[2])

    return newtree

def getSumWeights(infiles_sumw):
    tree_sumw = TChain('sumWeights')
    for fsumw in infiles_sumw:
        tree_sumw.Add(fsumw)

    sumw = 0
    for evt in tree_sumw:
        sumw += evt.totalEventsWeighted

    return sumw

def getPrefixReco(recoAlgo):
    # prefix of variable names
    if recoAlgo.lower() == 'klfitter':
        # KLFitter
        prefix_thad = "klfitter_bestPerm_topHad"
        prefix_tlep = "klfitter_bestPerm_topLep"
        prefix_ttbar = "klfitter_bestPerm_ttbar"
    elif recoAlgo.lower() == 'pseudotop':
        # PseudoTop
        prefix_thad = "PseudoTop_Reco_top_had"
        prefix_tlep = "PseudoTop_Reco_top_lep"
        prefix_ttbar = "PseudoTop_Reco_ttbar"
    else:
        raise RuntimeError(f"Unknown top reconstruction algorithm {recoAlgo}")

    return prefix_thad, prefix_tlep, prefix_ttbar

def getPrefixTruth(truthLevel):
    # prefix of variable names
    if truthLevel == "parton":
        prefix_thad = "MC_thad_afterFSR"
        prefix_tlep = "MC_tlep_afterFSR"
        prefix_ttbar = "MC_ttbar_afterFSR"
    elif truthLevel == "particle":
        prefix_thad = "PseudoTop_Particle_top_had"
        prefix_tlep = "PseudoTop_Particle_top_lep"
        prefix_ttbar = "PseudoTop_Particle_ttbar"
    else:
        raise RuntimeError(f"Unknown truth level {truthLevel}")

    return prefix_thad, prefix_tlep, prefix_ttbar

def matchAndSplitTrees(
        outputName,
        inputFiles_reco,
        inputFiles_truth=[],
        sumWeights_dict = None,
        recoAlgo = 'klfitter', # ttbar reconstruction algorithm
        truthLevel ='parton',
        treename='nominal',
        saveUnmatchedReco=True, saveUnmatchedTruth=True,
        maxevents=None,
        checkDuplicate=False
    ):
    logger.info("Start processing mini-ntuples")

    ##########
    logger.info("Read input trees and build index")
    # Reco
    logger.info("Reco level")
    tree_reco = TChain(treename)
    for infile_reco in inputFiles_reco:
        tree_reco.Add(infile_reco)
    nevents_reco = tree_reco.GetEntries()
    logger.info(f"Number of events in the reco tree: {nevents_reco}")

    if checkDuplicate:
        logger.info(f"Build index hash table for reco tree")
        index_reco, dup_reco = buildHashMapFromTTree(
            tree_reco,
            check_duplicate=True,
            fname_eventID=f"{outputName}_duplicate_eventID_reco.txt"
            )
        assert(index_reco)
    else:
        # No need to build tree index now if not check duplicated event ID
        index_reco = dict()
        dup_reco = set()

    # MC truth level
    if inputFiles_truth:
        logger.info(truthLevel.capitalize()+" level")
        tree_truth = TChain('nominal') # truth level tree is always 'nominal'
        for infile_truth in inputFiles_truth:
            tree_truth.Add(infile_truth)
        nevents_truth = tree_truth.GetEntries()
        logger.info(f"Number of events in the truth tree: {nevents_truth}")

#        try:
#            buildTreeIndex(tree_truth)
#        except RuntimeError as err:
#            logger.info(f"Failed to build index for truth level trees: {err}")
#            return

        logger.info(f"Build index hash table for truth tree")
        index_truth, dup_truth = buildHashMapFromTTree(
            tree_truth,
            check_duplicate=checkDuplicate,
            fname_eventID=f"{outputName}_duplicate_eventID_truth.txt"
            )
        assert(index_truth)
    else:
        tree_truth = None
        index_truth = dict()
        dup_truth = set()

    ##########
    # Output trees
    logger.info("Create output trees")

    # output file name prefix
    foutname_prefix = f"{outputName}_{recoAlgo}"
    if tree_truth is not None:
        foutname_prefix += f"_{truthLevel}"

    #####
    # e+jets
    outfile_ej = TFile(foutname_prefix+"_ejets.root", "recreate")
    logger.info(f"Create output file: {outfile_ej.GetName()}")

    # reco
    newtree_reco_ej = prepareOutputTree(tree_reco, 'reco')

    # add extra branches
    extra_variables_reco_ej = varsExtra(
        *getPrefixReco(recoAlgo), compute_energy=True,
        sum_weights_map = sumWeights_dict
        )
    extra_variables_reco_ej.set_up_branches(newtree_reco_ej)

    # truth
    if tree_truth is not None:
        newtree_truth_ej = prepareOutputTree(tree_truth, truthLevel)

        # add extra branches
        extra_variables_truth_ej = varsExtra(
            *getPrefixTruth(truthLevel), compute_energy = truthLevel!="parton",
            sum_weights_map = sumWeights_dict, is_reco=False
            )
        extra_variables_truth_ej.set_up_branches(newtree_truth_ej)
    else:
        extra_variables_truth_ej = None
        newtree_truth_ej = None

    #####
    # mu+jets
    outfile_mj = TFile(foutname_prefix+"_mjets.root", "recreate")
    logger.info(f"Create output file: {outfile_mj.GetName()}")

    # reco
    newtree_reco_mj = prepareOutputTree(tree_reco, 'reco')

    # add extra branches
    extra_variables_reco_mj = varsExtra(
        *getPrefixReco(recoAlgo), compute_energy=True,
        sum_weights_map = sumWeights_dict
        )
    extra_variables_reco_mj.set_up_branches(newtree_reco_mj)

    # truth
    if tree_truth is not None:
        newtree_truth_mj = prepareOutputTree(tree_truth, truthLevel)

        # add extra branches
        extra_variables_truth_mj = varsExtra(
            *getPrefixTruth(truthLevel), compute_energy = truthLevel!="parton",
            sum_weights_map = sumWeights_dict, is_reco=False
            )
        extra_variables_truth_mj.set_up_branches(newtree_truth_mj)
    else:
        extra_variables_truth_mj = None
        newtree_truth_mj = None

    ##########
    logger.info("Iterate through events in reco trees")

    tstart = time.time()

    for i in range(nevents_reco):
        if maxevents is not None:
            if i > maxevents:
                break

        if not i%10000:
            logger.info(f"processing event #{i}")
        tree_reco.GetEntry(i)

        # event ID
        eventID = (tree_reco.runNumber, tree_reco.eventNumber)

        if eventID in dup_reco or eventID in dup_truth:
            # this is an event with duplicated event ID
            continue

        # reco-level selections
        if not sel.passRecoSelections(tree_reco, recoAlgo):
            continue

        passEJets = sel.passRecoSelections_ejets(tree_reco)
        passMJets = sel.passRecoSelections_mjets(tree_reco)

        # sanity check: should pass one and only one of the selections
        if not ( bool(passEJets) ^ bool(passMJets) ):
            logger.info(f"WARNING! event {i}: passEJets = {passEJets} passMJets = {passMJets}")
            continue

        # point to the extra variables and output trees for the right channel
        if passEJets:
            extra_vars_reco = extra_variables_reco_ej
            extra_vars_truth = extra_variables_truth_ej
            newtree_reco = newtree_reco_ej
            newtree_truth = newtree_truth_ej
        else: # passMJets
            extra_vars_reco = extra_variables_reco_mj
            extra_vars_truth = extra_variables_truth_mj
            newtree_reco = newtree_reco_mj
            newtree_truth = newtree_truth_mj

        # try to find the matched event in truth tree
        isTruthMatched = False

        if tree_truth is not None:
#            truth_entry = tree_truth.GetEntryNumberWithIndex(*eventID)
            truth_entry = index_truth.get(eventID, -1)
            tree_truth.GetEntry(truth_entry)

            if truth_entry >= 0:
                # found a matched truth-level event
                # check if the matched event satisfies truth-level requirements
                if truthLevel == 'parton':
                    # check if it is semi-leptonic ttbar
                    #isTruthMatched = tree_reco.isTruthSemileptonic
                    # instead of trusting the flag in tree_reco, check tree_truth
                    isTruthMatched = sel.isSemiLeptonicTTbar(tree_truth)
                elif truthLevel == 'particle':
                    # check if passing the particle level selections
                    isTruthMatched = sel.passPLSelections(tree_truth)

            if isTruthMatched:
                extra_vars_truth.write_event(tree_truth)
                extra_vars_truth.set_dummy_flag(0)
                extra_vars_truth.set_match_flag(1)
            else:
                # no matched truth event or the truth event fails selections
                extra_vars_truth.write_event(tree_truth)
                extra_vars_truth.set_dummy_flag(1)
                extra_vars_truth.set_match_flag(0)

        extra_vars_reco.write_event(tree_reco)
        extra_vars_reco.set_dummy_flag(0)
        extra_vars_reco.set_match_flag(isTruthMatched)

        # fill the new tree
        if tree_truth is None:
            # truth matching not possible, just fill the new reco tree
            newtree_reco.Fill()
        else:
            if isTruthMatched or saveUnmatchedReco:
                # fill the new reco and truth tree
                newtree_reco.Fill()
                newtree_truth.Fill()

    # end of tree_reco loop

    tdone = time.time()
    logger.info(f"Processing all reco events took {tdone-tstart:.2f} seconds ({(tdone-tstart)/nevents_reco:.5f} seconds/event)")

    ##########
    # truth tree
    if saveUnmatchedTruth and tree_truth is not None:
        # build reco tree index if this has not been done already
#        try:
#            buildTreeIndex(tree_reco)
#        except RuntimeError as err:
#            logger.info(f"Failed to build index for reco level trees: {err}")
#            return

        if not index_reco:
            logger.info(f"Build index hash table for reco tree")
            index_reco, dup_reco = buildHashMapFromTTree(
                tree_reco,
                check_duplicate=checkDuplicate,
                fname_eventID=f"{outputName}_duplicate_eventID_reco.txt"
                )
            assert(index_reco)

        logger.info("Iterate through events in truth trees")

        # append unmatched truth events
        tstart = time.time()
        for j in range(nevents_truth):
            if maxevents is not None:
                if j > maxevents:
                    break

            if not j%10000:
                logger.info(f"processing {truthLevel} event {j}")

            tree_truth.GetEntry(j)

            eventID_truth = (tree_truth.runNumber, tree_truth.eventNumber)
            if eventID_truth in dup_truth or eventID_truth in dup_reco:
                continue

            # truth-level selections
            passTruthSel = False
            if truthLevel=='parton':
                passTruthSel = sel.isSemiLeptonicTTbar(tree_truth)
            elif truthLevel=='particle':
                passTruthSel = sel.passPLSelections(tree_truth)

            if not passTruthSel:
                continue

            # try getting the matched reco event
#            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)
            reco_entry = index_reco.get(eventID_truth, -1)

            if reco_entry >= 0:
                # found a matched reco-level event
                tree_reco.GetEntry(reco_entry)

                # check if it passed the reco-level selection
                if sel.passRecoSelections(tree_reco, recoAlgo):
                    # this event has already been included in the reco tree loop
                    # skip
                    continue

            passEJets = sel.passTruthSelections_ejets(tree_truth)
            passMJets = sel.passTruthSelections_mjets(tree_truth)

            if passEJets:
                extra_vars_reco = extra_variables_reco_ej
                extra_vars_truth = extra_variables_truth_ej
                newtree_reco = newtree_reco_ej
                newtree_truth = newtree_truth_ej
            elif passMJets:
                extra_vars_reco = extra_variables_reco_mj
                extra_vars_truth = extra_variables_truth_mj
                newtree_reco = newtree_reco_mj
                newtree_truth = newtree_truth_mj
            else:
                # do not know tau decay products, skip for now
                continue

            extra_vars_truth.write_event(tree_truth)
            extra_vars_truth.set_match_flag(0)
            extra_vars_truth.set_dummy_flag(0)

            newtree_truth.Fill()

            # fill reco tree with dummy events
            # get a random event from the reco tree
            #ireco = np.random.randint(0, nevents_reco-1) # too slow
            ireco = -1
            tree_reco.GetEntry(ireco)

            extra_vars_reco.write_event(tree_reco)
            extra_vars_reco.set_match_flag(0)
            extra_vars_reco.set_dummy_flag(1)
            newtree_reco.Fill()

        # end of tree_truth loop

        tdone = time.time()
        logger.info(f"Processing all truth events took {tdone-tstart:.2f} seconds ({(tdone-tstart)/nevents_truth:.5f} seconds/event)")

    # new reco and truth trees should be of the same length
    #if newtree_truth_ej is not None:
    #    assert(newtree_reco_ej.GetEntries() == newtree_truth_ej.GetEntries())
    #if newtree_truth_mj is not None:
    #    assert(newtree_reco_mj.GetEntries() == newtree_truth_mj.GetEntries())

    # Write and close output files
    outfile_ej.Write()
    outfile_ej.Close()

    outfile_mj.Write()
    outfile_mj.Close()
