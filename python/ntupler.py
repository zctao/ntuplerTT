import os
import time
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

def getSumWeights(tree_sumw):
    sumw = 0
    for w in tree_sumw:
        sumw += w.totalEventsWeighted

    return sumw

def matchAndSplitTrees(inputFiles_reco, inputFiles_truth, inputFiles_sumw,
                       outputName, truthLevel ='parton', treename='nominal',
                       saveUnmatchedReco=True, saveUnmatchedTruth=True,
                       maxevents=None):

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
    print("sum weights = ", sumWeights)

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
        if maxevents is not None:
            if i > maxevents:
                break

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
            passEJets = passSelection_ejets(tree_reco)
            passMJets = passSelection_mjets(tree_reco)
            # should pass one and only one of the selections
            assert( bool(passEJets) ^ bool(passMJets) )

            if passEJets:
                extra_variables_reco_ej.set_match_flag(1)
                extra_variables_reco_ej.write_event(tree_reco)
                newtree_reco_ej.Fill()
            if passMJets:
                extra_variables_reco_mj.set_match_flag(1)
                extra_variables_reco_mj.write_event(tree_reco)
                newtree_reco_mj.Fill()

            # write truth events
            tree_truth.GetEntry(truth_entry)
            if passEJets:
                extra_variables_truth_ej.set_match_flag(1)
                extra_variables_truth_ej.write_event(tree_truth)
                newtree_truth_ej.Fill()
            if passMJets:
                extra_variables_truth_mj.set_match_flag(1)
                extra_variables_truth_mj.write_event(tree_truth)
                newtree_truth_mj.Fill()

    if saveUnmatchedReco:
        # append unmatched reco events
        print("Append unmatched reco events")
        for ievt, ireco_unmatched in enumerate(unmatched_reco_entries):
            if maxevents is not None:
                if i > maxevents:
                    break

            if not ievt%10000:
                print("processing unmatched reco event {}".format(ievt))

            tree_reco.GetEntry(ireco_unmatched)

            passEJets = passSelection_ejets(tree_reco)
            passMJets = passSelection_mjets(tree_reco)
            assert( bool(passEJets) ^ bool(passMJets) )
            if passEJets:
                extra_variables_reco_ej.set_match_flag(0)
                extra_variables_reco_ej.write_event(tree_reco)
                newtree_reco_ej.Fill()
            if passMJets:
                extra_variables_reco_mj.set_match_flag(0)
                extra_variables_reco_mj.write_event(tree_reco)
                newtree_reco_mj.Fill()

    if saveUnmatchedTruth:
        # append unmatched truth events
        print("Append unmatched {} events".format(truthLevel))
        for j in range(tree_truth.GetEntries()):
            if maxevents is not None:
                if i > maxevents:
                    break

            if not j%10000:
                print("processing {} event {}".format(truthLevel, j))

            tree_truth.GetEntry(j)
            reco_entry = tree_reco.GetEntryNumberWithIndex(tree_truth.runNumber, tree_truth.eventNumber)

            if reco_entry >= 0:
                # found matched reco event.
                # skip since it has already been written.
                continue

            if passSelection_ejets(tree_truth):
                extra_variables_truth_ej.set_match_flag(0)
                extra_variables_truth_ej.write_event(tree_truth)
                newtree_truth_ej.Fill()
            if passSelection_mjets(tree_truth):
                extra_variables_truth_mj.set_match_flag(0)
                extra_variables_truth_mj.write_event(tree_truth)
                newtree_truth_mj.Fill()

    # Write and close output files
    outfile_ej.Write()
    outfile_ej.Close()

    outfile_mj.Write()
    outfile_mj.Close()

def getInputFileNames(input_list, check_file=True):
    rootFiles = []
    if input_list is None:
        return rootFiles

    for fp in input_list:
        if check_file and not os.path.isfile(fp):
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
            files = getInputFileNames(lines, check_file=False)
            rootFiles += files
        else:
            print("Don't know how to handle input file". fp)
            continue

    return rootFiles
