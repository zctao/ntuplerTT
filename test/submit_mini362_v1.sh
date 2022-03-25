#!/bin/bash
jobcfg=configs/jobfiles_mini362_v1.yaml

# obs
#python scripts/submitJobs.py ${jobcfg} -c obs -d

# fakes
#python scripts/submitJobs.py ${jobcfg} -c fakes -d

# systCRL
#python scripts/submitJobs.py ${jobcfg} -c systCRL -s ttbar VV Wjets Zjets singleTop ttH ttV -d

# detNP
# nominal
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u nominal

#
# detector

systs="CategoryReduction_JET_Pileup_RhoTopology__1up CategoryReduction_JET_Pileup_RhoTopology__1down"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs} -d

systs="CategoryReduction_JET_BJES_Response__1down CategoryReduction_JET_BJES_Response__1up"
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Detector1__1down CategoryReduction_JET_EffectiveNP_Detector1__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Detector2__1down CategoryReduction_JET_EffectiveNP_Detector2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Mixed1__1down CategoryReduction_JET_EffectiveNP_Mixed1__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Mixed2__1down CategoryReduction_JET_EffectiveNP_Mixed2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Mixed3__1down CategoryReduction_JET_EffectiveNP_Mixed3__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Modelling1__1down CategoryReduction_JET_EffectiveNP_Modelling1__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Modelling2__1down CategoryReduction_JET_EffectiveNP_Modelling2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Modelling3__1down CategoryReduction_JET_EffectiveNP_Modelling3__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Modelling4__1down CategoryReduction_JET_EffectiveNP_Modelling4__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical1__1down CategoryReduction_JET_EffectiveNP_Statistical1__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical2__1down CategoryReduction_JET_EffectiveNP_Statistical2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical3__1down CategoryReduction_JET_EffectiveNP_Statistical3__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical4__1down CategoryReduction_JET_EffectiveNP_Statistical4__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical5__1down CategoryReduction_JET_EffectiveNP_Statistical5__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EffectiveNP_Statistical6__1down CategoryReduction_JET_EffectiveNP_Statistical6__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_Modelling__1down CategoryReduction_JET_EtaIntercalibration_Modelling__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_NonClosure_2018data__1down CategoryReduction_JET_EtaIntercalibration_NonClosure_2018data__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_NonClosure_highE__1down CategoryReduction_JET_EtaIntercalibration_NonClosure_highE__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_NonClosure_negEta__1down CategoryReduction_JET_EtaIntercalibration_NonClosure_negEta__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_NonClosure_posEta__1down CategoryReduction_JET_EtaIntercalibration_NonClosure_posEta__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_EtaIntercalibration_TotalStat__1down CategoryReduction_JET_EtaIntercalibration_TotalStat__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_Flavor_Composition__1down CategoryReduction_JET_Flavor_Composition__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_Flavor_Response__1down CategoryReduction_JET_Flavor_Response__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_DataVsMC_MC16__1down CategoryReduction_JET_JER_DataVsMC_MC16__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_1__1down CategoryReduction_JET_JER_EffectiveNP_1__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_2__1down CategoryReduction_JET_JER_EffectiveNP_2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_3__1down CategoryReduction_JET_JER_EffectiveNP_3__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_4__1down CategoryReduction_JET_JER_EffectiveNP_4__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_5__1down CategoryReduction_JET_JER_EffectiveNP_5__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_6__1down CategoryReduction_JET_JER_EffectiveNP_6__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_JER_EffectiveNP_7restTerm__1down CategoryReduction_JET_JER_EffectiveNP_7restTerm__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_Pileup_OffsetMu__1down CategoryReduction_JET_Pileup_OffsetMu__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_Pileup_OffsetNPV__1down CategoryReduction_JET_Pileup_OffsetNPV__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_Pileup_PtTerm__1down CategoryReduction_JET_Pileup_PtTerm__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_PunchThrough_MC16__1down CategoryReduction_JET_PunchThrough_MC16__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="CategoryReduction_JET_SingleParticle_HighPt__1down CategoryReduction_JET_SingleParticle_HighPt__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="EG_RESOLUTION_ALL__1down EG_RESOLUTION_ALL__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="EG_SCALE_AF2__1down EG_SCALE_AF2__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="EG_SCALE_ALL__1down EG_SCALE_ALL__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MET_SoftTrk_Scale__1down MET_SoftTrk_Scale__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MET_SoftTrk_ResoPara MET_SoftTrk_ResoPerp"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_ID__1down MUON_ID__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_MS__1down MUON_MS__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_SAGITTA_RESBIAS__1down MUON_SAGITTA_RESBIAS__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_SAGITTA_RHO__1down MUON_SAGITTA_RHO__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_SCALE__1down MUON_SCALE__1up"
#python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

# mcWAlt
#python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttbar ttbar_hw -d
#python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttbar_amc ttbar_hdamp ttbar_mt169 ttbar_mt176 ttbar_sh
#python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s VV VV_syst
#python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s singleTop singleTop_DS singleTop_amc singleTop_hw
#python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttH ttV ttV_syst 
