import os
from datasets import datasets
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('sample', type=str, help="Sample name")
parser.add_argument('-n', '--njobs', type=int, default=8,
                    help="Number of jobs to run")
parser.add_argument('-o', '--outdir', type=str,
                    default='/home/ztao/data/batch_output/NtupleTT/latest',
                    help="Output directory")
parser.add_argument('-d', '--datadir', type=str, default='/home/ztao/data/ttbarDiffXs13TeV')
parser.add_argument('-f', '--filename', type=str, default='submitJob.sh',
                    help="Job file name")

args = parser.parse_args()

template = """#!/bin/bash
#PBS -t 0-{njobs}
#PBS -o {outdir}/$PBS_JOBID.out
#PBS -j oe
#PBS -m abe
#PBS -M {email}
#PBS -V

# set up environment
source $HOME/ntuplerTT/setup.sh
echo "SourceDIR = $SourceDIR"
echo "PWD = $PWD"

# local disk of the node
#if [ ! -v PBS_JOBID ]; then PBS_JOBID=42; fi    # for local testing
if [ ! -v PBS_ARRAYID ]; then PBS_ARRAYID=3; fi # for local testing

TMPDIR=/tmp/$USER/$(date +'%Y%m%d%H%M%S')
mkdir -p $TMPDIR
cd $TMPDIR
echo "Work directory: $TMPDIR"

# input files
InputFiles_Reco={infiles_reco}
InputFiles_Parton={infiles_parton}
InputFiles_Particle={infiles_particle}

# output directory
OUTDIR={outdir}

# start running
python3 $SourceDIR/processMiniNtuples.py -r $InputFiles_Reco -t $InputFiles_Parton -p $InputFiles_Particle -n {name}_$PBS_ARRAYID -o $OUTDIR

# copy output to the final destination
#cp $TMPDIR/*.root $OUTDIR/.

# clean up
cd /tmp
rm -rf $TMPDIR
"""

vdict = {}
vdict['njobs'] = args.njobs-1
vdict['email'] = os.environ.get('USER')+"@phas.ubc.ca"
vdict['name'] = 'mntuple_'+args.sample

# output directory
if not os.path.isdir(args.outdir):
    print("Create output directory: {}".format(args.outdir))
    os.makedirs(args.outdir)
    os.symlink(args.outdir, 'tmplink')
    os.rename('tmplink', '/home/ztao/data/batch_output/NtupleTT/latest')
vdict['outdir'] = args.outdir

# input files
def writeInputFileLists(sample_name, njobs, datadir, outdir):
    dspath = datasets.get(sample_name)
    if dspath is None:
        print("Unknown sample:", sample_name)
        print("Registered samples are:", list(datasets.keys()))

    dir_reco = os.path.join(datadir, dspath)+'tt.root'
    dir_truth = os.path.join(datadir, dspath)+'tt_truth.root'
    dir_PL = os.path.join(datadir, dspath)+'tt_PL.root'
    dir_sumw = os.path.join(datadir, dspath)+'sumWeights.root'
    
    files_reco = [os.path.join(dir_reco, fp) for fp in sorted(os.listdir(dir_reco))]
    files_truth = [os.path.join(dir_truth, fp) for fp in sorted(os.listdir(dir_truth))]
    files_PL = [os.path.join(dir_PL, fp) for fp in sorted(os.listdir(dir_PL))]
    files_sumw = [os.path.join(dir_sumw, fp) for fp in sorted(os.listdir(dir_sumw))]

    lists_dir = os.path.join(outdir, 'input_lists')
    if not os.path.isdir(lists_dir):
        print("Create directory", lists_dir)
        os.makedirs(lists_dir)

    inlist_reco = os.path.join(lists_dir, 'input_'+sample_name+'_reco_{}.txt')
    inlist_truth = os.path.join(lists_dir, 'input_'+sample_name+'_truth_{}.txt')
    inlist_PL = os.path.join(lists_dir, 'input_'+sample_name+'_PL_{}.txt')
    inlist_sumw = os.path.join(lists_dir, 'input_'+sample_name+'_sumw_{}.txt')

    nfiles = len(files_reco)
    nfilesPerJob = int(nfiles/njobs)

    for j in range(njobs):
        istart = j*nfilesPerJob
        iend = istart + nfilesPerJob if j < njobs-1 else None

        f_list_reco = open(inlist_reco.format(j), 'w')
        f_list_reco.write('\n'.join(files_reco[istart:iend]))
        f_list_reco.close()

        f_list_truth = open(inlist_truth.format(j), 'w')
        f_list_truth.write('\n'.join(files_truth[istart:iend]))
        f_list_truth.close()

        f_list_PL = open(inlist_PL.format(j), 'w')
        f_list_PL.write('\n'.join(files_PL[istart:iend]))
        f_list_PL.close()

        f_list_sumw = open(inlist_sumw.format(j), 'w')
        f_list_sumw.write('\n'.join(files_sumw[istart:iend]))
        f_list_sumw.close()

    return inlist_reco, inlist_truth, inlist_PL, inlist_sumw

infilelists = writeInputFileLists(args.sample, args.njobs, args.datadir, args.outdir)
    
vdict['infiles_reco'] = infilelists[0].format("$PBS_ARRAYID")
vdict['infiles_parton'] = infilelists[1].format("$PBS_ARRAYID")
vdict['infiles_particle'] = infilelists[2].format("$PBS_ARRAYID")

foutname = os.path.join(args.outdir, args.filename)
fjobfile = open(foutname, 'w')
fjobfile.write(template.format(**vdict))
fjobfile.close()

print("Create job file:", foutname)
print("To submit the job to cluster:")
print("qsub -l walltime=<hh:mm:ss>", foutname)
