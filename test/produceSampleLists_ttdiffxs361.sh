#!/bin/bash
token=${1}

outdir=configs/datasets/ttdiffxs361
if [[ ! -d ${outdir} ]]
then
    mkdir -p ${outdir}
fi

# With detector systematic NP
echo 'With detector systematic NP'
# ttbar: v05; other MC: v02
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v05 or TTDIFFXS361_v02) and not klfitter' \
       -o ${outdir}/datasets_detNP.yaml

# KLFitter
echo 'with KLFitter'
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v05 or TTDIFFXS361_v02) and klfitter' \
       -o ${outdir}/datasets_detNP_klf.yaml

# With SF systematics and CR loose selection
echo 'With SF systematics and CR loose selection'
# ttbar: v06; other MC: v01
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v06 or TTDIFFXS361_v01) and not klfitter' \
       -o ${outdir}/datasets_systCRL.yaml

# KLFitter
echo 'with KLFitter'
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v06 or TTDIFFXS361_v01) and klfitter' \
       -o ${outdir}/datasets_systCRL_klf.yaml

# MC weights and alternative samples
echo 'MC weights and alternative samples'
# ttbar: v08 or v09; other MC: v03 or v04
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v08 or TTDIFFXS361_v09 or TTDIFFXS361_v03 or TTDIFFXS361_v04) and not klfitter' \
       -o ${outdir}/datasets_mcWAlt.yaml

# KLFitter
echo 'with KLFitter'
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f '(TTDIFFXS361_v08 or TTDIFFXS361_v09 or TTDIFFXS361_v03 or TTDIFFXS361_v04) and klfitter' \
       -o ${outdir}/datasets_mcWAlt_klf.yaml

# data
echo 'Data'
python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f 'physics_Main and not klfitter' \
       -o ${outdir}/datasets_obs.yaml

python scripts/getSampleListsFromGitlab.py ${token} -s MINI362_v1 \
       -f 'physics_Main and klfitter' \
       -o ${outdir}/datasets_obs_klf.yaml
