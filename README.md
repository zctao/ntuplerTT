# ntuplerTT

## Prerequisites

CVMFS

## Set up environment

- To run scripts/writeJobFile.py:

      source setup_atlas.sh
      lsetup rucio

- To run scripts/processMiniNtuples.py:

      source setup_atlas.sh
    
  Do NOT set up rucio because it messes up python path. Rucio client is only needed by scripts/writeJobFile.py
    
- To run scripts/makeNumpyArrays.py:

      source setup_lcg.sh
    
  For this one, setupATLAS is not necessary. It needs a more recent version of LCG release because of uproot 4.
