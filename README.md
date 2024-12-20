# ntuplerTT

## Prerequisites

CVMFS

## Set up environment

- On ATLAS tier 3:

      source setup_atlas.sh

- For scripts that require Rucio, need to set up rucio as well:

      lsetup rucio

## Usage

### Sample management

Sample DSIDs are listed in YAML files under `configs/datasets/<verson>/`.

- To get the file sizes of samples (require rucio):

      python scripts/getSampleSize.py <dataset_config.yaml> -s <list of sample names> -e <list of subcampaigns or years>

  An example to compute and print the sizes of all samples in dataset config files:

      source test/getAllSampleSize.sh

- To download samples to local disks from the sample lists generated earlier (require rucio):

      source scripts/downloadSamples.sh <dataset_config.yaml> <sample_name> <local_directory> [<subcampaign> ...]

  An example to download all MINI382_v1 samples:

      source test/downloadMINI382_v1.sh

### Ntuple processing

- Before processing ntuples, a map for sum of Monte Carlo weights for each sample needs to be computed:

      python scripts/computeSumWeights.py <dataset_config.yaml> [-l <local_directory>] [-o <output_dir>]

  An example slurm job script to compute all sample sum of weights is provided. To submit a slurm job:

      sbatch test/calcSumWeights.slurm

  The sum weights are saved as yaml files in the same directory as the dataset config files.

- To process ntuples:

      python scripts/processMiniNtuples.py -n <sample_name> -r <reco_root_files> -t <truth_root_files> -w <sum_weight_confg.yaml> -o <output_directory>

  For more options:

      python scripts/processMiniNtuples.py -h

  A script for a quick test run:

      source test/quick_test.sh 

- To prepare and produce batch job files to be submitted to a cluster:

      python scripts/writeJobFile.py <sample_name> -d <dataset_config.yaml> -o <output_directory> -c <subcampaign or year> -t <truth_level> -l <local_directory_to_read_input_files> -w <sum_weight_config.yaml>

  For more options:

      python scripts/writeJobFile.py -h

  A script is provided to generate all job files using mini-ntuple MINI382_v1 including all systematics:
  
      python test/generate_jobfiles_mini382_v1.py

  Slurm job files are written to `${HOME}/data/ntupleTT/latest/` by default.
  The generated jobs are summarized in a YAML file: `${HOME}/data/ntupleTT/latest/jobs_mini382_v1/jobfiles.yaml`.

- To submit the jobs:

      python scripts/submitJobs.py <job_summary.yaml> -c <sample_category> -s <list_of_sample_names> -u <list_of_systematics>

  It generates a job submission status file with suffix "_submitted" based on the `<job_summary.yaml>` (configs/jobs_mini362_v1/jobfiles.yaml).

  Any systematic uncertainty in `<job_summary.yaml>` is included if its name contains one of the elements in `<list_of_systematics>`.

  A example script to submit all jobs generated in the previous step:

      source test/submit_mini362_v1.sh
      
- To check job outputs:

      python scripts/checkOutputs.py -j <job_summary.yaml>
      
  It generates a yaml file (in the same directory as `<job_summary.yaml>` by default) that reports the fraction of complete outputs.

