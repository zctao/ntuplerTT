import os
import sys
import subprocess
from datasets import writeDataFileLists

template_header_pbs = """#!/bin/bash
#PBS -t 0-{njobarray}%{max_task}
#PBS -o {outdir}
#PBS -j oe
### #PBS -m abe
### #PBS -M
#PBS -l nodes=1

export FRONTIER="(http://frontier.triumf.ca:3128/ATLAS_frontier)(proxyurl=http://lcg-adm1.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm2.sfu.computecanada.ca:3128)(proxyurl=http://lcg-adm3.sfu.computecanada.ca:3128)"

# for testing/debugging on local host
if [ ! -v PBS_JOBID ]; then PBS_JOBID=42; fi
if [ ! -v PBS_ARRAYID ]; then PBS_ARRAYID=0; fi
"""

template_header_slurm = """#!/bin/bash
#SBATCH --array=0-{njobarray}%{max_task}
#SBATCH --output={outdir}/%A_%a.out
### #SBATCH --mail-type=ALL
### #SBATCH --mail-user=
#SBATCH --mem=4G
#SBATCH --export=NONE
"""

template_env_atlas = """
echo HOSTNAME=$HOSTNAME

# set up environment
source {ntupler_dir}/setup_atlas.sh

# grid proxy
#export X509_USER_PROXY=

echo "SourceDIR = $SourceDIR"
"""

template_env_lcg = """
echo HOSTNAME=$HOSTNAME

# set up environment
source {ntupler_dir}/setup_lcg.sh LCG_100
echo "SourceDIR = $SourceDIR"
"""

template_workdir = """
WorkDIR=#TMP#/$USER/$(date +'%Y%m%d%H%M%S')
mkdir -p $WorkDIR
cd $WorkDIR
echo "Change to work directory: $WorkDIR"
echo "PWD = $PWD"
"""

template_mntuple = """
# output directory
OUTDIR={outdir}
echo OUTDIR=$OUTDIR

# start running
python3 $SourceDIR/scripts/processMiniNtuples.py -n {name}_#ARRAYID# -o $OUTDIR {input_args} {extra_args}

echo exit code $?
"""

template_cleanup = """
# clean up
cd ..
rm -rf $WorkDIR
"""

def writeJobFile_flashy(pars_dict, filename, verbosity=1):
    # PBS jobs on atlas-t3-ubc.westgrid.ca
    # $PBS_ARRAYID, $PBS_JOBID, /tmp

    jobscripts = template_header_pbs + template_env_atlas + template_workdir + template_mntuple + template_cleanup
    jobscripts = jobscripts.format(**pars_dict)
    jobscripts = jobscripts.replace('#ARRAYID#', '${PBS_ARRAYID}')
    jobscripts = jobscripts.replace('#TMP#', '/tmp')

    if verbosity > 0:
        print("Create job file:", filename)
    fjobfile = open(filename, 'w')
    fjobfile.write(jobscripts)
    fjobfile.close()

    if verbosity > 0:
        print("To submit the job to cluster:")
        print("qsub -l walltime=<hh:mm:ss>", filename)

def writeJobFile_atlasserv(pars_dict, filename, verbosity=1):
    # Slurm jobs on atlasserv2.phas.ubc.ca
    # $SLURM_ARRAY_TASK_ID, $SLURM_JOB_ID, /mnt/xrootdg/tmp (for now)
    jobscripts = template_header_slurm + template_env_atlas + template_mntuple
    jobscripts = jobscripts.format(**pars_dict)
    jobscripts = jobscripts.replace('#ARRAYID#', '${SLURM_ARRAY_TASK_ID}')
    jobscripts = jobscripts.replace('#TMP#', '/mnt/xrootdg/tmp') # For now

    if verbosity > 0:
        print("Create job file:", filename)
    fjobfile = open(filename, 'w')
    fjobfile.write(jobscripts)
    fjobfile.close()

    if verbosity > 0:
        print("To submit the job to cluster:")
        print("sbatch --time=<hh:mm:ss>", filename)

def writeJobFile_cedar(pars_dict, filename, verbosity=1):
    # Slurm jobs on cedar.computecanada.ca
    # $SLURM_ARRAY_TASK_ID, $SLURM_JOB_ID, $SLURM_TMPDIR

    # get job template from batchScript
    template_jobfile = subprocess.check_output(['batchScript','RUNPLACEHOLDER']).decode('utf-8')

    # add job directives after #! /bin/bash -l
    template_jobfile = template_jobfile.replace('#! /bin/bash -l\n', 'DIRECTIVES\n')

    template_jobfile = template_jobfile.replace("DIRECTIVES", template_header_slurm.format(**pars_dict))

    # run script
    runscript = template_env_lcg + template_workdir + template_mntuple + template_cleanup
    runscript = runscript.format(**pars_dict)
    runscript = "array_id=${1}\n" + runscript
    runscript = runscript.replace('#ARRAYID#', '${array_id}')
    runscript = runscript.replace('#TMP#', '${SLURM_TMPDIR}')
    # save run script
    fname_run = filename.replace('submitJob', 'runJob')
    if verbosity > 0:
        print("Create run script file:", fname_run)
    frunfile = open(fname_run, 'w')
    frunfile.write(runscript)
    frunfile.close()

    if verbosity > 0:
        print("Create job file:", filename)
    fjobfile = open(filename, 'w')
    fjobfile.write(template_jobfile.replace("RUNPLACEHOLDER", "source {} {}".format(fname_run, "${SLURM_ARRAY_TASK_ID}")))
    fjobfile.close()

    if verbosity > 0:
        print("To submit the job to cluster:")
        print("sbatch --export=None --time=<hh:mm:ss>", filename)

def writeJobFile(
    sample,
    dataset_config,
    outdir,
    subcampaigns = ['mc16a', 'mc16d', 'mc16e'],
    extra_args = '',
    njobs = -1,
    submit_dir = None,
    grid_proxy = None, #'$HOME/x509up_u$(id -u)',
    email = None, #"os.getenv('USER')+@phas.ubc.ca",
    site = 'flashy',
    truth_level = '',
    local_dir = None,
    max_task = None,
    verbosity = 0,
    sumw_config = None
    ):

    # get the type of job manager based on the site
    if site in ['flashy']:
        job_manager = 'torque'
    elif site in ['cedar', 'atlasserv']:
        job_manager = 'slurm'
    else:
        raise RuntimeError(f"Unknown site {site}")

    srcdir = os.getenv('SourceDIR')
    if srcdir is None:
        raise RuntimeError("SourceDIR is not set.")

    # update templates
    global template_env_atlas
    global template_header_pbs
    global template_header_slurm

    if grid_proxy:
        template_env_atlas = template_env_atlas.replace(
            "#export X509_USER_PROXY=", f"export X509_USER_PROXY={grid_proxy}")

    if email:
        if job_manager == 'torque':
            template_header_pbs = template_header_pbs.replace(
                "### #PBS -m abe", "#PBS -m abe")
            template_header_pbs = template_header_pbs.replace(
                "### #PBS -M", f"#PBS -M {email}")
        elif job_manager == 'slurm':
            template_header_slurm = template_header_slurm.replace(
                "### #SBATCH --mail-type=ALL", "#SBATCH --mail-type=ALL")
            template_header_slurm = template_header_slurm.replace(
                "### #SBATCH --mail-user=", f"#SBATCH --mail-user={email}")

    if not max_task:
        if job_manager == 'torque':
            template_header_pbs = template_header_pbs.replace(
                '#PBS -t 0-{njobarray}%{max_task}', '#PBS -t 0-{njobarray}')
        elif job_manager == 'slurm':
            template_header_slurm = template_header_slurm.replace(
                '#SBATCH --array=0-{njobarray}%{max_task}',
                '#SBATCH --array=0-{njobarray}')

    # Job parameters
    params_dict = {
        'ntupler_dir' : srcdir,
        'njobarray' : njobs - 1,
        'name' : sample,
        'extra_args' : extra_args,
        'outdir' : outdir,
        'max_task' : max_task
    }

    ########
    # output diretory
    if not os.path.isdir(outdir):
        if verbosity > 0:
            print(f"Create output directory: {outdir}")
        os.makedirs(outdir)

    # submit directory
    if not submit_dir:
        submit_dir = outdir

    ########
    # Create input file lists
    datalists = writeDataFileLists(
        dataset_config,
        sample,
        subcampaigns,
        outdir = os.path.join(submit_dir, 'inputs'),
        njobs = njobs,
        host = site,
        truthLevel = truth_level,
        localDir = local_dir,
        quiet = verbosity < 1)

    actual_njobs = len(datalists['tt'])
    assert(actual_njobs != 0)
    if actual_njobs != njobs:
        if verbosity > 0:
            print(f"The actual number of jobs is {actual_njobs}")
        params_dict['njobarray'] = actual_njobs - 1

    # Input files
    fin_reco = datalists['tt'][0].replace('_tt_0.txt', '_tt_#ARRAYID#.txt')
    # '#ARRAYID#' is to be replaced with proper env variables
    params_dict['input_args'] = f"-r {fin_reco}"

    if 'tt_truth' in datalists:
        fin_truth = datalists['tt_truth'][0].replace('_tt_truth_0.txt', '_tt_truth_#ARRAYID#.txt')
        params_dict['input_args'] += f" -t {fin_truth}"

    if 'tt_PL' in datalists:
        fin_PL = datalists['tt_PL'][0].replace('_tt_PL_0.txt', '_tt_PL_#ARRAYID#.txt')
        params_dict['input_args'] += f" -p {fin_PL}"

    if sumw_config is None:
        # infer the sum weights config file name based on dataset_config
        # replace the prefix of the dataset config file name with 'sumWeights'
        sumw_config = os.path.basename(dataset_config)
        sumw_config = 'sumWeights'+sumw_config[sumw_config.find('_'):]
        sumw_config = os.path.join(os.path.dirname(dataset_config), sumw_config)

    if sample != 'data':
        # check the sum weight config file exists
        assert(os.path.isfile(sumw_config))
        # convert it to absolute path
        sumw_config = os.path.abspath(sumw_config)

        # add to input_args
        params_dict['input_args'] += f" -w {sumw_config}"

    ########
    # job file name
    foutname = f"submitJob_{sample}_{'_'.join(subcampaigns)}.sh"
    foutname = os.path.join(submit_dir, foutname)
    foutname = os.path.realpath(foutname)

    # write job file
    if site == 'flashy':
        writeJobFile_flashy(params_dict, foutname, verbosity)
    elif site == 'atlasserv':
        writeJobFile_atlasserv(params_dict, foutname, verbosity)
    elif site == 'cedar':
        writeJobFile_cedar(params_dict, foutname, verbosity)
    else:
        raise RuntimeError(f"Unknown job manager {job_manager}")

    return foutname

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('sample', type=str, help="Sample name")
    parser.add_argument('-d', '--dataset-config', type=str, required=True,
                        help="Path to the dataset yaml configuration file")
    parser.add_argument('-o', '--outdir', type=str, required=True,
                        help="Output directory for the batch jobs")
    parser.add_argument('-c', '--subcampaigns', nargs='+', default=['mc16e'],
                        help="MC production subcampaign or data taking year")
    parser.add_argument('-a', '--extra-args', type=str, default='',
                        help="Extra arguments to be passed to processMiniNtuples.py")
    parser.add_argument('-n', '--njobs', type=int, default=-1,
                        help="Number of jobs to run. If non-positive, set the number of jobs such that there is one input file per job")
    parser.add_argument('--submit-dir', type=str,
                        help="Directory to write job scripts and input lists. If none, set to outdir")
    parser.add_argument('-g', '--grid-proxy', #default="$HOME/x509up_u$(id -u)",
                        help="Grid proxy for accessing files via xrootd")
    parser.add_argument('-e', '--email', type=str,
                        default="os.getenv('USER')+'@phas.ubc.ca'")
    parser.add_argument('-s', '--site', choices=['flashy', 'cedar', 'atlasserv'],
                        default='flashy',
                        help="Host to run batch jobs")
    parser.add_argument('-t', '--truth-level',
                        choices=['parton', 'particle', ''], default='',
                        help="truth levels")
    parser.add_argument('-l', '--local-dir', type=str, default=None,
                        help="Look for sample files in the local directory if provided")
    parser.add_argument('-m', '--max-tasks', type=int,
                        help="Max number of active tasks at any one time")
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help="Verbosity level")
    parser.add_argument('-w', '--sumw-config', type=str, default=None,
                        help="Path to th sum weights yaml config file. If None, infer the file name based on dataset config")

    args = parser.parse_args()

    try:
        writeJobFile(
            args.sample,
            args.dataset_config,
            args.outdir,
            subcampaigns = args.subcampaigns,
            extra_args = args.extra_args,
            njobs = args.njobs,
            submit_dir = args.submit_dir,
            grid_proxy = args.grid_proxy,
            email = eval(args.email),
            site = args.site,
            truth_level = args.truth_level,
            local_dir = args.local_dir,
            max_task = args.max_tasks,
            verbosity = args.verbosity,
            sumw_config = args.sumw_config
        )
    except:
        print("Failed to generate job files.")
