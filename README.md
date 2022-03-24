# ntuplerTT

## Prerequisites

CVMFS

## Set up environment

- On ATLAS tier 3:

      source setup_atlas.sh

- On CC Cedar:

      setupATLAS -c centos7 -b
      cd <ntuplerTT directory>
      source setup_lcg.sh LCG_97apython3

- For scripts that require Rucio, need to set up rucio as well:

      lsetup rucio

## Usage

### Sample management

- To grab sample lists (.yaml) from gitlab repo pyTTbarDiffXs13TeV:

      python scripts/getSampleListsFromGitlab.py <gitlab token> -s <sample_tag> -f <filters> -o <output_name>

  An example to run this script and produce sample lists of version MINI362_v1:

      source test/produceSampleLists_ttdiffxs361.sh

  It produces a collection of dataset config yaml files in configs/datasets/ttdiffxs361/

- To get the file sizes of samples (require rucio):

      python scripts/getSampleSize.py <dataset_config.yaml> -s <list of sample names> -e <list of subcampaigns or years>

  An example to compute and print the sizes of all samples in dataset config files:

      source test/getAllSampleSize.sh

- To download samples to local disks from the sample lists generated earlier (require rucio):

      source scripts/downloadSamples.sh <dataset_config.yaml> <sample_name> <local_directory> [<subcampaign> ...]

  An example to download all MINI362_v1 samples:

      source test/downloadMINI362_v1.sh

  This script uses the dataset configs generated earlier and downloads data files to ${HOME}/data/ttbarDiffXs13TeV/MINI362_v1/

### Ntuple processing

- Before processing ntuples, a map for sum of Monte Carlo weights for each sample needs to be computed:

      python scripts/computeSumWeights.py <dataset_config.yaml> [-l <local_directory>] [-o <output_dir>]

  An example to calculate and produce all sample sum weights map:

      source test/calc_sumweights_mini362_v1.sh

  The sum weights are saved as yaml files in the same directory as the dataset config files.

- To process ntuples:

      python scripts/processMiniNtuples.py -n <sample_name> -r <reco_root_files> -t <truth_root_files> -w <sum_weight_confg.yaml> -o <output_directory>

  For more options:

      python scripts/processMiniNtuples.py -h

- To prepare and produce batch job files to be submitted to a cluster:

      python scripts/writeJobFile.py <sample_name> -d <dataset_config.yaml> -o <output_directory> -c <subcampaign or year> -t <truth_level> -l <local_directory_to_read_input_files> -w <sum_weight_config.yaml>

  For more options:

      python scripts/writeJobFile.py -h

  A script to generate all job files using mini-ntuple MINI362_v1 including all systematics:
  
      python test/generate_jobfiles_mini362_v1.py

  It writes job files, which can be submitted using qsub later, to ${HOME}/data/batch_output/NtupleTT/latest/ by default.
