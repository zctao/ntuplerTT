#!/usr/bin/env python3
import os
import sys
import subprocess

if len(sys.argv) != 2:
    print("Usage: ./checkJobStatus.py <directory>")
    exit()

top_directory = sys.argv[1]
good_status = 0
server_name = "atlas-t3-ubc.computecanada.ca"

success_jobs = {}
failed_jobs = {}

# search PBS job output logs
for r, dirs, files in os.walk(top_directory):
    # look for job logs
    for f in files:
        if server_name+'.out' in f:
            # get job ID
            jobid = f.split('.')[0]

            # get job status
            report = subprocess.check_output(['tracejob', '-q', jobid])
            status = None
            for x in str(report).split(' '):
                if x.startswith('Exit_status'):
                    status = int(x.split('=')[-1])
                    break

            if status == good_status:
                if r in success_jobs:
                    success_jobs[r].append(jobid)
                else:
                    success_jobs[r] = [jobid]
            else:
                if r in failed_jobs:
                    failed_jobs[r].append(jobid)
                else:
                    failed_jobs[r] = [jobid]

print("Jobs with nonzero exit status:")
#print(failed_jobs)
for d in failed_jobs:
    print(d, ': ', failed_jobs[d])
