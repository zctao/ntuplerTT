# ntuplerTT

## Prerequisites

CVMFS

## Set up environment

- To run scripts/writeJobFile.py:

      source setup_atlas.sh
      lsetup rucio
      
  or
  
      # In case of running on Cedar
      cd ~
      setupATLAS -c centos7 -b
      cd <ntuplerTT directory>
      source setup_lcg.sh LCG_97apython3
      lsetup rucio

- To run scripts/processMiniNtuples.py:

      source setup_atlas.sh
      
  or
  
      # In case of running on Cedar
      source setup_lcg.sh
    
  Do NOT set up rucio because it messes up python path. Rucio client is only needed by scripts/writeJobFile.py

- To run scripts/writeJobFile_toNumpy.py and/or scripts/makeNumpyArrays.py:

      source setup_lcg.sh
    
  For this one, setupATLAS is not necessary. It needs a more recent version of LCG release because of uproot 4.

## Examples

- Generate job files to process mini ntuples

      source test/generate_jobfiles.sh
      
- Generate job files to convert root ntuples to numpy arrays

      source test/generate_jobfiles_toNumpy.sh
