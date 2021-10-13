import os
import time
import numpy as np
from ROOT import TChain, TTree, TFile
from extra_variables import varsExtra
from acceptance import CorrectionFactors
import selections as sel

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
    # e+jets
    outfile_ej = TFile('{}_{}_ejets.root'.format(outputName, truthLevel), 'recreate')
    print("Create output file: {}".format(outfile_ej.GetName()))

    # reco
    newtree_reco_ej = prepareOutputTree(tree_reco, 'reco')

    # add extra branches
    extra_variables_reco_ej = varsExtra(
        *getPrefixReco(recoAlgo), compute_energy=True, sum_weights=sumWeights
        )
    extra_variables_reco_ej.set_up_branches(newtree_reco_ej)

    # truth
    if tree_truth is not None:
        newtree_truth_ej = prepareOutputTree(tree_truth, truthLevel)

        # add extra branches
        extra_variables_truth_ej = varsExtra(
            *getPrefixTruth(truthLevel), compute_energy = truthLevel!="parton"
            )
        extra_variables_truth_ej.set_up_branches(newtree_truth_ej)
    else:
        extra_variables_truth_ej = None
        newtree_truth_ej = None

    #####
    # mu+jets
    outfile_mj = TFile('{}_{}_mjets.root'.format(outputName, truthLevel), 'recreate')
    print("Create output file: {}".format(outfile_mj.GetName()))

    # reco
    newtree_reco_mj = prepareOutputTree(tree_reco, 'reco')

    # add extra branches
    extra_variables_reco_mj = varsExtra(
        *getPrefixReco(recoAlgo), compute_energy=True, sum_weights=sumWeights
        )
    extra_variables_reco_mj.set_up_branches(newtree_reco_mj)

    # truth
    if tree_truth is not None:
        newtree_truth_mj = prepareOutputTree(tree_truth, truthLevel)

        # add extra branches
        extra_variables_truth_mj = varsExtra(
            *getPrefixTruth(truthLevel), compute_energy = truthLevel!="parton"
            )
        extra_variables_truth_mj.set_up_branches(newtree_truth_mj)
    else:
        extra_variables_truth_mj = None
        newtree_truth_mj = None

    #####
    # For acceptance correction factors
    outfile_acc = TFile('{}_{}_acc.root'.format(outputName, truthLevel), 'recreate')
    wname = 'totalWeight_nominal'
    acc = CorrectionFactors('acc', *getPrefixReco(recoAlgo), wname)
    acc_ejets = CorrectionFactors('acc_ejets', *getPrefixReco(recoAlgo), wname)
    acc_mjets = CorrectionFactors('acc_mjets', *getPrefixReco(recoAlgo), wname)

    # For efficiency correction factors
    outfile_eff = TFile('{}_{}_eff.root'.format(outputName, truthLevel), 'recreate')
    wname_mc = 'weight_mc'
    eff = CorrectionFactors('eff', *getPrefixTruth(truthLevel), wname_mc)
    eff_ejets = CorrectionFactors('eff_ejets', *getPrefixTruth(truthLevel), wname_mc)
    eff_mjets = CorrectionFactors('eff_mjets', *getPrefixTruth(truthLevel), wname_mc)

    ##########
    print("Iterate through events in reco trees")
    matched_reco_entries = []
    unmatched_reco_entries = []

    for i in range(tree_reco.GetEntries()):
        if maxevents is not None:
            if i > maxevents:
                break

        if not i%10000:
            print("processing event #{}".format(i))
        tree_reco.GetEntry(i)

        # reco-level selections
        if not sel.passRecoSelections(tree_reco, recoAlgo):
            continue

        passEJets = sel.passRecoSelections_ejets(tree_reco)
        passMJets = sel.passRecoSelections_mjets(tree_reco)

        # sanity check: should pass one and only one of the selections
        if not ( bool(passEJets) ^ bool(passMJets) ):
            print("WARNING! event {}: passEJets = {} passMJets = {}".format(i, passEJets, passMJets))
            continue

        # point to the extra variables and output trees for the right channel
        if passEJets:
            extra_vars_reco = extra_variables_reco_ej
            extra_vars_truth = extra_variables_truth_ej
            newtree_reco = newtree_reco_ej
            newtree_truth = newtree_truth_ej
            acc_ch = acc_ejets
            eff_ch = eff_ejets
        else: # passMJets
            extra_vars_reco = extra_variables_reco_mj
            extra_vars_truth = extra_variables_truth_mj
            newtree_reco = newtree_reco_mj
            newtree_truth = newtree_truth_mj
            acc_ch = acc_mjets
            eff_ch = eff_mjets

        # try to find the matched event in truth tree
        isTruthMatched = False

        if tree_truth is not None:
            eventID = (tree_reco.runNumber, tree_reco.eventNumber)
            truth_entry = tree_truth.GetEntryNumberWithIndex(*eventID)
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
                matched_reco_entries.append(i)

                extra_vars_truth.write_event(tree_truth)
                extra_vars_truth.set_dummy_flag(0)
                extra_vars_truth.set_match_flag(1)
            else:
                # no matched truth event or the truth event fails selections
                unmatched_reco_entries.append(i)

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

        # fill the histograms for acceptance and efficiency corrections
        if tree_truth is not None:
            acc.fill_denominator(tree_reco, extra_vars_reco)
            acc_ch.fill_denominator(tree_reco, extra_vars_reco)

            if isTruthMatched:
                acc.fill_numerator(tree_reco, extra_vars_reco)
                acc_ch.fill_numerator(tree_reco, extra_vars_reco)

                eff.fill_numerator(tree_truth, extra_vars_truth)
                eff_ch.fill_numerator(tree_truth, extra_vars_truth)

                eff.fill_denominator(tree_truth, extra_vars_truth)
                eff_ch.fill_denominator(tree_truth, extra_vars_truth)

    # end of tree_reco loop

    if not saveUnmatchedTruth:
        # The output files for new trees can be closed
        outfile_ej.Write()
        outfile_ej.Close()

        outfile_mj.Write()
        outfile_mj.Close()

    # compute acceptance corrections and write to the output file
    print("Compute acceptance correction factors")
    acc.compute_factors()
    acc_ejets.compute_factors()
    acc_mjets.compute_factors()

    outfile_acc.Write()
    outfile_acc.Close()

    ##########
    # truth tree
    #if saveUnmatchedTruth and tree_truth is not None:
    if tree_truth is not None:
        print("Iterate through events in truth trees")

        # build reco tree index
        try:
            buildTreeIndex(tree_reco)
        except RuntimeError as err:
            print("Failed to build index for reco level trees: {}".format(err))
            return

        # append unmatched truth events
        for j in range(tree_truth.GetEntries()):
            if maxevents is not None:
                if j > maxevents:
                    break

            if not j%10000:
                print("processing {} event {}".format(truthLevel, j))

            tree_truth.GetEntry(j)

            # truth-level selections
            passTruthSel = False
            if truthLevel=='parton':
                passTruthSel = sel.isSemiLeptonicTTbar(tree_truth)
            elif truthLevel=='particle':
                passTruthSel = sel.passPLSelections(tree_truth)

            if not passTruthSel:
                continue

            # try getting the matched reco event
            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)

            if reco_entry in matched_reco_entries:
                # found matched reco event.
                # skip since it has already been written.
                continue

            passEJets = sel.passTruthSelections_ejets(tree_truth)
            passMJets = sel.passTruthSelections_mjets(tree_truth)

            if passEJets:
                extra_vars_reco = extra_variables_reco_ej
                extra_vars_truth = extra_variables_truth_ej
                newtree_reco = newtree_reco_ej
                newtree_truth = newtree_truth_ej
                eff_ch = eff_ejets
            elif passMJets:
                extra_vars_reco = extra_variables_reco_mj
                extra_vars_truth = extra_variables_truth_mj
                newtree_reco = newtree_reco_mj
                newtree_truth = newtree_truth_mj
                eff_ch = eff_mjets
            else:
                # do not know tau decay products, skip for now
                continue

            extra_vars_truth.write_event(tree_truth)
            extra_vars_truth.set_match_flag(0)
            extra_vars_truth.set_dummy_flag(0)

            eff.fill_denominator(tree_truth, extra_vars_truth)
            eff_ch.fill_denominator(tree_truth, extra_vars_truth)

            if saveUnmatchedTruth:
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

    # new reco and truth trees should be of the same length
    #if newtree_truth_ej is not None:
    #    assert(newtree_reco_ej.GetEntries() == newtree_truth_ej.GetEntries())
    #if newtree_truth_mj is not None:
    #    assert(newtree_reco_mj.GetEntries() == newtree_truth_mj.GetEntries())

    # compute efficiency corrections and write to the output file
    print("Compute efficiency correction factors")
    eff.compute_factors()
    eff_ejets.compute_factors()
    eff_mjets.compute_factors()

    outfile_eff.Write()
    outfile_eff.Close()

    # Write and close output files
    if saveUnmatchedTruth:
        outfile_ej.Write()
        outfile_ej.Close()

        outfile_mj.Write()
        outfile_mj.Close()
