import os
import yaml
import subprocess

def init_dict(job_file_dict, val=False):
    sub_dict = {}
    for k in job_file_dict:
        if isinstance(job_file_dict[k], dict):
            sub_dict[k] = init_dict(job_file_dict[k])
        else:
            sub_dict[k] = val

    return sub_dict

def submit(fname_job, args='', dry_run=False):
    commands = ['qsub']

    if args:
        commands += args.split()

    commands += [fname_job]

    print(" ".join(commands))
    if not dry_run:
        subprocess.run(commands, check=True)

def submitJobs(
    jobs_config, # yaml config of jobs that are ready to be submitted
    category, # detNP, systCRL, mcWAlt, obs, fakes
    samples=['ttbar','singleTop','VV','ttH','ttV','Wjets','Zjets'],
    systematics=['nominal'],
    eras=['mc16a', 'mc16d', 'mc16e'],
    args_string='', # command line arguments to be passed to qsub
    jobs_submitted=None, # yaml files to keep track of the submitted jobs
    resubmit=False, # if True, resubmit the jobs even if they have been submitted
    dry_run=False # if True, print the qsub command instead of executing it
    ):

    # load the dictionary of jobs that are ready to be submitted
    jobs_dict = {}
    try:
        with open(jobs_config) as f:
            jobs_dict = yaml.load(f, yaml.FullLoader)
    except Exception as e:
        print(f"ERROR: failed to open job config file {jobs_config}. Abort...")
        return

    if not jobs_dict:
        print(f"There is no job to be submitted from {jobs_config}")
        return

    # A dictionary to keep track of if or not a job is submitted
    submitted_dict = {}

    if jobs_submitted is None:
        # use the same file name as jobs_config but add a suffix _submitted
        jcfg_names = os.path.splitext(jobs_config)
        jobs_submitted = jcfg_names[0] + '_submitted' + jcfg_names[1]

    if os.path.isfile(jobs_submitted):
        # open and read it
        with open(jobs_submitted) as f:
            submitted_dict = yaml.load(f, yaml.FullLoader)
    else:
        # initialize submitted_dict according to keys in jobs_dict
        submitted_dict = init_dict(jobs_dict)

    #####
    if category in ['obs', 'fakes']:
        years = []
        if 'mc16a' in eras:
            years += ['2015', '2016']
        if 'mc16d' in eras:
            years += ['2017']
        if 'mc16e' in eras:
            years += ['2018']
        eras = years

    # Submit
    if category in ['obs', 'fakes']:
        for e in eras:
            if submitted_dict[category][e] and not resubmit:
                print(f"WARNING: [{category}][{e}] has already been submitted")
                continue
            submit(jobs_dict[category][e], args_string, dry_run)
            submitted_dict[category][e] = True
    elif category == 'detNP':
        for s in samples:
            if not s in jobs_dict[category]:
                print(f"WARNING: {s} not in [{category}]")
                continue

            # all available systematics
            systematics_cfg = list(jobs_dict[category][s].keys())

            for syst in systematics_cfg:
                # filter syst based on the systematics argument
                if not any(keyword in syst for keyword in systematics):
                    continue

                for e in eras:
                    if submitted_dict[category][s][syst][e] and not resubmit:
                        print(f"WARNING: [{category}][{s}][{syst}][{e}] has already been submitted")
                        continue
                    submit(jobs_dict[category][s][syst][e], args_string, dry_run)
                    submitted_dict[category][s][syst][e] = True
    else:
        for s in samples:
            if not s in jobs_dict[category]:
                print(f"WARNING: {s} not in [{category}]")
                continue
            for e in eras:
                if submitted_dict[category][s][e] and not resubmit:
                    print(f"WARNING: {[category]}{[s]}{[e]} has already been submitted")
                    continue
                submit(jobs_dict[category][s][e], args_string, dry_run)
                submitted_dict[category][s][e] = True

    # Save job submission status to file, replace the old one if it exists
    print(f"Update job submission status in {jobs_submitted}")
    with open(jobs_submitted, 'w') as outfile:
        yaml.dump(submitted_dict, outfile)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("job_config", type=str,
                        help="Config file of jobs that are read to be submitted")
    parser.add_argument("-c", "--categories", nargs="+", required=True,
                        choices=["detNP", "mcWAlt", "systCRL", "obs", "fakes"],
                        help="Type of datasets to submit")
    parser.add_argument("-s", "--samples", nargs="+",
                        default=["ttbar","singleTop","VV","ttV","ttH","Wjets","Zjets"],
                        help="List of samples")
    parser.add_argument("-u", "--systematics", nargs="+", default=["nominal"],
                        help="List of systematic uncertainties")
    parser.add_argument("-e", "--eras", nargs="+", default=["mc16a", "mc16d", "mc16e"],
                        help="List of subcampaigns/years of datasets")
    parser.add_argument("-a", "--arguments", type=str,
                        default="-l walltime=8:00:00",
                        help="Arguments to be passed to qsub")
    parser.add_argument("-r", "--resubmit", action="store_true",
                        help="If True, submit the job even if it has been submitted before")
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="If True, print the command instead of running it")

    args = parser.parse_args()

    for c in args.categories:
        submitJobs(
            jobs_config = args.job_config,
            category = c,
            samples = args.samples,
            systematics = args.systematics,
            eras = args.eras,
            args_string = args.arguments,
            resubmit = args.resubmit,
            dry_run = args.dry_run
        )
