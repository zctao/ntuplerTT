import sys

from submitJobs import submit

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("job_list", type=str,
                    help="list of job sumbitting scripts")
parser.add_argument("-a", "--arguments", type=str, default="",
                    help="Arguments to be passed to qsub")
parser.add_argument("-b", "--batch-system", choices=['pbs','slurm'],
                    default='slurm', help="Batch system")
parser.add_argument("-d", "--dry-run", action="store_true",
                    help="If True, print the command instead of running it")

args = parser.parse_args()

print(f"Submit jobs from {args.job_list}")
with open(args.job_list, 'r') as flist:
    for fname_sub in flist:
        submit(
            fname_sub.strip(), 
            args=args.arguments,
            dry_run=args.dry_run,
            batch_system=args.batch_system
            )
        
