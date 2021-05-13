import numpy as np

class varsExtra():
    def __init__(self, thad_prefix, tlep_prefix, ttbar_prefix, compute_energy=True, sum_weights=None):
        # prefix of branches names for ttbar, hadronic top, and leptonic top
        # e.g
        # klfitter_bestPerm_ttbar, klfitter_bestPerm_topHad, klfitter_bestPerm_topLep
        # MC_ttbar_afterFSR, MC_thad_afterFSR, MC_tlep_afterFSR
        # PseudoTop_Reco_ttbar, PseudoTop_Reco_top_had, PseudoTop_Reco_top_lep
        # PseudoTop_Particle_ttbar, PseudoTop_Particle_top_had, PseudoTop_Particle_top_lep
        self.thad_prefix = thad_prefix.rstrip('_')
        self.tlep_prefix = tlep_prefix.rstrip('_')
        self.ttbar_prefix = ttbar_prefix.rstrip('_')

        self.sumWeights = sum_weights
        self.compute_energy = compute_energy

        # event weight
        self.normalizedWeight = np.empty((1), dtype="float")

        # truth event match flag
        self.isMatched = np.empty((1), dtype="int")

        # hadronic top kinematics
        self.thad_E = np.empty((1), dtype="float")
        #self.thad_pout = np.empty((1), dtype="float")

        # leptonic top kinematics
        self.tlep_E = np.empty((1), dtype="float")
        #self.tlep_pout = np.empty((1), dtype="float")

        # ttbar kinematics
        self.ttbar_E = np.empty((1), dtype="float")
        #self.ttbar_dphi = np.empty((1), dtype="float")

    def set_up_branches(self, tree):
        tree.Branch("isMatched", self.isMatched, "isMatched/I")

        if self.sumWeights is not None:
            tree.Branch("normedWeight", self.normalizedWeight, "normedWeight/F")

        if self.compute_energy:
            tree.Branch(self.thad_prefix+"_E", self.thad_E, self.thad_prefix+"_E/F")
            tree.Branch(self.tlep_prefix+"_E", self.tlep_E, self.tlep_prefix+"_E/F")
            tree.Branch(self.ttbar_prefix+"_E", self.ttbar_E, self.ttbar_prefix+"_E/F")

    def set_match_flag(self, ismatched):
        self.isMatched[0] = ismatched
