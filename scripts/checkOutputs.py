import os
import yaml
import ROOT

def checkROOTinDir(dirname):
    print(f"Check ROOT files in {dirname}")
    nfiles = 0
    ngood = 0

    for fname in os.listdir(dirname):
        if not fname.endswith(".root"):
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

            # write to the result dictionary
            oDict[k] = res

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
