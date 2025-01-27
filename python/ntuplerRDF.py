import time
import re
import h5py
import ROOT

from mc_weight_variations import dict_systname_varindex

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

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

def getPrefixTruth(truthLevel, common_prefix=False):
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

    if common_prefix:
        prefix_thad = f"{truthLevel}.{prefix_thad}"
        prefix_tlep = f"{truthLevel}.{prefix_tlep}"
        prefix_ttbar = f"{truthLevel}.{prefix_ttbar}"

    return prefix_thad, prefix_tlep, prefix_ttbar

######
# JIT C++ function
ROOT.gInterpreter.Declare("""
float compute_energy(float pt, float eta, float phi, float mass) {
    return ROOT::Math::PtEtaPhiMVector(pt,eta,phi,mass).E();
}                          
""")

ROOT.gInterpreter.Declare("""
float compute_pout(float pt_1, float eta_1, float phi_1, float mass_1, float pt_2, float eta_2, float phi_2, float mass_2) {
    auto p4_1 = ROOT::Math::PtEtaPhiMVector(pt_1, eta_1, phi_1, mass_1);
    auto p4_2 = ROOT::Math::PtEtaPhiMVector(pt_2, eta_2, phi_2, mass_2);
    return p4_1.Vect().Unit().Cross(ROOT::Math::XYZVector(0,0,1)).Dot(p4_2.Vect());
}                          
""")

ROOT.gInterpreter.Declare("""
float compute_dR(float rapidity1, float phi1, float rapidity2, float phi2) {
    float drap = rapidity1 - rapidity2;
    float dphi = ROOT::Math::VectorUtil::Phi_mpi_pi(phi1 - phi2);
    return std::sqrt(drap*drap+dphi*dphi);
}
""")
######

def define_extra_variables(rdf, prefix_thad, prefix_tlep, prefix_ttbar, compute_energy=True):

    # energy
    if compute_energy:
        rdf = rdf \
            .Define(f"{prefix_thad}_E", f"compute_energy({prefix_thad}_pt, {prefix_thad}_eta, {prefix_thad}_phi, {prefix_thad}_m)") \
            .Define(f"{prefix_tlep}_E", f"compute_energy({prefix_tlep}_pt, {prefix_tlep}_eta, {prefix_tlep}_phi, {prefix_tlep}_m)") \
            .Define(f"{prefix_ttbar}_E", f"compute_energy({prefix_ttbar}_pt, {prefix_ttbar}_eta, {prefix_ttbar}_phi, {prefix_ttbar}_m)")

    # pout
    rdf = rdf \
        .Define(f"{prefix_thad}_pout", f"compute_pout({prefix_tlep}_pt, {prefix_tlep}_eta, {prefix_tlep}_phi, {prefix_tlep}_m, {prefix_thad}_pt, {prefix_thad}_eta, {prefix_thad}_phi, {prefix_thad}_m)") \
        .Define(f"{prefix_tlep}_pout", f"compute_pout({prefix_thad}_pt, {prefix_thad}_eta, {prefix_thad}_phi, {prefix_thad}_m, {prefix_tlep}_pt, {prefix_tlep}_eta, {prefix_tlep}_phi, {prefix_tlep}_m)")

    # dphi
    rdf = rdf \
        .Define(f"{prefix_ttbar}_dphi", f"abs(ROOT::VecOps::DeltaPhi({prefix_thad}_phi,{prefix_tlep}_phi))") \
        .Define(f"{prefix_ttbar}_Ht", f"{prefix_thad}_pt+{prefix_tlep}_pt") \
        .Define(f"{prefix_ttbar}_ystar", f"({prefix_thad}_y-{prefix_tlep}_y)/2.") \
        .Define(f"{prefix_ttbar}_yboost", f"({prefix_thad}_y+{prefix_tlep}_y)/2.") \
        .Define(f"{prefix_ttbar}_chi", f"exp(std::abs({prefix_thad}_y-{prefix_tlep}_y))")
    
    return rdf

def define_dR_variables(rdf, recoAlgo, truthLevel):
    ######
    # dR between the reconstructed and truth-level top quarks
    prefix_reco_thad, prefix_reco_tlep, prefix_reco_ttbar = getPrefixReco(recoAlgo)
    prefix_truth_thad, prefix_truth_tlep, prefix_truth_ttbar = getPrefixTruth(truthLevel)

    rdf = rdf \
        .Define("dR_thad", f"compute_dR({prefix_reco_thad}_y, {prefix_reco_thad}_phi, {prefix_truth_thad}_y, {prefix_truth_thad}_phi)") \
        .Define("dR_tlep", f"compute_dR({prefix_reco_tlep}_y, {prefix_reco_tlep}_phi, {prefix_truth_tlep}_y, {prefix_truth_tlep}_phi)")

    ######
    # dR between the reco-level and truth-level top decay products
    if truthLevel == "parton":
        rdf = rdf \
            .Define("t_islep", "abs(MC_Wdecay1_from_t_afterFSR_pdgid) > 10") \
            .Define("t_wd1_oddID", "MC_Wdecay1_from_t_afterFSR_pdgid%2 == 1") \
            .Define("tbar_wd1_oddID", "MC_Wdecay1_from_tbar_afterFSR_pdgid%2 == 1")

        rdf = rdf \
            .Define("MC_lq1_y", "t_islep ? MC_Wdecay1_from_tbar_afterFSR_y : MC_Wdecay1_from_t_afterFSR_y") \
            .Define("MC_lq1_phi", "t_islep ? MC_Wdecay1_from_tbar_afterFSR_phi : MC_Wdecay1_from_t_afterFSR_phi")

        rdf = rdf \
            .Define("MC_lq2_y", "t_islep ? MC_Wdecay2_from_tbar_afterFSR_y : MC_Wdecay2_from_t_afterFSR_y") \
            .Define("MC_lq2_phi", "t_islep ? MC_Wdecay2_from_tbar_afterFSR_phi : MC_Wdecay2_from_t_afterFSR_phi")

        rdf = rdf \
            .Define("MC_lep_y", "t_islep ? (t_wd1_oddID ? MC_Wdecay1_from_t_afterFSR_y : MC_Wdecay2_from_t_afterFSR_y) : (tbar_wd1_oddID ? MC_Wdecay1_from_tbar_afterFSR_y : MC_Wdecay2_from_tbar_afterFSR_y)") \
            .Define("MC_lep_phi", "t_islep ? (t_wd1_oddID ? MC_Wdecay1_from_t_afterFSR_phi : MC_Wdecay2_from_t_afterFSR_phi) : (tbar_wd1_oddID ? MC_Wdecay1_from_tbar_afterFSR_phi : MC_Wdecay2_from_tbar_afterFSR_phi)")

        rdf = rdf \
            .Define("MC_nu_y", "t_islep ? (t_wd1_oddID ? MC_Wdecay2_from_t_afterFSR_y : MC_Wdecay1_from_t_afterFSR_y) : (tbar_wd1_oddID ? MC_Wdecay2_from_tbar_afterFSR_y : MC_Wdecay1_from_tbar_afterFSR_y)") \
            .Define("MC_nu_phi", "t_islep ? (t_wd1_oddID ? MC_Wdecay2_from_t_afterFSR_phi : MC_Wdecay1_from_t_afterFSR_phi) : (tbar_wd1_oddID ? MC_Wdecay2_from_tbar_afterFSR_phi : MC_Wdecay1_from_tbar_afterFSR_phi)")

    elif truthLevel == "particle":
        # TODO: dR between particle-level and reco-level jets as identified from top decays
        pass

    # reco level
    #rdf = rdf.Define("reco_lep_eta", "lep_eta").Define("reco_lep_phi", "lep_phi")
    if recoAlgo.lower() == 'klfitter':
        rdf = rdf \
            .Define("nu_eta", "klfitter_model_nu_eta") \
            .Define("nu_phi", "klfitter_model_nu_phi") \
            .Define("reco_lq1_eta", "jet_eta[klfitter_model_lq1_jetIndex]") \
            .Define("reco_lq1_phi", "jet_phi[klfitter_model_lq1_jetIndex]") \
            .Define("reco_lq2_eta", "jet_eta[klfitter_model_lq2_jetIndex]") \
            .Define("reco_lq2_phi", "jet_phi[klfitter_model_lq2_jetIndex]")
    elif recoAlgo.lower() == 'pseudotop':
        rdf = rdf \
            .Define("nu_eta", "PseudoTop_Reco_nu_eta") \
            .Define("nu_phi", "PseudoTop_Reco_nu_phi") \
            .Define("reco_lq1_eta", "jet_eta[PseudoTop_Reco_lq1_jetIndex]") \
            .Define("reco_lq1_phi", "jet_phi[PseudoTop_Reco_lq1_jetIndex]") \
            .Define("reco_lq2_eta", "jet_eta[PseudoTop_Reco_lq2_jetIndex]") \
            .Define("reco_lq2_phi", "jet_phi[PseudoTop_Reco_lq2_jetIndex]")

    rdf = rdf \
        .Define("dR_lq1", "std::min(compute_dR(reco_lq1_eta, reco_lq1_phi, MC_lq1_y, MC_lq1_phi), compute_dR(reco_lq1_eta, reco_lq1_phi, MC_lq2_y, MC_lq2_phi))") \
        .Define("dR_lq2", "std::min(compute_dR(reco_lq2_eta, reco_lq2_phi, MC_lq1_y, MC_lq1_phi), compute_dR(reco_lq2_eta, reco_lq2_phi, MC_lq2_y, MC_lq2_phi))") \
        .Define("dR_lep", "compute_dR(lep_eta, lep_phi, MC_lep_y, MC_lep_phi)") \
        .Define("dR_nu", "compute_dR(nu_eta, nu_phi, MC_nu_y, MC_nu_phi)")

    return rdf

def define_weight_variations(rdf, weight_component):
    # match columns with the prefix
    weight_prefix = f"^{weight_component}_"
    p = re.compile(weight_prefix)
    weight_variations_list = [str(col) for col in rdf.GetColumnNames() if p.search(str(col))]

    for weight_var in weight_variations_list:
        # check column type
        if 'ROOT::VecOps::RVec' in rdf.GetColumnType(weight_var):
            # need to flatten the branch
            # get the size of the vector
            nvec = rdf.Define("nsize", f"{weight_var}.size()").Min("nsize").GetValue()
            # assume the weight variation branches are of the same length for each event
            # TODO check Max and Min is the same?

            for i in range(int(nvec)):
                rdf = rdf.Define(f"{weight_var}_{i}", f"{weight_var}[{i}]")
        else:
            # no action required
            pass

    return rdf

def define_generator_weights(rdf, treename=None):
    branch_name = "mc_generator_weights" if treename is None else f"{treename}.mc_generator_weights"

    if not rdf.HasColumn(branch_name):
        logger.warning(f"Cannot store MC generator weight variations: no branch '{branch_name}'")
        return rdf

    # Get dsid
    dsid = rdf.Min('mcChannelNumber').GetValue()
    # check if all events have the same dsid
    if dsid != rdf.Max('mcChannelNumber').GetValue():
        raise RuntimeError("Events in the samples are of mixed DSIDs! Cannot make branches for the generator weight variations at the moment.")

    # check if dsid is available in dict_systname_varindex
    if not dsid in dict_systname_varindex:
        raise RuntimeError(f"DSID {dsid} not in the weight variation dictionary!")

    varindex_dsid_d = dict_systname_varindex[dsid]

    for varname, wname in varindex_dsid_d.items():
        # skip if PLACEHOLDER
        if "PLACEHOLDER" in varname:
            continue

        if isinstance(wname, int):
            # Skip for now if wname is an integer
            # In this canse varname is the string extracted from the sumWeight files and may not be a valid c++ variable name for calling RDataFrame::Define
            continue
        else:
            # Use wname to look up the weight index
            windex = varindex_dsid_d[wname]

            rdf = rdf.Define(f"mc_generator_weights_{varname}", f"{branch_name}[{windex}]")

    return rdf

def SelectColumns(rdf, recoAlgo=None, truthLevel=None, include_dR=False, include_gen_weights=False, flat_only=True):
    patterns = '^pass_|isMatched|runNumber|eventNumber|^weight_|totalWeight|^normalized_weight|sum_weights|mcChannelNumber'

    # reco level
    if recoAlgo is None:
        pass
    elif recoAlgo.lower() == 'klfitter':
        patterns += "|^klfitter_bestPerm_(?!NoFit)(?!.*eta).*$" # exclude NoFit and eta
    elif recoAlgo.lower() == 'pseudotop':
        patterns += "|^PseudoTop_Reco_(?!.*eta)(?!.*jetIndex).*$" # exclude eta and jetIndex
    else:
        raise RuntimeError(f"Unknown top reconstruction algorithm {recoAlgo}")

    # truth level
    if truthLevel is not None:
        patterns += "|isSemiLeptonic|passesPL"

        if include_gen_weights:
            patterns += f"|mc_generator_weights_"
    
        if truthLevel == "parton":
            patterns += "|MC_(ttbar|tlep|thad)_afterFSR"
        elif truthLevel == "particle":
            patterns += "|PseudoTop_Particle_(top_had|top_lep|ttbar)_"

        if include_dR:
            patterns += "|dR_(thad|tlep|lq1|lq2|lep|nu)"

    p = re.compile(patterns)

    columns = [str(col) for col in rdf.GetColumnNames() if p.search(str(col))]

    # check columns type if needed
    if flat_only:
        flat_columns = []
        for col in columns:
            if not 'ROOT::VecOps::RVec' in rdf.GetColumnType(col):
                flat_columns.append(col)
        return flat_columns
    else:
        return columns

class NtupleRDF():
    def __init__(
        self,
        outputName,
        inputFiles_reco,
        inputFiles_truth = [],
        sumWeights_dict = None,
        recoAlgo = 'klfitter', # ttbar reconstruction algorithm
        truthLevel ='parton',
        treename = 'nominal',
        treename_truth = 'nominal',
        verbose = False
        ):

        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        self.truthLevel = truthLevel
        self.recoAlgo = recoAlgo
        self.sumWeights_d = sumWeights_dict

        logger.info("Read reco-level trees")
        self.tree_reco = ROOT.TChain(treename)

        for infile_reco in inputFiles_reco:
            self.tree_reco.Add(infile_reco)

        nevents_reco = self.tree_reco.GetEntries()
        logger.info(f"Number of events in the reco tree: {nevents_reco}")

        if inputFiles_truth:
            logger.info(f"Read {truthLevel}-level trees")
            self.tree_truth = ROOT.TChain(treename_truth)

            for infile_truth in inputFiles_truth:
                self.tree_truth.Add(infile_truth)

            nevents_truth = self.tree_truth.GetEntries()
            logger.info(f"Number of events in the {truthLevel}-level tree: {nevents_truth}")
        else:
            self.tree_truth = None

        # output file name
        if self.tree_truth:
            self.foutname = f"{outputName}_{recoAlgo}_{truthLevel}_ljets"
        else:
            self.foutname = f"{outputName}_{recoAlgo}_ljets"

    def __call__(
        self,
        maxevents=None,
        saveUnmatchedReco=True,
        saveUnmatchedTruth=True,
        include_dR = False,
        include_gen_weights = False
        ):
        logger.info("Start processing mini-ntuples")

        if maxevents is None:
            #ROOT.EnableImplicitMT()
            # Currently the code crashes with multiple TTrees if enabling multi-threading
            # Running single thread for now
            ROOT.DisableImplicitMT()
        else:
            ROOT.DisableImplicitMT()
            # RDataFrame.Range() does not support multi-threading

        if self.tree_truth is None:
            saveUnmatchedTruth = False

        ######
        # Build tree index
        if self.tree_truth:
            tstart = time.time()
            logger.info(f"Build index for {self.truthLevel}-level trees")
            self.tree_truth.BuildIndex("runNumber", "eventNumber")
            logger.info(f"Add {self.truthLevel}-level trees as friends to the reco-level trees")
            self.tree_reco.AddFriend(self.tree_truth, self.truthLevel)
            tstop = time.time()
            logger.info(f"Building truth tree index took {tstop-tstart:.2f} seconds")

        logger.info("Construct RDataFrame from TTree")
        df = ROOT.RDataFrame(self.tree_reco)
        logger.info(f"Total number of events: {df.Count().GetValue()}")

        # Add progress bar
        ROOT.RDF.Experimental.AddProgressBar(df)

        if maxevents is not None:
            df = df.Range(maxevents)

        ###
        tstart = time.time()
        # Reco-level selections
        # pass either e+jets or mu+jets selections
        #reco_cuts = "passed_resolved_ejets_4j2b != passed_resolved_mujets_4j2b"
        reco_cuts = "el_n+mu_n==1 && jet_n>=4 && bjet_n>=2"

        df = df.Define("pass_reco", reco_cuts)
        df = df.Filter('pass_reco')
        logger.info(f"Number of events after reco cuts: {df.Count().GetValue()}")

        ###
        # extra variables
        df = define_extra_variables(df, *getPrefixReco(self.recoAlgo), compute_energy=True)

        ###
        # normalized event weights
        if df.Max('mcChannelNumber').GetValue() < 1:
            # data sample mcChannelNumber is 0
            if df.HasColumn("ASM_weight"): # data driven fake estimation
                logger.debug("Data-driven fake estimation")
                df = df.Define("normalized_weight", "ASM_weight[0]")
            else:
                logger.debug("Data sample")
                df = df.Define("normalized_weight", '1.')
            df = df.Define("sum_weights", "-1")
        elif self.sumWeights_d:
            # Sum weights
            logger.debug("Sum weights")

            logger.debug("Declaring function GetSumWeights...")
            # declare the sum weights map
            ROOT.gInterpreter.Declare('''
                auto &GetSumWeightsMap() {
                    static std::unordered_map<int, std::unordered_map<std::string, double>> sumwMap;
                    return sumwMap;
                };
            ''')
            # fill the sum weights map from self.sumWeights_d
            sumwMap = ROOT.GetSumWeightsMap()
            for dsid in self.sumWeights_d:
                sumwMap[dsid] = self.sumWeights_d[dsid]

            # https://twiki.cern.ch/twiki/bin/view/AtlasProtected/DataMCForAnalysis
            ROOT.gInterpreter.Declare('''
                double GetSumWeights(int mcChannelNumber, int runNumber) {
                    auto subcamp = "";
                    if (276073 <= runNumber and runNumber <= 311481) {
                        subcamp = "mc16a";
                    } else if (325713 <= runNumber and runNumber <= 340453) {
                        subcamp = "mc16d";
                    } else if (348885 <= runNumber and runNumber <= 364292) {
                        subcamp = "mc16e";
                    }

                    auto &sumwMap = GetSumWeightsMap();
                    return sumwMap[mcChannelNumber][subcamp];
                }
            ''')
            logger.debug("...done!")

            df = df \
                .Define("sum_weights", "GetSumWeights(mcChannelNumber,runNumber)") \
                .Define("normalized_weight", "totalWeight_nominal*xs_times_lumi/sum_weights")

        # event weight systematic variations
        df = define_weight_variations(df, "weight_bTagSF_DL1r_70")
        df = define_weight_variations(df, "weight_jvt")
        df = define_weight_variations(df, "weight_leptonSF")
        df = define_weight_variations(df, "weight_pileup")

        if include_gen_weights:
            try:
                df = define_generator_weights(df)
            except RuntimeError as e:
                logger.warning(f"Failed to add generator weight variations: {e}")

        ###
        # truth tree
        if self.tree_truth:
            logger.debug("Handling the truth tree")
            ###
            # Truth-level selections
            df = df.Define("isMatched", f"runNumber=={self.truthLevel}.runNumber && eventNumber=={self.truthLevel}.eventNumber")

            if self.truthLevel == "parton":
                isSemiLeptonic = "(abs(MC_Wdecay1_from_t_afterFSR_pdgid) > 0 && abs(MC_Wdecay1_from_t_afterFSR_pdgid) < 7) != (abs(MC_Wdecay1_from_tbar_afterFSR_pdgid) > 0 && abs(MC_Wdecay1_from_tbar_afterFSR_pdgid) < 7)"
                df = df.Define("isSemiLeptonic", isSemiLeptonic)

                df = df.Define("pass_truth", "isSemiLeptonic && isMatched && !TMath::IsNaN(MC_thad_afterFSR_y)")

            elif self.truthLevel == "particle":
                #df = df.Define("passesPL", "passedPL")
                df = df.Define("pass_truth", "passesPL && isMatched}")
            else:
                raise RuntimeError(f"Unknown truth level: {self.truthLevel}")

            if not saveUnmatchedReco:
                df = df.Filter("isMatched")
                logger.info(f"Number of truth matched events: {df.Count().GetValue()}")

            # compute extra variableas for truth level
            df = define_extra_variables(df, *getPrefixTruth(self.truthLevel), compute_energy=self.truthLevel!='parton')

            if include_dR:
                # compute dR between the reconstructed and truth-level top quarks
                df = define_dR_variables(df, self.recoAlgo, self.truthLevel)

            # normalized mc weights
            if df.HasColumn("sum_weights"):
                df = df.Define("normalized_weight_mc", "weight_mc*xs_times_lumi/sum_weights")

        # save as numpy arrays
        cols = SelectColumns(df, self.recoAlgo, self.truthLevel, include_dR=include_dR, include_gen_weights=include_gen_weights)
        logger.info("Columns to be stored:")
        logger.info(f"{cols}")

        logger.info("Save as numpy arrays")
        arrays_d = df.AsNumpy(cols)
        tstop = time.time()
        logger.info(f"Total processing time: {tstop-tstart:.2f} seconds")

        logger.info(f"Create output file: {self.foutname}.h5")
        with h5py.File(f"{self.foutname}.h5", "w") as file_arr:
            for vname in arrays_d:
                logger.debug(vname)
                file_arr.create_dataset(vname, data=arrays_d[vname])

        ####
        if saveUnmatchedTruth and self.tree_truth:
            # unfriend trees first
            self.tree_reco.RemoveFriend(self.tree_truth)

            logger.info("Build index for reco-level trees")
            self.tree_reco.BuildIndex("runNumber", "eventNumber")
            logger.info(f"Add reco-level trees as friends to the {self.truthLevel}-level trees")
            self.tree_truth.AddFriend(self.tree_reco, "reco")

            logger.info(f"Construct RDataFrame from {self.truthLevel}-level TTree")
            df_truth = ROOT.RDataFrame(self.tree_truth)
            logger.info(f"Total number of events: {df_truth.Count().GetValue()}")

            # Add progress bar
            ROOT.RDF.Experimental.AddProgressBar(df_truth)

            if maxevents is not None:
                df_truth = df_truth.Range(maxevents)

            tstart_t = time.time()

            # event selection flags
            df_truth = df_truth.Define("isMatched", "runNumber==reco.runNumber && eventNumber==reco.eventNumber")

            # save only the events that do not match to reco level by event ID
            df_truth = df_truth.Filter("!isMatched")

            if self.truthLevel == "parton":
                df_truth = df_truth.Define("isSemiLeptonic", isSemiLeptonic)
                df_truth = df_truth.Define("pass_truth", f"isSemiLeptonic && !TMath::IsNaN(MC_thad_afterFSR_y)")
            else:
                df_truth = df_truth.Define("pass_truth", "passedPL")

            # extra variables
            df_truth = define_extra_variables(df_truth, *getPrefixTruth(self.truthLevel), compute_energy=self.truthLevel!='parton')

            if include_gen_weights:
                try:
                    df_truth = define_generator_weights(df_truth)
                except RuntimeError as e:
                    logger.warning(f"Failed to add generator weight variations: {e}")

            df_truth = df_truth \
                .Define("sum_weights", "GetSumWeights(mcChannelNumber,runNumber)") \
                .Define("normalized_weight_mc", "weight_mc*xs_times_lumi/sum_weights")

            # save as numpy arrays
            cols_truth = SelectColumns(df_truth, truthLevel=self.truthLevel, include_gen_weights=include_gen_weights)
            logger.info("Columns to be stored:")
            logger.info(f"{cols_truth}")
            arrays_umt_d = df_truth.AsNumpy(cols_truth)
            tstop_t= time.time()
            logger.info(f"Total processing time: {tstop_t-tstart_t:.2f} seconds")

            logger.info(f"Create output file: {self.foutname}_unmatched_truth.h5")
            with h5py.File(f"{self.foutname}_unmatched_truth.h5", "w")as file_arr_umt:
                for vname in arrays_umt_d:
                    logger.debug(vname)
                    file_arr_umt.create_dataset(vname, data=arrays_umt_d[vname])
