import numpy as np
import math
import ROOT
#from ROOT.Math import PtEtaPhiMVector, XYZVectorF
from ROOT import TLorentzVector, TVector3

from datasets import getMC16SubCampaign

class varsExtra():
    def __init__(self, thad_prefix, tlep_prefix, ttbar_prefix, compute_energy=True, sum_weights_map=None, is_reco=True):
        # prefix of branches names for ttbar, hadronic top, and leptonic top
        # e.g
        # klfitter_bestPerm_ttbar, klfitter_bestPerm_topHad, klfitter_bestPerm_topLep
        # MC_ttbar_afterFSR, MC_thad_afterFSR, MC_tlep_afterFSR
        # PseudoTop_Reco_ttbar, PseudoTop_Reco_top_had, PseudoTop_Reco_top_lep
        # PseudoTop_Particle_ttbar, PseudoTop_Particle_top_had, PseudoTop_Particle_top_lep
        self.thad_prefix = thad_prefix.rstrip('_')
        self.tlep_prefix = tlep_prefix.rstrip('_')
        self.ttbar_prefix = ttbar_prefix.rstrip('_')

        self.sumWeights_d = sum_weights_map
        self.compute_energy = compute_energy
        self.isReco = is_reco

        # event weight normalization factor
        self.sum_weights = np.empty((1), dtype="float32")

        # event weights normalized to cross section, luminosity, and sum weights
        self.normalized_weight = np.empty((1), dtype="float32")

        # truth event match flag
        self.isMatched = np.empty((1), dtype="int")

        # dummy event indicator
        self.isDummy = np.empty((1), dtype="int")

        # hadronic top kinematics
        self.thad_E = np.empty((1), dtype="float32")
        self.thad_pout = np.empty((1), dtype="float32")

        # leptonic top kinematics
        self.tlep_E = np.empty((1), dtype="float32")
        self.tlep_pout = np.empty((1), dtype="float32")

        # ttbar kinematics
        self.ttbar_E = np.empty((1), dtype="float32")
        self.ttbar_dphi = np.empty((1), dtype="float32")
        self.ttbar_Ht = np.empty((1), dtype="float32")
        self.ttbar_chi = np.empty((1), dtype="float32")
        self.ttbar_ystar = np.empty((1), dtype="float32")
        self.ttbar_yboost = np.empty((1), dtype="float32")

    def set_up_branches(self, tree):
        tree.Branch("isMatched", self.isMatched, "isMatched/I")
        tree.Branch("isDummy", self.isDummy, "isDummy/I")

        wbranch = "normalized_weight" if self.isReco else "normalized_weight_mc"
        tree.Branch(wbranch, self.normalized_weight, wbranch+"/F")

        if self.sumWeights_d is not None:
            tree.Branch("sum_weights", self.sum_weights, "sum_weights/F")

        if self.compute_energy:
            tree.Branch(self.thad_prefix+"_E", self.thad_E, self.thad_prefix+"_E/F")
            tree.Branch(self.tlep_prefix+"_E", self.tlep_E, self.tlep_prefix+"_E/F")
            tree.Branch(self.ttbar_prefix+"_E", self.ttbar_E, self.ttbar_prefix+"_E/F")

        tree.Branch(self.thad_prefix+"_pout", self.thad_pout, self.thad_prefix+"_pout/F")
        tree.Branch(self.tlep_prefix+"_pout", self.tlep_pout, self.tlep_prefix+"_pout/F")

        tree.Branch(self.ttbar_prefix+"_dphi", self.ttbar_dphi, self.ttbar_prefix+"_dphi/F")
        tree.Branch(self.ttbar_prefix+"_Ht", self.ttbar_Ht, self.ttbar_prefix+"_Ht/F")
        tree.Branch(self.ttbar_prefix+"_chi", self.ttbar_chi, self.ttbar_prefix+"_chi/F")
        tree.Branch(self.ttbar_prefix+"_ystar", self.ttbar_ystar, self.ttbar_prefix+"_ystar/F")
        tree.Branch(self.ttbar_prefix+"_yboost", self.ttbar_yboost, self.ttbar_prefix+"_yboost/F")

    def set_match_flag(self, ismatched):
        self.isMatched[0] = ismatched

    def set_dummy_flag(self, isdummy):
        self.isDummy[0] = isdummy

    def write_event(self, event):
        # normalized event weight
        dsid = getattr(event, 'mcChannelNumber')

        if not dsid: # for data files, mcChannelNumber is 0
            if hasattr(event, 'ASM_weight'):
                # Data-driven fakes estimation
                self.normalized_weight[0] = getattr(event, 'ASM_weight')[0]
            else:
                self.normalized_weight[0] = 1
        else:
            # Monte Carlo
            if self.sumWeights_d is not None:
                # look up sum weights from self.sumWeights_d
                if not dsid in self.sumWeights_d:
                    raise RuntimeError(f"Cannot find sum of weights for {dsid}")

                # total sum of weights:
                # infer MC subcampaign based on run number
                subcamp = getMC16SubCampaign(getattr(event, 'runNumber'))
                self.sum_weights[0] = self.sumWeights_d[dsid][subcamp]

                if self.isReco:
                    self.normalized_weight[0] = getattr(event, 'totalWeight_nominal') * getattr(event,'xs_times_lumi') / self.sum_weights[0]
                else:
                    self.normalized_weight[0] = getattr(event, 'weight_mc') * getattr(event, 'xs_times_lumi') / self.sum_weights[0]

        # hadronic top
        th_pt  = getattr(event, self.thad_prefix+'_pt')
        th_eta = getattr(event, self.thad_prefix+'_eta')
        th_y   = getattr(event, self.thad_prefix+'_y')
        th_phi = getattr(event, self.thad_prefix+'_phi')
        th_m   = getattr(event, self.thad_prefix+'_m')
        #th_p4  = PtEtaPhiMVector(th_pt, th_eta, th_phi, th_m)
        th_p4 = TLorentzVector()
        th_p4.SetPtEtaPhiM(th_pt, th_eta, th_phi, th_m)

        if self.compute_energy:
            self.thad_E[0] = th_p4.E()

        # leptonic top
        tl_pt  = getattr(event, self.tlep_prefix+'_pt')
        tl_eta = getattr(event, self.tlep_prefix+'_eta')
        tl_y   = getattr(event, self.tlep_prefix+'_y')
        tl_phi = getattr(event, self.tlep_prefix+'_phi')
        tl_m   = getattr(event, self.tlep_prefix+'_m')
        #tl_p4  = PtEtaPhiMVector(tl_pt, tl_eta, tl_phi, tl_m)
        tl_p4 = TLorentzVector()
        tl_p4.SetPtEtaPhiM(tl_pt, tl_eta, tl_phi, tl_m)

        if self.compute_energy:
            self.tlep_E[0] = tl_p4.E()

        # ttbar
        tt_pt  = getattr(event, self.ttbar_prefix+'_pt')
        tt_eta = getattr(event, self.ttbar_prefix+'_eta')
        tt_phi = getattr(event, self.ttbar_prefix+'_phi')
        tt_m   = getattr(event, self.ttbar_prefix+'_m')
        #tt_p4  = PtEtaPhiMVector(tt_pt, tt_eta, tt_phi, tt_m)
        tt_p4 = TLorentzVector()
        tt_p4.SetPtEtaPhiM(tt_pt, tt_eta, tt_phi, tt_m)

        if self.compute_energy:
            self.ttbar_E[0] = tt_p4.E()

        self.ttbar_dphi[0] = abs(ROOT.VecOps.DeltaPhi(th_phi, tl_phi))
        self.ttbar_Ht[0] = th_pt + tl_pt
        self.ttbar_ystar[0] = (th_y - tl_y) / 2.
        self.ttbar_yboost[0] = (th_y + tl_y) / 2.
        self.ttbar_chi[0] = math.exp( abs(th_y - tl_y) )

        #self.thad_pout[0] = tl_p4.Vect().Unit().Cross(XYZVectorF(0,0,1)).Dot(th_p4.Vect())
        #self.tlep_pout[0] = th_p4.Vect().Unit().Cross(XYZVectorF(0,0,1)).Dot(tl_p4.Vect())
        self.thad_pout[0] = tl_p4.Vect().Unit().Cross(TVector3(0,0,1)).Dot(th_p4.Vect())
        self.tlep_pout[0] = th_p4.Vect().Unit().Cross(TVector3(0,0,1)).Dot(tl_p4.Vect())
