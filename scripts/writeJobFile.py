import os
import sys
from datasets import writeDataFileLists
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('sample', type=str, help="Sample name")
parser.add_argument('-d', '--dataset-config', type=str, required=True,
                    help="Path to the dataset yaml configuration file")
parser.add_argument('-o', '--outdir', type=str, required=True,
                    help="Output directory for the batch jobs")
parser.add_argument('-c', '--subcampaigns', choices=['mc16a', 'mc16d', 'mc16e'],
                    type=str, default='mc16e',
                    help="MC production subcampaign")
parser.add_argument('-n', '--njobs', type=int, default=1,
                    help="Number of jobs to run")
parser.add_argument('-s', '--submit-dir', type=str,
                    help="Directory to write job scripts and input lists. If none, set to outdir")
parser.add_argument('-g', '--grid-proxy', default="$HOME/x509up_u$(id -u)",
                    help="Grid proxy for accessing files via xrootd")
parser.add_argument('-p', '--padding', type=float, default=-99.,
                    help="Value to pad dummy events")
parser.add_argument('-k', '--klfitter-ll', type=float, default=-52.,
                    help="Cut on KLFitter log likelihood")

args = parser.parse_args()

# Get the top directory of the package
ntupler_dir = os.getenv('SourceDIR')
if ntupler_dir is None:
    sys.exit("SourceDIR is not set. Abort.")

template_header = """#!/bin/bash
#PBS -t 0-{njobs}
#PBS -o {outdir}/$PBS_JOBID.out
#PBS -j oe
#PBS -m abe
#PBS -M {email}
#PBS -V

export FRONTIER="(http://frontier.triumf.ca:3128/ATLAS_frontier)(proxyurl=http://lcg-adm1.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm2.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm3.sfu.computecanada.ca:3128)"

# for testing/debugging on local host
if [ ! -v PBS_JOBID ]; then PBS_JOBID=42; fi
if [ ! -v PBS_ARRAYID ]; then PBS_ARRAYID=0; fi

echo HOSTNAME=$HOSTNAME

TMPDIR=/tmp/$USER/$(date +'%Y%m%d%H%M%S')
mkdir -p $TMPDIR
cd $TMPDIR
echo "Change to work directory: $TMPDIR"

"""

template_mntuple = """
# set up environment
source {ntupler_dir}/setup_atlas.sh
# grid proxy
export X509_USER_PROXY={proxy}

echo "SourceDIR = $SourceDIR"
echo "PWD = $PWD"

# input files
InputFiles_Reco={infiles_reco}
InputFiles_Parton={infiles_parton}
InputFiles_Particle={infiles_particle}
InputFiles_SumW={infiles_sumw}

echo InputFiles_Reco=$InputFiles_Reco
echo InputFiles_Parton=$InputFiles_Parton
echo InputFiles_Particle=$InputFiles_Particle
echo InputFiles_SumW=$InputFiles_SumW

# output directory
OUTDIR={outdir}
echo OUTDIR=$OUTDIR

# start running
python3 $SourceDIR/scripts/processMiniNtuples.py -n {name}_$PBS_ARRAYID -o $OUTDIR -r $InputFiles_Reco -w $InputFiles_SumW -t $InputFiles_Parton -p $InputFiles_Particle

# clean up
cd /tmp
rm -rf $TMPDIR
"""

template_nparray = """
# set up environment
source {ntupler_dir}/setup_lcg.sh

echo "SourceDIR = $SourceDIR"
echo "PWD = $PWD"

inFileNamePrefix={outdir}/{name}_$PBS_ARRAYID
OUTDIR={outdir}/npz

# parton level
# e+jets
python3 $SourceDIR/scripts/makeNumpyArrays.py $inFileNamePrefix_parton_ejets -t parton -p {padding} -l {llcut} -o $OUTDIR/{name}_$PBS_ARRAYID_parton_ejets.npz
# mu+jets
python3 $SourceDIR/scripts/makeNumpyArrays.py $inFileNamePrefix_parton_mjets -t parton -p {padding} -l {llcut} -o $OUTDIR/{name}_$PBS_ARRAYID_parton_mjets.npz

# particle level
# e+jets
python3 $SourceDIR/scripts/makeNumpyArrays.py $inFileNamePrefix_particle_ejets -t particle -p {padding} -o $OUTDIR/{name}_$PBS_ARRAYID_particle_ejets.npz
# mu+jets
python3 $SourceDIR/scripts/makeNumpyArrays.py $inFileNamePrefix_particle_mjets -t particle -p {padding} -o $OUTDIR/{name}_$PBS_ARRAYID_particle_mjets.npz

# clean up
cd /tmp
rm -rf $TMPDIR
"""

vdict = {}
vdict['ntupler_dir'] = ntupler_dir
vdict['njobs'] = args.njobs-1
vdict['email'] = os.environ.get('USER')+"@phas.ubc.ca"
vdict['name'] = 'mntuple_'+args.sample
vdict['proxy'] = args.grid_proxy
vdict['padding'] = args.padding
vdict['llcut'] = args.klfitter_ll

# output directory
if not os.path.isdir(args.outdir):
    print("Create output directory: {}".format(args.outdir))
    os.makedirs(args.outdir)
    #os.symlink(args.outdir, 'tmplink')
    #os.rename('tmplink', '/home/ztao/data/batch_output/NtupleTT/latest')
vdict['outdir'] = args.outdir

# submit directory
if args.submit_dir is None:
    args.submit_dir = args.outdir

# input files
datalists = writeDataFileLists(args.dataset_config, args.sample,
                               args.subcampaigns, args.submit_dir, args.njobs)

assert(datalists['tt'] != [])
vdict['infiles_reco'] = datalists['tt'][0].replace('_tt_0.txt', '_tt_${PBS_ARRAYID}.txt')
actual_njobs = len(datalists['tt'])
if actual_njobs != args.njobs:
    print("The actual number of jobs is set to {}".format(actual_njobs))
    vdict['njobs'] = actual_njobs - 1

# FIXME: check if datalists['tt_truth'] or datalists['tt_PL'] is empty
vdict['infiles_parton'] = datalists['tt_truth'][0].replace('_tt_truth_0.txt', '_tt_truth_${PBS_ARRAYID}.txt')
vdict['infiles_particle'] = datalists['tt_PL'][0].replace('_tt_PL_0.txt', '_tt_PL_${PBS_ARRAYID}.txt')
vdict['infiles_sumw'] = datalists['sumWeights'][0].replace('_sumWeights_0.txt', '_sumWeights_${PBS_ARRAYID}.txt')

foutname = os.path.join(args.submit_dir, 'submitJob_'+args.sample+'_'+args.subcampaigns+'.sh')
print("Create job file:", foutname)
fjobfile = open(foutname, 'w')
fjobfile.write((template_header+template_mntuple).format(**vdict))
fjobfile.close()

print("To submit the job to cluster:")
print("qsub -l walltime=<hh:mm:ss>", foutname)

# jobs to convert the output root files to numpy array
foutname2 = os.path.join(args.submit_dir, 'submitJob_'+args.sample+'_'+args.subcampaigns+'_toNumpy.sh')
print("Create job file:", foutname2)
fjobfile = open(foutname2, 'w')
fjobfile.write((template_header+template_nparray).format(**vdict))
fjobfile.close()
