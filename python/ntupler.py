import os
import time
import numpy as np
from ROOT import TChain, TTree, TFile
from extra_variables import varsExtra

def buildTreeIndex(tree):
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

def passSelection_ejets(tree):
    if hasattr(tree, 'passed_resolved_ejets_4j2b'):
        # reco or particle level tree
        return tree.passed_resolved_ejets_4j2b
    elif hasattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid'):
        # parton tree
        decayIDs = [abs(getattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay1_from_t_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_t_afterFSR_pdgid'))]
        if 11 in decayIDs:
            return True
        else:
            return False
    # for backward compatibility with old ntuple files
    elif hasattr(tree, 'lep_pdgid'):
        return abs(tree.lep_pdgid) == 11
    return False

def passSelection_mjets(tree):
    if hasattr(tree, 'passed_resolved_mujets_4j2b'):
        # reco or particle level tree
        return tree.passed_resolved_mujets_4j2b
    elif hasattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid'):
        # parton tree
        decayIDs = [abs(getattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay1_from_t_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_t_afterFSR_pdgid'))]
        if 13 in decayIDs:
            return True
        else:
            return False
    # for backward compatibility with old ntuple files
    elif hasattr(tree, 'lep_pdgid'):
        return abs(tree.lep_pdgid) == 13
    else:
        return False

def getSumWeights(infiles_sumw):
    tree_sumw = TChain('sumWeights')
    for fsumw in infiles_sumw:
        tree_sumw.Add(fsumw)

    sumw = 0
    for evt in tree_sumw:
        sumw += evt.totalEventsWeighted

    return sumw

def matchAndSplitTrees(
        outputName,
        inputFiles_reco,
        inputFiles_truth=[],
        inputFiles_sumw=[],
        recoAlgo = 'klfitter', # ttbar reconstruction algorithm
        truthLevel ='parton',
        treename='nominal',
        saveUnmatchedReco=True, saveUnmatchedTruth=True,
        maxevents=None
    ):

    ##########
    print("Read input trees and build index")
    # Reco
    print("Reco level")
    tree_reco = TChain(treename)
    for infile_reco in inputFiles_reco:
        tree_reco.Add(infile_reco)
    nevents_reco = tree_reco.GetEntries()
    print("Number of events in the reco tree: {}".format(nevents_reco))

    try:
        buildTreeIndex(tree_reco)
    except RuntimeError as err:
        print("Failed to build index for reco level trees: {}".format(err))
        return

    # MC truth level
    if inputFiles_truth:
        print(truthLevel.capitalize()+" level")
        tree_truth = TChain(treename)
        for infile_truth in inputFiles_truth:
            tree_truth.Add(infile_truth)
        nevents_truth = tree_truth.GetEntries()
        print("Number of events in the truth tree: {}".format(nevents_truth))

        try:
            buildTreeIndex(tree_truth)
        except RuntimeError as err:
            print("Failed to build index for truth level trees: {}".format(err))
            return
    else:
        tree_truth = None

    # Sum weights
    if inputFiles_sumw:
        print("Read sumWeights")
        sumWeights = getSumWeights(inputFiles_sumw)
        print("sum weights = ", sumWeights)
    else:
        sumWeights = None

    ##########
    # Output trees
    print("Create output trees")
    #####
    # reco branches
    if recoAlgo.lower() == 'klfitter':
        # KLFitter
        reco_prefix_thad = "klfitter_bestPerm_topHad"
        reco_prefix_tlep = "klfitter_bestPerm_topLep"
        reco_prefix_ttbar = "klfitter_bestPerm_ttbar"
    elif recoAlgo.lower() == 'pseudotop':
        # PseudoTop
        reco_prefix_thad = "PseudoTop_Reco_top_had"
        reco_prefix_tlep = "PseudoTop_Reco_top_lep"
        reco_prefix_ttbar = "PseudoTop_Reco_ttbar"
    else:
        print("Unknown top reconstruction algorithm: {}".format(recoAlgo))
        return

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
    if tree_truth is not None:
        extra_variables_truth_ej = varsExtra(
            truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar,
            compute_energy = truthLevel!="parton"
        )

        newtree_truth_ej = prepareOutputTree(tree_truth, truthLevel)
        extra_variables_truth_ej.set_up_branches(newtree_truth_ej)
    else:
        extra_variables_truth_ej = None
        newtree_truth_ej = None

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
    if tree_truth is not None:
        extra_variables_truth_mj = varsExtra(
            truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar,
            compute_energy = truthLevel!="parton"
        )

        newtree_truth_mj = prepareOutputTree(tree_truth, truthLevel)
        extra_variables_truth_mj.set_up_branches(newtree_truth_mj)
    else:
        extra_variables_truth_mj = None
        newtree_truth_mj = None

    ##########
    print("Iterate through events in reco trees")
    unmatched_reco_entries = []

    for i in range(tree_reco.GetEntries()):
        if maxevents is not None:
            if i > maxevents:
                break

        if not i%10000:
            print("processing event #{}".format(i))
        tree_reco.GetEntry(i)

        # event selections
        passEJets = passSelection_ejets(tree_reco)
        passMJets = passSelection_mjets(tree_reco)

        # sanity check: should pass one and only one of the selections
        if not ( bool(passEJets) ^ bool(passMJets) ):
            print("WARNING! event {}: passEJets = {} passMJets = {}".format(i, passEJets, passMJets))
            continue

        ####
        isTruthMatched = False
        if tree_truth is not None:
            # try to get the truth level event that matches this reco event
            eventID = (tree_reco.runNumber, tree_reco.eventNumber)
            truth_entry = tree_truth.GetEntryNumberWithIndex(*eventID)
            if truth_entry >= 0:
                # found matched truth event
                isTruthMatched = True
            else:
                # no matched truth event found
                unmatched_reco_entries.append(i)
                # skip for now
                continue

        # write reco events
        # fill the new trees
        if passEJets:
            extra_variables_reco_ej.set_match_flag(isTruthMatched)
            extra_variables_reco_ej.set_dummy_flag(0)
            extra_variables_reco_ej.write_event(tree_reco)
            newtree_reco_ej.Fill()
        elif passMJets:
            extra_variables_reco_mj.set_match_flag(isTruthMatched)
            extra_variables_reco_mj.set_dummy_flag(0)
            extra_variables_reco_mj.write_event(tree_reco)
            newtree_reco_mj.Fill()

        if tree_truth is not None:
            # write matched truth event
            tree_truth.GetEntry(truth_entry)
            if passEJets:
                extra_variables_truth_ej.set_match_flag(1)
                extra_variables_truth_ej.set_dummy_flag(0)
                extra_variables_truth_ej.write_event(tree_truth)
                newtree_truth_ej.Fill()
            elif passMJets:
                extra_variables_truth_mj.set_match_flag(1)
                extra_variables_truth_mj.set_dummy_flag(0)
                extra_variables_truth_mj.write_event(tree_truth)
                newtree_truth_mj.Fill()
    # end of tree_reco loop

    if saveUnmatchedReco and tree_truth is not None:
        # append unmatched reco events
        print("Append unmatched reco events")
        for ievt, ireco_unmatched in enumerate(unmatched_reco_entries):
            if maxevents is not None:
                if ievt > maxevents:
                    break

            if not ievt%10000:
                print("processing unmatched reco event {}".format(ievt))

            tree_reco.GetEntry(ireco_unmatched)

            passEJets = passSelection_ejets(tree_reco)
            passMJets = passSelection_mjets(tree_reco)

            if passEJets:
                extra_variables_reco_ej.set_match_flag(0)
                extra_variables_reco_ej.set_dummy_flag(0)
                extra_variables_reco_ej.write_event(tree_reco)
                newtree_reco_ej.Fill()
            elif passMJets:
                extra_variables_reco_mj.set_match_flag(0)
                extra_variables_reco_mj.set_dummy_flag(0)
                extra_variables_reco_mj.write_event(tree_reco)
                newtree_reco_mj.Fill()

            # fill truth tree with dummy events
            # get a random event from the truth tree
            #itruth = np.random.randint(0,nevents_truth-1) # too slow
            itruth = -1
            tree_truth.GetEntry(itruth)
            if passEJets:
                extra_variables_truth_ej.set_match_flag(0)
                extra_variables_truth_ej.set_dummy_flag(1)
                extra_variables_truth_ej.write_event(tree_truth)
                newtree_truth_ej.Fill()
            elif passMJets:
                extra_variables_truth_mj.set_match_flag(0)
                extra_variables_truth_mj.set_dummy_flag(1)
                extra_variables_truth_mj.write_event(tree_truth)
                newtree_truth_mj.Fill()

    if saveUnmatchedTruth and tree_truth is not None:
        # append unmatched truth events
        print("Append unmatched {} events".format(truthLevel))
        for j in range(tree_truth.GetEntries()):
            if maxevents is not None:
                if j > maxevents:
                    break

            if not j%10000:
                print("processing {} event {}".format(truthLevel, j))

            tree_truth.GetEntry(j)
            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)

            if reco_entry >= 0:
                # found matched reco event.
                # skip since it has already been written.
                continue

            passEJets = passSelection_ejets(tree_truth)
            passMJets = passSelection_mjets(tree_truth)
            if passEJets:
                extra_variables_truth_ej.set_match_flag(0)
                extra_variables_truth_ej.set_dummy_flag(0)
                extra_variables_truth_ej.write_event(tree_truth)
                newtree_truth_ej.Fill()
            elif passMJets:
                extra_variables_truth_mj.set_match_flag(0)
                extra_variables_truth_mj.set_dummy_flag(0)
                extra_variables_truth_mj.write_event(tree_truth)
                newtree_truth_mj.Fill()

            # fill reco tree with dummy events
            # get a random event from the reco tree
            #ireco = np.random.randint(0, nevents_reco-1) # too slow
            ireco = -1
            tree_reco.GetEntry(ireco)
            if passEJets:
                extra_variables_reco_ej.set_match_flag(0)
                extra_variables_reco_ej.set_dummy_flag(1)
                extra_variables_reco_ej.write_event(tree_reco)
                newtree_reco_ej.Fill()
            elif passMJets:
                extra_variables_reco_mj.set_match_flag(0)
                extra_variables_reco_mj.set_dummy_flag(1)
                extra_variables_reco_mj.write_event(tree_reco)
                newtree_reco_mj.Fill()

    # new reco and truth trees should be of the same length
    if newtree_truth_ej is not None:
        assert(newtree_reco_ej.GetEntries() == newtree_truth_ej.GetEntries())
    if newtree_truth_mj is not None:
        assert(newtree_reco_mj.GetEntries() == newtree_truth_mj.GetEntries())

    # Write and close output files
    outfile_ej.Write()
    outfile_ej.Close()

    outfile_mj.Write()
    outfile_mj.Close()
