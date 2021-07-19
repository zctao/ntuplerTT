import os
from datasets import getInputFileNames

template_header_pbs = """#!/bin/bash
#PBS -t 0-{njobarray}%{maxtasks}
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
#SBATCH --array=0-{njobarray}%{maxtasks}
#SBATCH --output={outdir}/%A_%a.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user={email}
#SBATCH --mem=4G
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

template_nparray = """
python3 $SourceDIR/scripts/makeNumpyArrays.py {inputs} -t {truthLevel} -p {padding} -l {llcut} -o {outdir}/{name}_#ARRAYID#_{truthLevel}_{channel}.npz

# clean up
cd ..
rm -rf $WorkDIR

if [ $? -ne 0 ]; then
    exit $?
fi
"""

def splitFilesBySize(filepath_lists, npartitions):
    assert(npartitions>0 and isinstance(npartitions, int))

    # output is a 2D list
    outlist = [[]]
    
    file_sizes = []
    for fpath in filepath_lists:
        try:
            file_sizes.append(os.path.getsize(fpath))
        except:
            file_sizes.append(1)

    total_size = sum(file_sizes)

    current_size = 0
    for fpath, fsize in zip(filepath_lists, file_sizes):
        if current_size >= total_size / npartitions:
            current_size = 0
            # add a new list
            outlist.append([])

        # add file path to the current list
        outlist[-1].append(fpath)
        current_size += fsize

    return outlist

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('ntuple_list', type=str,
                        help="Lists of input root files")
    parser.add_argument('-o', '--output-dir', type=str, required=True,
                        help="Output directory")
    parser.add_argument('-n', '--njobs', type=int, default=1,
                        help="Number of jobs to split into")
    parser.add_argument('--submit-dir', type=str,
                        help="Directory to submit jobs")
    parser.add_argument('-k', '--klfitter-ll', type=float, default=-52.,
                        help="Cut on KLFitter log likelihood")
    parser.add_argument('-p', '--padding', type=float, default=-99.,
                        help="Value to pad dummy events")
    parser.add_argument('-e', '--email', type=str,
                        default="os.getenv('USER')+'@phas.ubc.ca'")
    parser.add_argument('-s', '--site', choices=['flashy', 'cedar'],
                        default='flashy',
                        help="Host to run batch jobs")
    parser.add_argument('-m', '--max-tasks', type=int, default=8,
                        help="Max number of active tasks at any one time")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Suppress some printouts")

    args = parser.parse_args()

    # submit directory
    if args.submit_dir is None:
        args.submit_dir = args.output_dir

    # Job parameters
    srcdir = os.getenv('SourceDIR')
    if srcdir is None:
        sys.exit("SourceDIR is not set. Abort.")

    params_dict = {
        'ntupler_dir' : srcdir,
        'njobarray' : args.njobs - 1,
        'email' : eval(args.email),
        'padding' : args.padding,
        'llcut' : args.klfitter_ll,
        'maxtasks': args.max_tasks
    }

    ######
    # output diretory
    if not os.path.isdir(args.output_dir):
        print("Create output directory: {}".format(args.output_dir))
        os.makedirs(args.output_dir)
    params_dict['outdir'] = args.output_dir

    # inputs
    # get input file names as a list
    ntuple_files = getInputFileNames([args.ntuple_list], check_file=False)

    # extract ntuple name prefix
    # .../<prefix>_0_....root
    name_prefix = os.path.basename(ntuple_files[0]).split('0')[0].rstrip('_')
    params_dict['name'] = name_prefix

    # truth level
    if 'parton' in ntuple_files[0]:
        params_dict['truthLevel'] = 'parton'
    elif 'particle' in ntuple_files[0]:
        params_dict['truthLevel'] = 'particle'

    # channel
    if 'ejets' in ntuple_files[0]:
        params_dict['channel'] = 'ejets'
    elif 'mjets' in ntuple_files[0]:
        params_dict['channel'] = 'mjets'

    # split inputs based on size
    infilelists = splitFilesBySize(ntuple_files, args.njobs)

    actual_njobs = len(infilelists)
    if actual_njobs != args.njobs:
        print("The actual number of jobs is {}".format(actual_njobs))
        params_dict['njobarray'] = actual_njobs - 1

    if not os.path.isdir(os.path.join(args.output_dir, 'inputs')):
        os.makedirs(os.path.join(args.output_dir, 'inputs'))

    fnamebase = os.path.basename(args.ntuple_list)
    fsplittext = os.path.splitext(fnamebase)
    fnamebase = fsplittext[0]+'_{}'+fsplittext[1]
    fname_inputs = os.path.join(args.output_dir, 'inputs', fnamebase)

    for i, filelist in enumerate(infilelists):
        if not args.quiet:
            print("Create file:", fname_inputs.format(i))
        finputs = open(fname_inputs.format(i), 'w')
        for fn in filelist:
            finputs.write(fn+'\n')
        finputs.close()

    params_dict['inputs'] = fname_inputs.format('#ARRAYID#')

    # write the job file
    fname_job = os.path.join(args.submit_dir, 'submitJob_toNumpy_{}_{}_{}.sh'.format(params_dict['name'], params_dict['channel'], params_dict['truthLevel'])) 
    
    if args.site == 'cedar':
        # Slurm jobs on cedar.computecanada.ca
        # get job template from batchScript
        template_jobfile = subprocess.check_output(['batchScript','RUNPLACEHOLDER']).decode('utf-8')

        # add job directives after #! /bin/bash -l
        template_jobfile = template_jobfile.replace('#! /bin/bash -l\n', '#! /bin/bash -l\nDIRECTIVES\n')

        template_jobfile = template_jobfile.replace("DIRECTIVES", template_header_slurm.format(**params_dict))

        # run scripts
        runscript = template_env_lcg + template_nparray
        runscript = runscript.format(**params_dict)
        runscript = "array_id=${1}\n" + runscript
        runscript = runscript.replace('#ARRAYID#', '${array_id}')
        runscript = runscript.replace('#TMP#', '${SLURM_TMPDIR}')
        # save run script
        fname_run = fname_job.replace('submitJob','runJob')
        print("Create run script file:", fname_run)
        file_run = open(fname_run, 'w')
        file_run.write(runscript)
        file_run.close()

        print("Create job file:", fname_job)
        file_job = open(fname_job, 'w')
        file_job.write(template_jobfile.replace("RUNPLACEHOLDER", "source {} {}".format(fname_run, "${SLURM_ARRAY_TASK_ID}")))
        file_job.close()

        print("To submit the job to cluster:")
        print("sbatch --export=None --time=<hh:mm:ss>", fname_job)

    else:
        # PBS jobs on atlas-t3-ubc.westgrid.ca
        jobscripts = template_header_pbs + template_env_lcg + template_nparray
        jobscripts = jobscripts.format(**params_dict)
        jobscripts = jobscripts.replace('#ARRAYID#', '${PBS_ARRAYID}')
        jobscripts = jobscripts.replace('#TMP#', '/tmp')

        print("Create job file:", fname_job)
        file_job = open(fname_job, 'w')
        file_job.write(jobscripts)
        file_job.close()

        print("To submit the job to cluster:")
        print("qsub -l walltime=<hh:mm:ss>", fname_job)
