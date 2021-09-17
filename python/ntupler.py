import os
import time
import numpy as np
from ROOT import TChain, TTree, TFile
from extra_variables import varsExtra
from acceptance import CorrectionFactors

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

def getWdecayIDs(tree, ievent=None):
    if ievent is not None:
        tree.GetEntry(ievent)

    if not hasattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid'):
        print("Cannot find branches for W decay products.")
        return []
    else:
        decayIDs = [abs(getattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_tbar_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay1_from_t_afterFSR_pdgid')),
                    abs(getattr(tree, 'MC_Wdecay2_from_t_afterFSR_pdgid'))]
        return decayIDs

def isSemiLeptonicTTbar(tree_parton, ievent=None):
    if ievent is not None:
        tree_parton.GetEntry(ievent)

    # check if a parton level event is semileptonic ttbar
    tbar_wdecay1_pdgid = tree_parton.MC_Wdecay1_from_tbar_afterFSR_pdgid
    tbarIsHadronic = abs(tbar_wdecay1_pdgid) in [1, 2, 3, 4, 5, 6]

    t_wdecay1_pdgid = tree_parton.MC_Wdecay1_from_t_afterFSR_pdgid
    tIsHadronic = abs(t_wdecay1_pdgid) in [1, 2, 3, 4, 5, 6]

    # Note:
    # This seletion also get rid of the truth events that have nan or inf for
    # some branches e.g. MC_thad_afterFSR_y, MC_ttbar_afterFSR_E
    # The W decay products on the hadronic leg in such events are all zeros
    # Need to investigate the upstream ntuple production

    return bool(tbarIsHadronic) ^ bool(tIsHadronic)

def passSelection_ejets(tree):
    if hasattr(tree, 'passed_resolved_ejets_4j2b'):
        # reco or particle level tree
        return tree.passed_resolved_ejets_4j2b
    elif hasattr(tree, 'MC_Wdecay1_from_tbar_afterFSR_pdgid'):
        # parton tree
        decayIDs = getWdecayIDs(tree)

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
        decayIDs = getWdecayIDs(tree)

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

    #####
    # For acceptance correction factors
    outfile_acc = TFile('{}_{}_acc.root'.format(outputName, truthLevel), 'recreate')
    wname = 'totalWeight_nominal'
    acc = CorrectionFactors('acc', reco_prefix_thad, reco_prefix_tlep, reco_prefix_ttbar, wname)
    acc_ejets = CorrectionFactors('acc_ejets', reco_prefix_thad, reco_prefix_tlep, reco_prefix_ttbar, wname)
    acc_mjets = CorrectionFactors('acc_mjets', reco_prefix_thad, reco_prefix_tlep, reco_prefix_ttbar, wname)

    # For efficiency correction factors
    outfile_eff = TFile('{}_{}_eff.root'.format(outputName, truthLevel), 'recreate')
    wname_mc = 'weight_mc'
    eff = CorrectionFactors('eff', truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar, wname_mc)
    eff_ejets = CorrectionFactors('eff_ejets', truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar, wname_mc)
    eff_mjets = CorrectionFactors('eff_mjets', truth_prefix_thad, truth_prefix_tlep, truth_prefix_ttbar, wname_mc)

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
        # add additional selections here

        passEJets = passSelection_ejets(tree_reco)
        passMJets = passSelection_mjets(tree_reco)

        passSel = passEJets or passMJets
        if not passSel:
            continue

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
                    isTruthMatched = isSemiLeptonicTTbar(tree_truth)
                elif truthLevel == 'particle':
                    # check if passing the particle level selections
                    isTruthMatched = tree_truth.passedPL

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
                passTruthSel = isSemiLeptonicTTbar(tree_truth)
            elif truthLevel=='particle':
                passTruthSel = tree_truth.passedPL

            if not passTruthSel:
                continue

            # try getting the matched reco event
            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)

            if reco_entry in matched_reco_entries:
                # found matched reco event.
                # skip since it has already been written.
                continue

            passEJets = passSelection_ejets(tree_truth)
            passMJets = passSelection_mjets(tree_truth)

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
    if newtree_truth_ej is not None:
        assert(newtree_reco_ej.GetEntries() == newtree_truth_ej.GetEntries())
    if newtree_truth_mj is not None:
        assert(newtree_reco_mj.GetEntries() == newtree_truth_mj.GetEntries())

    # compute acceptance and efficiency
    acc.compute_factors()
    acc_ejets.compute_factors()
    acc_mjets.compute_factors()
    eff.compute_factors()
    eff_ejets.compute_factors()
    eff_mjets.compute_factors()

    # Write and close output files
    outfile_ej.Write()
    outfile_ej.Close()

    outfile_mj.Write()
    outfile_mj.Close()

    outfile_acc.Write()
    outfile_acc.Close()

    outfile_eff.Write()
    outfile_eff.Close()
