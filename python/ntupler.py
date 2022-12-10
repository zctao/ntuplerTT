import os
import time
import numpy as np

from ROOT import TChain, TTree, TFile

from extra_variables import varsExtra
import selections as sel
from histogramer import HistogramManager

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
            logger.info(f" processing {i}/{nentries}")
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

class Ntupler():
    def __init__(
        self,
        outputName,
        inputFiles_reco,
        inputFiles_truth = [],
        sumWeights_dict = None,
        recoAlgo = 'klfitter', # ttbar reconstruction algorithm
        truthLevel ='parton',
        treename = 'nominal',
        makeHistograms = False
        ):

        self.recoAlgo = recoAlgo
        self.truthLevel = truthLevel

        ######
        # Read input trees
        # Set self.tree_reco and self.tree_truth
        # Initialize self.index_reco, self.index_truth to empty dict()
        # Initialize self.dup_reco, self.dup_truth to empty set()
        self._read_input_trees(
            inputFiles_reco,
            inputFiles_truth,
            treename = treename
            )

        ######
        # Prepare output trees
        # self.outfile
        # self.newtree_reco, self.newtree_truth
        # self.extra_variables_reco, self.extra_variables_truth
        self._prepare_outputs(
            outputName,
            sumWeights_dict = sumWeights_dict
            )

        ######
        # Histograms
        self.histograms = HistogramManager(outputName+'_histograms.root') if makeHistograms else None

    def __call__(
        self,
        maxevents=None,
        saveUnmatchedReco=True,
        saveUnmatchedTruth=True,
        checkDuplicate = False
        ):
        logger.info("Start processing mini-ntuples")

        if self.tree_truth is None:
            saveUnmatchedTruth = False

        ######
        # Build tree index
        if checkDuplicate or saveUnmatchedTruth:
            # Need to build reco tree index before iterating
            self._build_reco_index(checkDuplicate=checkDuplicate)

        # Always need to build truth tree index if there is one
        if self.tree_truth:
            self._build_truth_index(checkDuplicate=checkDuplicate)

        ######
        # Loop over reco tree
        self._iterate_reco_tree(maxevents, saveUnmatchedReco)

        ######
        # Loop over truth tree
        if saveUnmatchedTruth or self.histograms is not None:
            self._iterate_truth_tree(maxevents)

        ###
        # new reco and truth trees should be of the same length
        #if self.newtree_truth_ej is not None:
        #    assert(self.newtree_reco_ej.GetEntries() == self.newtree_truth_ej.GetEntries())
        #if self.newtree_truth_mj is not None:
        #    assert(self.newtree_reco_mj.GetEntries() == self.newtree_truth_mj.GetEntries())

        if self.histograms:
            self.histograms.computeCorrections()

        ######
        # Write files to disk
        self._write_to_files()

    def _read_input_trees(
        self,
        inputFiles_reco,
        inputFiles_truth = [],
        treename = 'nominal'
        ):

        self.tree_reco = TChain(treename)
        logger.info("Read input trees and build index")
        logger.info("Reco level")
        for infile_reco in inputFiles_reco:
            self.tree_reco.Add(infile_reco)
        nevents_reco = self.tree_reco.GetEntries()
        logger.info(f"Number of events in the reco tree: {nevents_reco}")

        self.index_reco = dict()
        self.dup_reco = set()

        self.tree_truth = None
        if inputFiles_truth:
            logger.info(self.truthLevel.capitalize()+" level")
            self.tree_truth = TChain('nominal') # truth-level tree is always 'nominal'
            for infile_truth in inputFiles_truth:
                self.tree_truth.Add(infile_truth)
            nevents_truth = self.tree_truth.GetEntries()
            logger.info(f"Number of events in the truth tree: {nevents_truth}")

        self.index_truth = dict()
        self.dup_truth = set()

    def _prepare_outputs(
        self,
        outputName,
        sumWeights_dict = None
        ):
        logger.info("Create output trees")

        self.outNamePrefix = outputName
        foutname = f"{self.outNamePrefix}_{self.recoAlgo}"
        if self.tree_truth:
            foutname += f"_{self.truthLevel}"

        ###
        # e+jets
        self.outfile = TFile(foutname+"_ljets.root", "recreate")
        logger.info(f"Create output file: {self.outfile.GetName()}")

        # reco tree
        self.newtree_reco = self.tree_reco.CloneTree(0)
        self.newtree_reco.SetName('reco')

        # add extra branches
        self.extra_variables_reco = varsExtra(
            *getPrefixReco(self.recoAlgo), compute_energy=True,
            sum_weights_map = sumWeights_dict
        )
        self.extra_variables_reco.set_up_branches(self.newtree_reco)

        # truth tree
        if self.tree_truth:
            self.newtree_truth = self.tree_truth.CloneTree(0)
            self.newtree_truth.SetName(self.truthLevel)

            # add extra branches
            self.extra_variables_truth = varsExtra(
                *getPrefixTruth(self.truthLevel),
                compute_energy = self.truthLevel!="parton",
                sum_weights_map = sumWeights_dict, is_reco=False
            )
            self.extra_variables_truth.set_up_branches(self.newtree_truth)
        else:
            self.newtree_truth = None
            self.extra_variables_truth = None

    def _build_reco_index(self, checkDuplicate):
        logger.info(f"Build index hash table for reco tree")
        self.index_reco, self.dup_reco = buildHashMapFromTTree(
            self.tree_reco,
            check_duplicate = checkDuplicate,
            fname_eventID = f"{self.outNamePrefix}_duplicate_eventID_reco.txt"
        )
        assert(self.index_reco)

    def _build_truth_index(self, checkDuplicate):
        logger.info(f"Build index hash table for truth tree")
        self.index_truth, self.dup_truth = buildHashMapFromTTree(
            self.tree_truth,
            check_duplicate = checkDuplicate,
            fname_eventID = f"{self.outNamePrefix}_duplicate_eventID_truth.txt"
        )
        assert(self.tree_truth)

    def _iterate_reco_tree(self, maxevents=None, saveUnmatchedReco=True):
        logger.info("Iterate through events in reco trees")

        tstart = time.time()

        nevents_reco = self.tree_reco.GetEntries()

        for i in range(nevents_reco):
            if maxevents is not None:
                if i > maxevents:
                    break

            if not i%10000:
                logger.info(f" processing event #{i}")

            self.tree_reco.GetEntry(i)

            # event ID
            eventID = (self.tree_reco.runNumber, self.tree_reco.eventNumber)

            if eventID in self.dup_reco or eventID in self.dup_truth:
                # this is an event with duplicated event ID
                continue

            # reco-level selections
            if not sel.passRecoSelections(self.tree_reco, self.recoAlgo):
                continue

            passEJets = sel.passRecoSelections_ejets(self.tree_reco)
            passMJets = sel.passRecoSelections_mjets(self.tree_reco)

            # sanity check: should pass one and only one of the selections
            if not ( bool(passEJets) ^ bool(passMJets) ):
                logger.info(f"WARNING! event {i}: passEJets = {passEJets} passMJets = {passMJets}")
                continue

            # try to find the matched event in the truth tree
            isTruthMatched = False

            if self.tree_truth:
                #truth_entry = self.tree_truth.GetEntryNumberWithIndex(*eventID)
                truth_entry = self.index_truth.get(eventID, -1)
                self.tree_truth.GetEntry(truth_entry)

                if truth_entry >= 0:
                    # found a matched truth-level event
                    # check if the matched event satisfies the truth-level requirement
                    if self.truthLevel == 'parton':
                        # check if it is semi-leptonic ttbar
                        #isTruthMatched = tree_reco.isTruthSemileptonic
                        # instead of trusting the flag in tree_reco, check the tree_truth ourselves
                        isTruthMatched = sel.isSemiLeptonicTTbar(self.tree_truth)
                    elif self.truthLevel == 'particle':
                        # check if passing the particle-level selections
                        isTruthMatched = sel.passPLSelections(self.tree_truth)

                if isTruthMatched:
                    self.extra_variables_truth.write_event(self.tree_truth)
                    self.extra_variables_truth.set_dummy_flag(0)
                    self.extra_variables_truth.set_match_flag(1)
                else:
                    # no matched truth event or the truth event fails selections
                    self.extra_variables_truth.write_event(self.tree_truth)
                    self.extra_variables_truth.set_dummy_flag(1)
                    self.extra_variables_truth.set_match_flag(0)

            self.extra_variables_reco.write_event(self.tree_reco)
            self.extra_variables_reco.set_dummy_flag(0)
            self.extra_variables_reco.set_match_flag(isTruthMatched)

            # fill the new tree
            if self.tree_truth is None:
                # just fill the new reco tree
                self.newtree_reco.Fill()
            else:
                if isTruthMatched or saveUnmatchedReco:
                    # fill the new reco and truth tree
                    self.newtree_reco.Fill()
                    self.newtree_truth.Fill()

            # fill the histograms
            if self.histograms:
                self.histograms.fillReco(self.newtree_reco)
                if isTruthMatched:
                    self.histograms.fillResponse(self.newtree_reco, self.newtree_truth)

        # end of tree_reco loop

        tdone = time.time()
        logger.info(f"Processing all reco events took {tdone-tstart:.2f} seconds ({(tdone-tstart)/nevents_reco:.5f} seconds/event)")

    def _iterate_truth_tree(self, maxevents=None, truthLevel='parton', saveEvents=False):

        logger.info("Iterate through events in truth trees")

        if saveEvents:
            assert(self.index_reco)

        tstart = time.time()

        nevents_truth = self.tree_truth.GetEntries()

        for j in range(nevents_truth):
            if maxevents is not None:
                if j > maxevents:
                    break

            if not j%10000:
                logger.info(f" processing {self.truthLevel} event {j}")

            self.tree_truth.GetEntry(j)

            eventID_truth = (self.tree_truth.runNumber, self.tree_truth.eventNumber)

            if eventID_truth in self.dup_truth or eventID_truth in self.dup_reco:
                continue

            # truth-level selections
            passTruthSel = False
            if self.truthLevel == 'parton':
                passTruthSel = sel.isSemiLeptonicTTbar(self.tree_truth)
            elif self.truthLevel == 'particle':
                passTruthSel = sel.passPLSelections(self.tree_truth)

            if not passTruthSel:
                continue

            # fill the histograms
            if self.histograms:
                self.histograms.fillTruth(self.tree_truth)

            if not saveEvents:
                continue

            # try getting the matched reco event
            #reco_entry = self.tree_reco.GetEntryNumberWithIndex(*eventID_truth)
            reco_entry = self.index_reco.get(eventID_truth, -1)

            if reco_entry >= 0:
                # found a matched reco-level event
                self.tree_reco.GetEntry(reco_entry)

                # check if it passed the reco-level selection
                if sel.passRecoSelections(self.tree_reco, self.recoAlgo):
                    # !!this event has already been included in the reco tree loop!!
                    # skip
                    continue

            self.extra_variables_truth.write_event(self.tree_truth)
            self.extra_variables_truth.set_match_flag(0)
            self.extra_variables_truth.set_dummy_flag(0)

            self.newtree_truth.Fill()

            # fill reco tree with dummy events
            # get a random event from the reco tree
            #ireco = np.random.randint(0, nevents_reco-1) # too slow
            ireco = -1
            self.tree_reco.GetEntry(ireco)

            self.extra_variables_reco.write_event(self.tree_reco)
            self.extra_variables_reco.set_match_flag(0)
            self.extra_variables_reco.set_dummy_flag(1)

            self.newtree_reco.Fill()

        # end of tree_truth loop

        tdone = time.time()
        logger.info(f"Processing all truth events took {tdone-tstart:.2f} seconds ({(tdone-tstart)/nevents_truth:.5f} seconds/event)")

    def _write_to_files(self):
        self.outfile.Write()
        self.outfile.Close()

        self.histograms.write_to_file()