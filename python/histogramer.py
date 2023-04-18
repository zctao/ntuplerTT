from array import array
import json

from ROOT import TH1D, TH2D, TFile

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Observable configurations (put here for now)
obsConfig_dict = {
    "th_pt" : {
        "reco" : "PseudoTop_Reco_top_had_pt",
        "truth" : "MC_thad_afterFSR_pt"
    },
    "th_y" : {
        "reco" :  "PseudoTop_Reco_top_had_y",
        "truth" : "MC_thad_afterFSR_y"
    },
    "th_y_abs" : {
        "reco" :  "PseudoTop_Reco_top_had_y",
        "truth" : "MC_thad_afterFSR_y"
    },
    "th_phi" : {
        "reco" :  "PseudoTop_Reco_top_had_phi",
        "truth" : "MC_thad_afterFSR_phi"
    },
    "th_e" : {
        "reco" :  "PseudoTop_Reco_top_had_E",
        "truth" : "MC_thad_afterFSR_E"
    },
    "tl_pt" : {
        "reco" : "PseudoTop_Reco_top_lep_pt",
        "truth" : "MC_tlep_afterFSR_pt"
    },
    "tl_y" : {
        "reco" :  "PseudoTop_Reco_top_lep_y",
        "truth" : "MC_tlep_afterFSR_y"
    },
    "tl_y_abs" : {
        "reco" :  "PseudoTop_Reco_top_lep_y",
        "truth" : "MC_tlep_afterFSR_y"
    },
    "tl_phi" : {
        "reco" :  "PseudoTop_Reco_top_lep_phi",
        "truth" : "MC_tlep_afterFSR_phi"
    },
    "tl_e" : {
        "reco" :  "PseudoTop_Reco_top_lep_E",
        "truth" : "MC_tlep_afterFSR_E"
    },
    "mtt": {
        "reco" : "PseudoTop_Reco_ttbar_m",
        "truth" : "MC_ttbar_afterFSR_m"
    },
    "ptt": {
        "reco" : "PseudoTop_Reco_ttbar_pt",
        "truth" : "MC_ttbar_afterFSR_pt"
    },
    "ytt": {
        "reco" : "PseudoTop_Reco_ttbar_y",
        "truth" : "MC_ttbar_afterFSR_y"
    },
    "ytt_abs": {
        "reco" : "PseudoTop_Reco_ttbar_y",
        "truth" : "MC_ttbar_afterFSR_y"
    },
}

def hasUnitMeV(variable_name):
    if variable_name in ["MC_thad_afterFSR_pt", "MC_tlep_afterFSR_pt", "MC_ttbar_afterFSR_m", "MC_ttbar_afterFSR_pt"]:
        return True
    else:
        return False

def getAcceptanceCorrection(h2d_response, h_reco, hname="Acceptance", flow=True):
    # project h2d_response to x-axis i.e. the reco axis
    if flow:
        firstbin_mc = 0
        lastbin_mc = -1
    else:
        # exclude Y underflow and overflow bins
        firstbin_mc = 1
        lastbin_mc = h2d_response.GetNbinsY()

    h_acc = h2d_response.ProjectionX(hname, firstbin_mc, lastbin_mc, "e")
    h_acc.Divide(h_reco)
    return h_acc

def getEfficiencyCorrection(h2d_response, h_mctruth, hname="Efficiency", flow=True):
    # project h2d_response to y-axis i.e. the MC truth axis
    if flow:
        firstbin_reco = 0
        lastbin_reco = -1
    else:
        # exclude X underflow and overflow bins
        firstbin_reco = 1
        lastbin_reco = h2d_response.GetNbinsX()

    h_eff = h2d_response.ProjectionY(hname, firstbin_reco, lastbin_reco, "e")
    h_eff.Divide(h_mctruth)
    return h_eff

class HistogramManager():
    def __init__(
        self,
        outputname='histograms.root',
        binning_config='configs/binning/bins_ttdiffxs_run2_ljets.json'
        ):

        # binning
        with open(binning_config, 'r') as f_bins:
            self.bins_d = json.load(f_bins)

        # event weight names
        self.wname = "normalized_weight"
        self.wname_mc = "normalized_weight_mc"

        # file to save the histograms
        self.outfile = TFile(outputname, "recreate")
        logger.info(f"Create output file: {self.outfile.GetName()}")

        # initialize histograms
        self.hists_d = {}

        for ob in observables:
            obCfg = obsConfig_dict.get(ob)
            if obCfg is None:
                print(f"WARNING: observable {ob} in not defined in obsConfig_dict. Skip...")
                continue

            self.hists_d[ob] = {}

            bins_reco = array('f', self.bins_d[ob])
            nbins_reco = len(bins_reco) - 1
            var_reco = obCfg['reco']
            if ob.endswith('_abs'):
                var_reco = var_reco+'_abs'

            self.hists_d[ob]['reco'] = TH1D(f"h_{var_reco}", "", nbins_reco, bins_reco)
            self.hists_d[ob]['reco'].GetXaxis().SetTitle(var_reco)

            # same reco and truth bins for now
            bins_truth = array('f', self.bins_d[ob])
            nbins_truth = len(bins_truth) - 1
            var_truth = obCfg['truth']
            if ob.endswith('_abs'):
                var_truth = var_truth+'_abs'

            self.hists_d[ob]['truth'] = TH1D(f"h_{var_truth}", "", nbins_truth, bins_truth)
            self.hists_d[ob]['truth'].GetXaxis().SetTitle(var_truth)

            self.hists_d[ob]['response'] = TH2D(f"h_{var_truth}_vs_{var_reco}", "", nbins_reco, bins_reco, nbins_truth, bins_truth)
            self.hists_d[ob]['response'].GetXaxis().SetTitle(var_reco)
            self.hists_d[ob]['response'].GetYaxis().SetTitle(var_truth)

            # response but with mc weights
            self.hists_d[ob]['response_mcweight'] = TH2D(f"h_{var_truth}_vs_{var_reco}_mcWeight", "", nbins_reco, bins_reco, nbins_truth, bins_truth)
            self.hists_d[ob]['response_mcweight'].GetXaxis().SetTitle(var_reco)
            self.hists_d[ob]['response_mcweight'].GetYaxis().SetTitle(var_truth)

    def fillReco(self, event):
        w = getattr(event, self.wname)

        for ob in self.hists_d:
            vname = obsConfig_dict[ob]['reco']
            value = getattr(event, vname)

            if ob.endswith('_abs'):
                value = abs(value)

            self.hists_d[ob]['reco'].Fill(value, w)

    def fillTruth(self, event, extra_vars):
        try:
            w = getattr(event, self.wname_mc)
        except AttributeError:
            # get the normalized weight from extra_vars
            w = extra_vars.normalized_weight[0]

        for ob in self.hists_d:
            vname = obsConfig_dict[ob]['truth']
            try:
                value = getattr(event, vname)
            except AttributeError:
                # try getting the variable from extra_vars
                value = getattr(extra_vars, ob)

            if ob.endswith('_abs'):
                value = abs(value)

            if hasUnitMeV(vname):
                value = value / 1000. # convert from MeV to GeV

            self.hists_d[ob]['truth'].Fill(value, w)

    def fillResponse(self, event_reco, event_truth):
        w_reco = getattr(event_reco, self.wname)
        w_truth = getattr(event_truth, self.wname_mc)

        for ob in self.hists_d:
            vname_reco = obsConfig_dict[ob]['reco']
            value_reco = getattr(event_reco, vname_reco)

            vname_truth = obsConfig_dict[ob]['truth']
            value_truth = getattr(event_truth, vname_truth)

            if ob.endswith('_abs'):
                value_reco = abs(value_reco)
                value_truth = abs(value_truth)

            if hasUnitMeV(vname_truth):
                value_truth = value_truth / 1000. # convert from MeV to GeV

            self.hists_d[ob]['response'].Fill(value_reco, value_truth, w_reco)
            self.hists_d[ob]['response_mcweight'].Fill(value_reco, value_truth, w_truth)

    def computeCorrections(self):
        for ob in self.hists_d:
            self.hists_d[ob]['acceptance'] = getAcceptanceCorrection(
                h2d_response = self.hists_d[ob]['response'],
                h_reco = self.hists_d[ob]['reco'],
                hname = f"Acceptance_{ob}",
                flow = True
            )

            self.hists_d[ob]['acceptance_noflow'] = getAcceptanceCorrection(
                h2d_response = self.hists_d[ob]['response'],
                h_reco = self.hists_d[ob]['reco'],
                hname = f"Acceptance_noflow_{ob}",
                flow = False
            )

            self.hists_d[ob]['efficiency'] = getEfficiencyCorrection(
                h2d_response = self.hists_d[ob]['response_mcweight'],
                h_mctruth = self.hists_d[ob]['truth'],
                hname = f"Efficiency_{ob}",
                flow = True
            )

            self.hists_d[ob]['efficiency_noflow'] = getEfficiencyCorrection(
                h2d_response = self.hists_d[ob]['response_mcweight'],
                h_mctruth = self.hists_d[ob]['truth'],
                hname = f"Efficiency_noflow_{ob}",
                flow = False
            )

            self.hists_d[ob]['efficiency_wreco'] = getEfficiencyCorrection(
                h2d_response = self.hists_d[ob]['response'],
                h_mctruth = self.hists_d[ob]['truth'],
                hname = f"Efficiency_wreco_{ob}",
                flow = True
            )

            self.hists_d[ob]['efficiency_wreco_noflow'] = getEfficiencyCorrection(
                h2d_response = self.hists_d[ob]['response'],
                h_mctruth = self.hists_d[ob]['truth'],
                hname = f"Efficiency_wreco_noflow_{ob}",
                flow = False
            )

    def write_to_file(self):
        for ob in self.hists_d:
            subdir = self.outfile.mkdir(ob)
            subdir.cd()
            for hname in self.hists_d[ob]:
                self.hists_d[ob][hname].Write()

        self.outfile.Close()