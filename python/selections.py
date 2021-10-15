# Event selections

####
# Reco level
def passRecoSelections_ejets(event):
    if hasattr(event, 'passed_resolved_ejets_4j2b'):
        return event.passed_resolved_ejets_4j2b
    else:
        pass4j2b = (event.jet_n > 3) and (event.bjet_n > 1)
        passEL = abs(event.lep_pdgid) == 11
        return pass4j2b and passEL

def passRecoSelections_mjets(event):
    if hasattr(event, 'passed_resolved_mujets_4j2b'):
        return event.passed_resolved_mujets_4j2b
    else:
        pass4j2b = (event.jet_n > 3) and (event.bjet_n > 1)
        passMU = abs(event.lep_pdgid) == 13
        return pass4j2b and passMU

def passRecoSelections(event, recoAlgo='klfitter'):
    if recoAlgo.lower() == 'klfitter':
        # cut on likelihood
        if event.klfitter_logLikelihood < -52:
            return False

    return passRecoSelections_ejets(event) or passRecoSelections_mjets(event)

####
# Particle level
def passPLSelections_ejets(event):
    return event.passedPL and event.passed_resolved_ejets_4j2b

def passPLSelections_mjets(event):
    return event.passedPL and event.passed_resolved_mujets_4j2b

def passPLSelections(event):
    return event.passedPL

####
# Parton level
def getTTbarDecayMode(event):
    # return:
    # 0 if both tops decay leptonically
    # 1 if the t decays leptonically and the tbar decays hadronically
    # 2 if the t decays hadronically and the tbar decays leptonically
    # 3 if both tops decay hadronically
    # -1 for a special case potentially due to a bug from upstream

    tbar_wdecay1_pdgid = event.MC_Wdecay1_from_tbar_afterFSR_pdgid
    tbarIsHadronic = abs(tbar_wdecay1_pdgid) in [1, 2, 3, 4, 5, 6]

    t_wdecay1_pdgid = event.MC_Wdecay1_from_t_afterFSR_pdgid
    tIsHadronic = abs(t_wdecay1_pdgid) in [1, 2, 3, 4, 5, 6]

    # Note:
    # In some events, the pdgID pf one of the decay products of W from either t
    # or tbar is 0. In such events, it is noticed that the value of some branches
    # e.g. MC_thad_afterFSR_y, MC_ttbar_afterFSR_E, is nan or inf
    # These truth events can be matched to valid reco-level events. and the
    # 'isTruthSemileptonic' branch of the matched reco events can be 1
    # Need to investigate the upstream ntuple production
    # Here such events are NOT treated as semileptonic decays
    if tbar_wdecay1_pdgid == 0 or t_wdecay1_pdgid == 0:
        return -1
    else:
        return (tIsHadronic << 1) + tbarIsHadronic

def isSemiLeptonicTTbar(event):
    decaymode = getTTbarDecayMode(event)
    isSemiLeptonic = decaymode == 1 or decaymode == 2

    return isSemiLeptonic

def passTruthSelections_ejets(event):
    decaymode = getTTbarDecayMode(event)

    if decaymode == 1:
        # t decays leptonically
        lepIDs = [
            abs(event.MC_Wdecay1_from_t_afterFSR_pdgid),
            abs(event.MC_Wdecay2_from_t_afterFSR_pdgid)
        ]
    elif decaymode == 2:
        # tbar decays leptonically
        lepIDs = [
            abs(event.MC_Wdecay1_from_tbar_afterFSR_pdgid),
            abs(event.MC_Wdecay2_from_tbar_afterFSR_pdgid)
        ]
    else:
        lepIDs = []

    return 11 in lepIDs

def passTruthSelections_mjets(event):
    decaymode = getTTbarDecayMode(event)

    if decaymode == 1:
        # t decays leptonically
        lepIDs = [
            abs(event.MC_Wdecay1_from_t_afterFSR_pdgid),
            abs(event.MC_Wdecay2_from_t_afterFSR_pdgid)
        ]
    elif decaymode == 2:
        # tbar decays leptonically
        lepIDs = [
            abs(event.MC_Wdecay1_from_tbar_afterFSR_pdgid),
            abs(event.MC_Wdecay2_from_tbar_afterFSR_pdgid)
        ]
    else:
        lepIDs = []

    return 13 in lepIDs
    
