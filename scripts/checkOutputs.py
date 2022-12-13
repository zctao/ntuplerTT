import os
import yaml
import ROOT

def checkNumInputs(dirname):
    inlistdir = os.path.join(dirname, "inputs")
    print(f"Check input files in {inlistdir}")

    indices = set()

    for fname in os.listdir(inlistdir):
        # get the index from the file name
        index_str = os.path.splitext(fname)[0].split('_')[-1]
        indices.add(index_str)

    # return the number of indices
    return len(indices)

def checkJobLogs(dirname):
    # Get the expected number of files from the number of input lists
    njobs_exp = checkNumInputs(dirname)
    njobs_success = 0

    jobid = None

    # Check the job logs
    for fname in os.listdir(dirname):
        # expect log extension '.out'
        fext = os.path.splitext(fname)[-1]
        if fext != '.out':
            continue

        # log name is the job id: 1234_5.out
        jid = os.path.splitext(fname)[0]
        jid = int(jid.split('_')[0])
        if jobid is None:
            jobid = jid
        else:
            if jid > jobid:
                # This is a newer job log with larger id.
                jobid = jid
                # reset previous counts
                njobs_success = 0
            elif jid < jobid:
                # This is an old job log. Skip
                continue

        # open the log file and read the last line
        # exit code
        logname = os.path.join(dirname, fname)
        with open(logname, 'r') as flog:
            last_line = flog.readlines()[-1]

        if not "exit code " in last_line:
            print(f"ERROR: cannot find the exit code in the last line of the log {logname}")
        else:
            # extract the exit code
            exit_code = int(last_line.split('exit code ')[1])
            if exit_code == 0:
                njobs_success += 1

    return str(njobs_success)+'/'+str(njobs_exp)

def checkROOTinDir(dirname):
    print(f"Check ROOT files in {dirname}")
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
            print(f"Failed to open ROOT file {fullname}: {e}")

        if treenames:
            ngood += int(ngoodtrees / len(treenames))

    return str(ngood)+'/'+str(nfiles)

def checkOutputs(jDict, sDict):
    oDict = {}

    for k in jDict:
        if isinstance(jDict[k], dict):
            oDict[k] = checkOutputs(jDict[k], sDict[k])
        else:
            if not sDict[k]: # skip if the job is not yet submitted
                continue

            # get directory name
            dirname = os.path.dirname(jDict[k])

            # check files
            res = checkROOTinDir(dirname)

            # check logs
            logs = checkJobLogs(dirname)

            # write to the result dictionary
            oDict[k] = f"{res} (files) {logs} (jobs)"

    return oDict

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-j", "--job-config", type=str, required = True,
                        help="Config file of jobs that are read to be submitted")

    parser.add_argument("-s", "--submit-config", type=str,
                        help="Config file of job submission status")
    parser.add_argument("-o", "--output", type=str,
                        help="Config file for outputs")

    args = parser.parse_args()

    print(f"Read job config {args.job_config}")
    with open(args.job_config) as f:
        jobs_dict = yaml.load(f, yaml.FullLoader)
    jcfg_names = os.path.splitext(args.job_config)

    if args.submit_config is None:
        args.submit_config = jcfg_names[0] + '_submitted' + jcfg_names[1]
    print(f"Read job submission status from {args.submit_config}")
    with open(args.submit_config) as f:
        submit_dict = yaml.load(f, yaml.FullLoader)

    result_dict = checkOutputs(jobs_dict, submit_dict)

    if args.output is None:
        args.output = jcfg_names[0] + '_results' + jcfg_names[1]
    print(f"Write results to {args.output}")
    with open(args.output, 'w') as outfile:
        yaml.dump(result_dict, outfile)
