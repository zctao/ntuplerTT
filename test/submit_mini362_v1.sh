#!/bin/bash
jobcfg=configs/jobs_mini362_v1/jobfiles.yaml

# obs
python scripts/submitJobs.py ${jobcfg} -c obs

# fakes
python scripts/submitJobs.py ${jobcfg} -c fakes

# nominal
# signal
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar -u nominal

# backgrounds
python scripts/submitJobs.py ${jobcfg} -c detNP -s VV singleTop ttH ttV -u nominal

#
# systCRL (With SF systematics and CR loose selection)
python scripts/submitJobs.py ${jobcfg} -c systCRL -s ttbar
python scripts/submitJobs.py ${jobcfg} -c systCRL -s VV Wjets Zjets singleTop ttH ttV

#
# detNP (detector systematic NP)
systs="CategoryReduction_JET_"
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="EG_"
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MET_"
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

systs="MUON_"
python scripts/submitJobs.py ${jobcfg} -c detNP -s ttbar VV singleTop ttH ttV -u ${systs}

#
# mcWAlt (MC weights and alternative samples)
python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttbar ttbar_hw
python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttbar_amc ttbar_hdamp ttbar_mt169 ttbar_mt176 ttbar_sh
python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s VV VV_syst
python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s singleTop singleTop_DS singleTop_amc singleTop_hw
python scripts/submitJobs.py ${jobcfg} -c mcWAlt -s ttH ttV ttV_syst
