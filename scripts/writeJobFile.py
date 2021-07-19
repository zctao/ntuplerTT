import os
import sys
import subprocess
from datasets import writeDataFileLists

template_header_pbs = """#!/bin/bash
#PBS -t 0-{njobarray}
#PBS -o {outdir}/$PBS_JOBID.out
#PBS -j oe
#PBS -m abe
#PBS -M {email}
#PBS -l nodes=1
#PBS -V

export FRONTIER="(http://frontier.triumf.ca:3128/ATLAS_frontier)(proxyurl=http://lcg-adm1.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm2.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm3.sfu.computecanada.ca:3128)"

# for testing/debugging on local host
if [ ! -v PBS_JOBID ]; then PBS_JOBID=42; fi
if [ ! -v PBS_ARRAYID ]; then PBS_ARRAYID=0; fi
"""

template_header_slurm = """
#SBATCH --array=0-{njobarray}
#SBATCH --output={outdir}/%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user={email}
#SBATCH --mem=4G
"""

template_env_atlas = """
echo HOSTNAME=$HOSTNAME

# set up environment
source {ntupler_dir}/setup_atlas.sh
# grid proxy
export X509_USER_PROXY={proxy}

echo "SourceDIR = $SourceDIR"
WorkDIR=#TMP#/$USER/$(date +'%Y%m%d%H%M%S')
mkdir -p $WorkDIR
cd $WorkDIR
echo "Change to work directory: $WorkDIR"
echo "PWD = $PWD"
"""

template_env_lcg = """
echo HOSTNAME=$HOSTNAME

# set up environment
source {ntupler_dir}/setup_lcg.sh LCG_100
echo "SourceDIR = $SourceDIR"

WorkDIR=#TMP#/$USER/$(date +'%Y%m%d%H%M%S')
mkdir -p $WorkDIR
cd $WorkDIR
echo "Change to work directory: $WorkDIR"
echo "PWD = $PWD"
"""

template_mntuple = """
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
python3 $SourceDIR/scripts/processMiniNtuples.py -n {name}_#ARRAYID# -o $OUTDIR -r $InputFiles_Reco -w $InputFiles_SumW -t $InputFiles_Parton -p $InputFiles_Particle

# clean up
cd ..
rm -rf $WorkDIR

if [ $? -ne 0 ]; then
    exit $?
fi
"""

def writeJobFile_flashy(pars_dict, filename):
    # PBS jobs on atlas-t3-ubc.westgrid.ca
    # $PBS_ARRAYID, $PBS_JOBID, /tmp

    jobscripts = template_header_pbs + template_env_atlas + template_mntuple
    jobscripts = jobscripts.format(**pars_dict)
    jobscripts = jobscripts.replace('#ARRAYID#', '${PBS_ARRAYID}')
    jobscripts = jobscripts.replace('#TMP#', '/tmp')

    print("Create job file:", filename)
    fjobfile = open(filename, 'w')
    fjobfile.write(jobscripts)
    fjobfile.close()

    print("To submit the job to cluster:")
    print("qsub -l walltime=<hh:mm:ss>", filename)

def writeJobFile_cedar(pars_dict, filename):
    # Slurm jobs on cedar.computecanada.ca
    # $SLURM_ARRAY_TASK_ID, $SLURM_JOB_ID, $SLURM_TMPDIR

    # get job template from batchScript
    template_jobfile = subprocess.check_output(['batchScript','RUNPLACEHOLDER']).decode('utf-8')

    # add job directives after #! /bin/bash -l
    template_jobfile = template_jobfile.replace('#! /bin/bash -l\n', '#! /bin/bash -l\nDIRECTIVES\n')

    template_jobfile = template_jobfile.replace("DIRECTIVES", template_header_slurm.format(**pars_dict))

    # run script
    runscript = template_env_lcg + template_mntuple
    runscript = runscript.format(**pars_dict)
    runscript = "array_id=${1}\n" + runscript
    runscript = runscript.replace('#ARRAYID#', '${array_id}')
    runscript = runscript.replace('#TMP#', '${SLURM_TMPDIR}')
    # save run script
    fname_run = filename.replace('submitJob', 'runJob')
    print("Create run script file:", fname_run)
    frunfile = open(fname_run, 'w')
    frunfile.write(runscript)
    frunfile.close()

    print("Create job file:", filename)
    fjobfile = open(filename, 'w')
    fjobfile.write(template_jobfile.replace("RUNPLACEHOLDER", "source {} {}".format(fname_run, "${SLURM_ARRAY_TASK_ID}")))
    fjobfile.close()

    print("To submit the job to cluster:")
    print("sbatch --export=None --time=<hh:mm:ss>", filename)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('sample', type=str, help="Sample name")
    parser.add_argument('-d', '--dataset-config', type=str, required=True,
                        help="Path to the dataset yaml configuration file")
    parser.add_argument('-o', '--outdir', type=str, required=True,
                        help="Output directory for the batch jobs")
    parser.add_argument('-c', '--subcampaigns',
                        choices=['mc16a', 'mc16d', 'mc16e'], default='mc16e',
                        help="MC production subcampaign")
    parser.add_argument('-n', '--njobs', type=int, default=-1,
                        help="Number of jobs to run. If non-positive, set the number of jobs such that there is one input file per job")
    parser.add_argument('--submit-dir', type=str,
                        help="Directory to write job scripts and input lists. If none, set to outdir")
    parser.add_argument('-g', '--grid-proxy', default="$HOME/x509up_u$(id -u)",
                        help="Grid proxy for accessing files via xrootd")
    parser.add_argument('-e', '--email', type=str,
                        default="os.getenv('USER')+'@phas.ubc.ca'")
    parser.add_argument('-s', '--site', choices=['flashy', 'cedar'],
                        default='flashy',
                        help="Host to run batch jobs")

    args = parser.parse_args()

    ########
    # General job parameters
    srcdir = os.getenv('SourceDIR')
    if srcdir is None:
        sys.exit("SourceDIR is not set. Abort.")

    params_dict = {
        'ntupler_dir' : srcdir,
        'njobarray' : args.njobs - 1,
        'email' : eval(args.email),
        'proxy' : args.grid_proxy,
        'name' : 'mntuple_'+args.sample
    }

    ########
    # output diretory
    if not os.path.isdir(args.outdir):
        print("Create output directory: {}".format(args.outdir))
        os.makedirs(args.outdir)
    params_dict['outdir'] = args.outdir

    # submit directory
    if args.submit_dir is None:
        args.submit_dir = args.outdir

    ########
    # input files
    datalists = writeDataFileLists(args.dataset_config, args.sample,
                                   args.subcampaigns,
                                   os.path.join(args.submit_dir, 'inputs'),
                                   args.njobs, args.site)

    actual_njobs = len(datalists['tt'])
    assert(actual_njobs != 0)
    if actual_njobs != args.njobs:
        print("The actual number of jobs is {}".format(actual_njobs))
        params_dict['njobarray'] = actual_njobs - 1

    params_dict['infiles_reco'] = datalists['tt'][0].replace('_tt_0.txt', '_tt_#ARRAYID#.txt')
    # '#ARRAYID#' is to be replaced with proper env variables

    # TODO: check if datalists['tt_truth'] or datalists['tt_PL'] is empty
    params_dict['infiles_parton'] = datalists['tt_truth'][0].replace('_tt_truth_0.txt', '_tt_truth_#ARRAYID#.txt')

    params_dict['infiles_particle'] = datalists['tt_PL'][0].replace('_tt_PL_0.txt', '_tt_PL_#ARRAYID#.txt')

    params_dict['infiles_sumw'] = datalists['sumWeights'][0].replace('_sumWeights_0.txt', '_sumWeights_#ARRAYID#.txt')

    ########
    # output job file name
    foutname = os.path.join(args.submit_dir, 'submitJob_'+args.sample+'_'+args.subcampaigns+'.sh')


    ########
    # write job file
    if args.site == 'cedar':
        writeJobFile_cedar(params_dict, foutname)
    else:
        writeJobFile_flashy(params_dict, foutname)

    # write ntuple file lists
    truthLevels = ['parton', 'particle']
    channels = ['ejets', 'mjets']

    for tl in truthLevels:
        if datalists['tt_truth'] == [] and tl == 'parton':
            continue
        if datalists['tt_PL'] == [] and tl == 'particle':
            continue
        for ch in channels:
            fname_list = os.path.join(params_dict['outdir'], 'ntuplelist_{}_{}.txt'.format(tl, ch))
            print("Create ntuple list:", fname_list)
            flist = open(fname_list, 'w')
            for j in range(actual_njobs):
                output_ntuple = os.path.join(params_dict['outdir'], params_dict['name']+'_{}_{}_{}.root'.format(j, tl, ch))
                flist.write(output_ntuple+'\n')
            flist.close()
