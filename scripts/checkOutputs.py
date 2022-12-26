import os
import yaml
import ROOT

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger("checkOutputs")

def checkNumInputs(dirname):
    inlistdir = os.path.join(dirname, "inputs")
    logger.debug(f"Check input files in {inlistdir}")

    indices = set()

    for fname in os.listdir(inlistdir):
        # get the index from the file name
        index_str = os.path.splitext(fname)[0].split('_')[-1]
        indices.add(index_str)

    # return the number of indices
    return len(indices)

def verifyLogs(file_log):
    nevents = 0
    for line in file_log:
        if "processing event #" in line:
            nevt_cur = int(line.split("processing event #")[-1].strip())
            if nevt_cur == 0:
                nevents = 0

            if nevt_cur < nevents:
                # something is wrong
                return False

    return True

def checkJobLogs(dirname, bad_job_indices, verify=False):
    # Get the expected number of jobs from the number of input lists
    njobs_exp = checkNumInputs(dirname)
    njobs_success = 0

    jobids = [None] * njobs_exp

    # Check job logs
    for fname in os.listdir(dirname):
        # expect log extension '.out'
        if os.path.splitext(fname)[-1] != '.out':
            continue

        # expect the log name is the job id: 1234_5.out
        fullid = os.path.splitext(fname)[0]
        jid, arrayid = fullid.split('_')
        jid = int(jid)
        arrayid = int(arrayid)

        if jobids[arrayid] is None or jid > jobids[arrayid]:
            # assume newer jobs have larger ids
            jobids[arrayid] = jid

    # Read the latest logs for all jobs
    for arrayid, jobid in enumerate(jobids):
        if jobid is None:
            bad_job_indices.add(arrayid)
            continue

        logname = os.path.join(dirname, f"{jobid}_{arrayid}.out")
        with open(logname, 'r') as flog:
            last_line = flog.readlines()[-1]
            if verify:
                logOk = verifyLogs(flog)
                if not logOk:
                    logger.critical(f"Something is wrong. Check {logname}")

        if not "exit code " in last_line:
            logger.debug(f"ERROR: cannot find the exit code in the last line of the log {logname}")
            bad_job_indices.add(arrayid)
        else:
            # extract the exit code
            exit_code = int(last_line.split('exit code ')[1])
            if exit_code == 0:
                njobs_success += 1
            else:
                bad_job_indices.add(arrayid)

    return str(njobs_success)+'/'+str(njobs_exp)

def checkROOTinDir(dirname):
    logger.debug(f"Check ROOT files in {dirname}")
    nfiles = 0
    ngood = 0

    for fname in os.listdir(dirname):
        if not fname.endswith(".root"):
            continue

        if fname.endswith("_acc.root") or fname.endswith("_eff.root"):
            continue

        if fname.endswith("_histograms.root"):
            continue

        # found a ROOT file
        nfiles += 1
        fullname = os.path.join(dirname, fname)
        treenames = []
        ngoodtrees = 0

        # try to open it
        try:
            rootfile = ROOT.TFile.Open(fullname)
            keys = rootfile.GetListOfKeys()
            for k in keys:
                if k.GetClassName() != 'TTree': # not TTree, skip
                    continue
                tname = k.GetName()
                if tname in treenames: # Already checked, skip
                    continue
                treenames.append(tname)

                # check number of events
                tree = rootfile.Get(tname)
                if tree.GetEntries() > 0:
                    ngoodtrees += 1
            rootfile.Close()
        except Exception as e:
            logger.debug(f"Failed to open ROOT file {fullname}: {e}")

        if treenames:
            ngood += int(ngoodtrees / len(treenames))

    return str(ngood)+'/'+str(nfiles)

def prepareResub(fname_orig, indices_resub, extra_mem=0):
    dirname = os.path.dirname(fname_orig)
    basename = os.path.basename(fname_orig)
    fname_resub = os.path.join(dirname, 're'+basename)

    # Read the original submit script
    with open(fname_orig, 'r') as forig:
        lines = forig.readlines()

    # modify the line that sets job arrays and write to a new file fname_resub
    with open(fname_resub, 'w') as fresub:
        for line in lines:
            if "#SBATCH --array=" in line:
                fresub.write("#SBATCH --array=" + ",".join([str(x) for x in indices_resub]) + "\n")
            elif '#SBATCH --mem=' in line and extra_mem > 0:
                mem_str = line.split("=")[-1].strip()
                # It is assumed the mem_str is in the unit of GB
                assert(len(mem_str.split('G'))==2)
                mem_cur = int(mem_str.split('G')[0].strip())
                mem_new = mem_cur + extra_mem
                fresub.write(f"#SBATCH --mem={mem_new}G\n")
            else:
                fresub.write(line)

    return os.path.realpath(fname_resub)

def checkOutputs(jDict, sDict, check_root, verify, extra_mem=0):
    oDict = {}
    flist_resub = []

    for k in jDict:
        if isinstance(jDict[k], dict):
            oDict[k], flist = checkOutputs(jDict[k], sDict[k], check_root, verify, extra_mem)
            flist_resub += flist
        else:
            if not sDict[k]: # skip if the job is not yet submitted
                continue

            # get directory name
            dirname = os.path.dirname(jDict[k])
            logger.info(f"Checking {dirname}")

            # indices of jobs to be resubmitted
            jobarray_index_resubmit = set()

            # check files
            if check_root:
                res = checkROOTinDir(dirname)
            else:
                res = 'n/a'

            # check logs
            logs = checkJobLogs(dirname, jobarray_index_resubmit, verify=verify)

            # write to the result dictionary
            res_str = f"{res} (files) {logs} (jobs)"

            if len(jobarray_index_resubmit) > 0:
                res_str += f" failed: {sorted(jobarray_index_resubmit)}"

                # prepare job files to be resubmitted
                fpath_resub = prepareResub(jDict[k], sorted(jobarray_index_resubmit), extra_mem)
                flist_resub.append(fpath_resub)

            oDict[k] = res_str

    return oDict, flist_resub

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-j", "--job-config", type=str, required = True,
                        help="Config file of jobs that are read to be submitted")

    parser.add_argument("-s", "--submit-config", type=str,
                        help="Config file of job submission status")
    parser.add_argument("-o", "--output", type=str,
                        help="Config file for outputs")
    parser.add_argument("-r", "--check-root", action='store_true',
                        help="If True, check the output ROOT files too")
    parser.add_argument("-c", "--check-log", action="store_true",
                        help="If True, check the job logs more carefully")
    parser.add_argument("-m", "--increase-mem", type=int, default=0,
                        help="Amount of extra memory (GB) to request for he failed jobs")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If True, set logging level to DEBUG, else INFO")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info(f"Read job config {args.job_config}")
    with open(args.job_config) as f:
        jobs_dict = yaml.load(f, yaml.FullLoader)
    jcfg_names = os.path.splitext(args.job_config)

    if args.submit_config is None:
        args.submit_config = jcfg_names[0] + '_submitted' + jcfg_names[1]
    logger.info(f"Read job submission status from {args.submit_config}")
    with open(args.submit_config) as f:
        submit_dict = yaml.load(f, yaml.FullLoader)

    logger.info(f"Start checking jobs")
    result_dict, fresub_list = checkOutputs(jobs_dict, submit_dict, check_root=args.check_root, verify=args.check_log, extra_mem=args.increase_mem)

    if args.output is None:
        args.output = jcfg_names[0] + '_results' + jcfg_names[1]
    logger.info(f"Write results to {args.output}")
    with open(args.output, 'w') as outfile:
        yaml.dump(result_dict, outfile)

    logger.info(f"Write list of scripts for resubmitting jobs")
    with open(os.path.join(os.path.dirname(args.output), "resubmit_list.txt"), 'w') as f_resub:
        f_resub.writelines('\n'.join(fresub_list))