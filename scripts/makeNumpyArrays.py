#!/user/bin/env python3
import os
import time
import tracemalloc
import numpy as np
import numpy.lib.recfunctions as rfn
import uproot

def MeVtoGeV(array):
    """
    array: numpy record array
    """
    for fname in list(array.dtype.names):
        # jet_pt, jet_e, met_met, mwt, lep_pt, lep_m
        isObjectVar = fname in ['jet_pt', 'jet_e', 'met_met', 'mwt', 'lep_pt', 'lep_m']
        # MC_*_afterFSR_[pt,m,E, Ht, pout]
        isPartonVar = fname.startswith('MC_') and ( fname.endswith('_pt') or fname.endswith('_m') or fname.endswith('_E') or fname.endswith('_Ht') or fname.endswith('_pout'))

        if isObjectVar or isPartonVar:
            array[fname] /= 1000.

    return array

def setDummyValue(array, dummy_value):
    isdummy = array['isDummy']==1
    for vname in list(array.dtype.names):
        if vname in ['isDummy', 'isMatched']:
            continue

        array[vname][isdummy] = dummy_value

    return array

def makeNumpyArrays(**parsed_args):
    # read input files
    treename_reco = 'reco'
    treename_truth = parsed_args['truth_level']

    intrees_reco = [fname+':'+treename_reco for fname in parsed_args['input_files']]
    intrees_truth = [fname+':'+treename_truth for fname in parsed_args['input_files']]

    # need uproot4
    assert(uproot.__version__ > "4.0.0")
    
    # check events are truth matched
    if parsed_args['check_match']:
        print("Checking if reco and truth arrays are matched ...")
        reco_ids = uproot.lazy(intrees_reco, filter_name=['runNumber', 'eventNumber', 'isMatched'])
        truth_ids = uproot.lazy(intrees_truth, filter_name=['runNumber', 'eventNumber', 'isMatched'])

        nparr_reco_ids = np.asarray(reco_ids)
        runNum_reco = nparr_reco_ids['runNumber'][nparr_reco_ids['isMatched']==1]
        evtNum_reco = nparr_reco_ids['eventNumber'][nparr_reco_ids['isMatched']==1]

        nparr_truth_ids = np.asarray(truth_ids)
        runNum_truth = nparr_truth_ids['runNumber'][nparr_truth_ids['isMatched']==1]
        evtNum_truth = nparr_truth_ids['eventNumber'][nparr_truth_ids['isMatched']==1]

        assert(np.all(runNum_reco == runNum_truth) and np.all(evtNum_reco == evtNum_truth))
        print("... done!")

    # read branches
    branches_reco = [parsed_args['weight_name'], "isMatched", "isDummy"]
    branches_truth = ['isMatched', "isDummy"]
    if parsed_args['truth_level'] == 'parton':
        branches_reco += ['klfitter_logLikelihood', 'klfitter_bestPerm_*']
        branches_truth += ['MC_ttbar_afterFSR_*', 'MC_thad_afterFSR_*', 'MC_tlep_afterFSR_*']
    else: # particle
        branches_reco += ["PseudoTop_*", "lep_pt", "jet_n"] #FIXME
        branches_truth += ["PseudoTop_*", "lep_pt", "jet_n"] #FIXME

    print("Reading arrays")
    akarr_reco = uproot.lazy(intrees_reco, filter_name=branches_reco)
    akarr_truth = uproot.lazy(intrees_truth, filter_name=branches_truth)

    # convert numpy array
    print("Converting to numpy arrays")
    arrays_reco = np.asarray(akarr_reco)
    arrays_truth = np.asarray(akarr_truth)

    # convert units
    print("Converting columns in the unit of MeV to GeV")
    arrays_reco = MeVtoGeV(arrays_reco)
    arrays_truth = MeVtoGeV(arrays_truth)

    if parsed_args['matched_only']:
        # only store reoc and truth events that are matched to each other
        print("Only take truth matched event")
        arrays_reco = arrays_reco[arrays_reco['isMatched']==1]
        arrays_truth = arrays_truth[arrays_truth['isMatched']==1]
    else:
        # pad unmatched dummy events with dummy value
        print("Pad dummy events with value {}".format(parsed_args['pad_value']))
        arrays_reco = setDummyValue(arrays_reco, parsed_args['pad_value'])
        arrays_truth = setDummyValue(arrays_truth, parsed_args['pad_value'])

    # apply selections here if needed
    if parsed_args['truth_level'] == 'parton':
        print("Apply event selections")
        if parsed_args['klfitter_loglikelihood'] is not None:
            sel = arrays_reco['klfitter_logLikelihood'] > parsed_args['klfitter_loglikelihood']
            arrays_reco = arrays_reco[sel]
            arrays_truth = arrays_truth[sel]
        else:
            # particle level
            pass

    assert(len(arrays_reco) == len(arrays_truth))

    # rename truth array fields if needed
    print("Adding proper prefix to all truth array fields")
    truth_prefix = 'MC_' if parsed_args['truth_level'] == 'parton' else 'PL_'
    newnames = {}
    for fname in arrays_truth.dtype.names:
        if not fname.startswith(truth_prefix):
            newnames[fname] = truth_prefix+fname
    arrays_truth = rfn.rename_fields(arrays_truth, newnames)

    # join reco and truth array
    print('Merging all arrays')
    arrays_all = rfn.merge_arrays([arrays_reco, arrays_truth], flatten=True)

    # write to disk
    outdir = os.path.dirname(parsed_args['output_name'])
    if not os.path.isdir(outdir):
        print("Create output directory: {}".format(outdir))
        os.makedirs(outdir)

    print("Writing arrays to file {} ...".format(parsed_args['output_name']))
    np.savez(parsed_args['output_name'], arrays_all)
    print('... done!')

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('input_files', nargs='+', type=str,
                        help="list of input root files")
    parser.add_argument('-t', '--truth-level', choices=['parton','particle'],
                        required=True, help="Parton or paticle level")
    parser.add_argument('-w', '--weight-name', default='normedWeight',
                        help="Name of the weight column")
    parser.add_argument('-o', '--output-name', default='ntuple.npz',
                        help="Output file name")
    parser.add_argument('-c', '--check-match', action='store_true',
                        help="Check if the events are truth matched")
    parser.add_argument('-m', '--matched-only', action='store_true',
                        help="if true, only save truth matched events")
    parser.add_argument('-p', '--pad-value', type=float, default=-999.,
                        help="value for padding dummy events")
    parser.add_argument('-l', '--klfitter-loglikelihood',
                        default=None, type=float,
                        help="Cut on KLFitter log likelihood")

    args = parser.parse_args()

    tracemalloc.start()

    tstart = time.time()
    makeNumpyArrays(**vars(args))
    tdone = time.time()
    print("makeNumpyArrays took {:.2f} seconds".format(tdone - tstart))

    mcurrent, mpeak = tracemalloc.get_traced_memory()
    print("Current memory usage is {:.1f} MB; Peak was {:.1f} MB".format(mcurrent * 10**-6, mpeak * 10**-6))
