import time
from ROOT import TH1, TH1F, TChain, TFile
from extra_variables import varsExtra
from ntupler import getPrefixReco, getPrefixTruth, buildTreeIndex
import selections as sel

class HistogramsTTbar():
    def __init__(self, label, thad_prefix, tlep_prefix, ttbar_prefix):
        # prefix of branch names for hadronic top, leptonic top, and ttbar
        self.thad_prefix = thad_prefix.rstrip('_')
        self.tlep_prefix = tlep_prefix.rstrip('_')
        self.ttbar_prefix = ttbar_prefix.rstrip('_')

        # Some parton MC truth variables have unit MeV instead of GeV
        sf_unit = 1000. if self.ttbar_prefix.startswith('MC_') else 1.

        # histograms
        TH1.SetDefaultSumw2()
        self.hist_th_pt = TH1F(label+"_th_pt", "p_{T}^{t,had}", 100, 0, 1000*sf_unit)
        self.hist_th_y = TH1F(label+"_th_y", "y^{t,had}", 100, -2.5, 2.5)
        self.hist_mtt = TH1F(label+"_mtt", "m^{ttbar}", 100, 300*sf_unit, 2000*sf_unit)
        self.hist_ptt = TH1F(label+"_ptt", "p_{T}^{ttbar}", 100, 0, 800*sf_unit)
        self.hist_ytt = TH1F(label+"_ytt", "y^{ttbar}", 100, -2.5, 2.5)
        self.hist_dphi = TH1F(label+"_dphi", "|\Delta\phi(t, tbar)|", 100, 0, 3.15)

    def fill(self, tree, extra_variables, ievent=None, weight_name=None):
        if ievent is not None:
            tree.GetEntry(ievent)

        w = 1 if weight_name is None else getattr(tree, weight_name)

        self.hist_th_pt.Fill( getattr(tree, self.thad_prefix+'_pt'), w )
        self.hist_th_y.Fill( getattr(tree, self.thad_prefix+'_y'), w )
        self.hist_mtt.Fill( getattr(tree, self.ttbar_prefix+'_m'), w )
        self.hist_ptt.Fill( getattr(tree, self.ttbar_prefix+'_pt'), w )
        self.hist_ytt.Fill( getattr(tree, self.ttbar_prefix+'_y'), w )

        self.hist_dphi.Fill( extra_variables.ttbar_dphi[0], w )

class CorrectionFactors():
    def __init__(self, label, thad_prefix, tlep_prefix, ttbar_prefix, wname):

        self.hists_numer = HistogramsTTbar(
            label+'_numer', thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.hists_denom = HistogramsTTbar(
            label+'_denom', thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.hists_ratio = HistogramsTTbar(
            label, thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.weight_name = wname

    def fill_denominator(self, tree, extra_vars, ievent=None):
        self.hists_denom.fill(tree, extra_vars, ievent, self.weight_name)

    def fill_numerator(self, tree, extra_vars, ievent=None):
        self.hists_numer.fill(tree, extra_vars, ievent, self.weight_name)

    def compute_factors(self, xtitle=None, ytitle=None):
        for vname, histogram in vars(self.hists_ratio).items():
            if not isinstance(histogram, TH1):
                continue

            histogram.Divide(
                getattr(self.hists_numer, vname),
                getattr(self.hists_denom, vname)
            )

            if xtitle:
                histogram.GetXaxis().SetTitle(xtitle)
            if ytitle:
                histogram.GetYaxis().SetTitle(ytitle)

def computeAcceptanceCorrections(
        outputName,
        tree_reco,
        tree_truth,
        recoAlgo='klfitter',
        truthLevel='parton'
    ):
    # build index for truth tree
    try:
        buildTreeIndex(tree_truth)
    except RuntimeError as err:
        print(f"Failed to build index for truth tree: {err}")
        return

    # extra variables
    extra_variables_reco = varsExtra(*getPrefixReco(recoAlgo))

    # output file
    outfile_acc = TFile(f"{outputName}_{truthLevel}_acc.root", "recreate")
    print(f"Create output file: {outfile_acc.GetName()}")

    # correction factors
    wname = "totalWeight_nominal"
    acc = CorrectionFactors('acc', *getPrefixReco(recoAlgo), wname)
    # corrections for e+jets and mu+jets separately in case necessary
    acc_ej = CorrectionFactors('acc_ejets', *getPrefixReco(recoAlgo), wname)
    acc_mj = CorrectionFactors('acc_mjets', *getPrefixReco(recoAlgo), wname)

    print("Loop over reco trees")

    tstart = time.time()
    for ireco in range(tree_reco.GetEntries()):
        if not ireco%10000:
            print(f"processing event #{ireco}")

        tree_reco.GetEntry(ireco)

        # event selections
        if not sel.passRecoSelections(tree_reco, recoAlgo):
            continue

        passEJets = sel.passRecoSelections_ejets(tree_reco)
        passMJets = sel.passRecoSelections_mjets(tree_reco)

        acc_ch = acc_ej if passEJets else acc_mj

        # compute additional variables
        extra_variables_reco.write_event(tree_reco)

        # fill histograms
        acc.fill_denominator(tree_reco, extra_variables_reco)
        acc_ch.fill_denominator(tree_reco, extra_variables_reco)

        # try to match events in the truth tree based on event ID
        eventID = (tree_reco.runNumber, tree_reco.eventNumber)
        itruth = tree_truth.GetEntryNumberWithIndex(*eventID)

        isTruthMatched = False
        if itruth >= 0:
            # found a matched truth-level event
            tree_truth.GetEntry(itruth)

            # check if the matched event satisfies truth-level requirements
            if truthLevel == 'parton':
                # check if it is semi-leptonic ttbar
                # There is a 'isTruthSemileptonic' branch in tree_reco
                # But instead of trusting it, check tree_truth ourselves
                isTruthMatched = sel.isSemiLeptonicTTbar(tree_truth)
            elif truthLevel == 'particle':
                # check if passing the particle level selections
                isTruthMatched = sel.passPLSelections(tree_truth)

        if isTruthMatched:
            # fill the numerator histograms
            acc.fill_numerator(tree_reco, extra_variables_reco)
            acc_ch.fill_numerator(tree_reco, extra_variables_reco)

    # end of tree_reco loop

    tdone = time.time()
    print(f"Processing time: {tdone-tstart:.2f} seconds ({(tdone-tstart)/tree_reco.GetEntries():.5f} seconds/event)")

    # compute correction factors
    print("Compute acceptance correction factors")
    acc.compute_factors()
    acc_ej.compute_factors()
    acc_mj.compute_factors()

    outfile_acc.Write()
    outfile_acc.Close()

def computeEfficiencyCorrections(
        outputName,
        tree_truth,
        tree_reco,
        truthLevel='parton',
        recoAlgo='klfitter'
    ):
    # build index for reco tree
    try:
        buildTreeIndex(tree_reco)
    except RuntimeError as err:
        print(f"Failed to build index for reco tree: {err}")
        return

    # extra variables
    extra_variables_truth = varsExtra(
        *getPrefixTruth(truthLevel), compute_energy = truthLevel!="parton")

    # output file
    outfile_eff = TFile(f"{outputName}_{truthLevel}_eff.root", "recreate")
    print(f"Create output file: {outfile_eff.GetName()}")

    # correction factors
    wname = 'weight_mc'
    eff = CorrectionFactors('eff', *getPrefixTruth(truthLevel), wname)
    # corrections for e and mu channels separately in casee necessary
    eff_ej = CorrectionFactors('eff_ejets', *getPrefixTruth(truthLevel), wname)
    eff_mj = CorrectionFactors('eff_mjets', *getPrefixTruth(truthLevel), wname)

    print(f"Loop over {truthLevel} tree")

    tstart = time.time()
    for itruth in range(tree_truth.GetEntries()):
        if not itruth%10000:
            print(f"processing event #{itruth}")

        tree_truth.GetEntry(itruth)

        # truth-level selections
        passTruthSel = False
        if truthLevel == 'parton':
            passTruthSel = sel.isSemiLeptonicTTbar(tree_truth)
        elif truthLevel == 'particle':
            passTruthSel = sel.passPLSelections(tree_truth)

        if not passTruthSel:
            continue

        passEJets = sel.passTruthSelections_ejets(tree_truth)
        passMJets = sel.passTruthSelections_mjets(tree_truth)

        eff_ch = eff_ej if passEJets else eff_mj

        # compute additional variables
        extra_variables_truth.write_event(tree_truth)

        # fill histograms
        eff.fill_denominator(tree_truth, extra_variables_truth)
        eff_ch.fill_denominator(tree_truth, extra_variables_truth)

        # try to match events in the reco tree based on event ID
        eventID = (tree_truth.runNumber, tree_truth.eventNumber)
        ireco = tree_reco.GetEntryNumberWithIndex(*eventID)

        if ireco >= 0:
            # found a matched reco-level event
            tree_reco.GetEntry(ireco)

            # check if it passes the reco-level selection
            if sel.passRecoSelections(tree_reco, recoAlgo):
                eff.fill_numerator(tree_truth, extra_variables_truth)
                eff_ch.fill_numerator(tree_truth, extra_variables_truth)

    # end of tree_truth loop

    tdone = time.time()
    print(f"Processing time: {tdone-tstart:.2f} seconds ({(tdone-tstart)/tree_truth.GetEntries():.5f} seconds/event)")

    # compute corrections
    print("Compute efficiency correction factors")
    eff.compute_factors()
    eff_ej.compute_factors()
    eff_mj.compute_factors()

    outfile_eff.Write()
    outfile_eff.Close()

def computeAccEffCorrections(
        outputName,
        inputFiles_reco,
        inputFiles_truth,
        recoAlgo = 'klfitter', # ttbar reconstruction algorithm
        truthLevel ='parton',
        treename='nominal',
    ):
    print("Compute correction factors")

    # Reco trees
    print("Read reco level trees")
    tree_reco = TChain(treename)
    for infile_reco in inputFiles_reco:
        tree_reco.Add(infile_reco)
    nevents_reco = tree_reco.GetEntries()
    print(f"Number of events in the reco tree: {nevents_reco}")

    # MC truth trees
    print(f"Read {truthLevel.capitalize()} level trees")
    tree_truth = TChain(treename)
    for infile_truth in inputFiles_truth:
        tree_truth.Add(infile_truth)
    nevents_truth = tree_truth.GetEntries()
    print(f"Number of events in the truth tree: {nevents_truth}")

    # Compute acceptance corrections
    print("Acceptance corrections")
    computeAcceptanceCorrections(
        outputName, tree_reco, tree_truth,
        recoAlgo=recoAlgo, truthLevel=truthLevel
    )

    # Compute efficiency corrections
    print("Efficiency corrections")
    computeEfficiencyCorrections(
        outputName, tree_truth, tree_reco,
        recoAlgo=recoAlgo, truthLevel=truthLevel
    )
