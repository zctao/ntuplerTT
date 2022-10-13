import os
import time
import tracemalloc

from ROOT import TChain, TH2F, TFile
from array import array

obsConfig_dict = {
    "th_pt" : {
        "reco" : "PseudoTop_Reco_top_had_pt",
        "truth" : "MC_thad_afterFSR_pt",
        "bins" : [0,50,100,160,225,300,360,475,1000]
    },
    "mtt": {
        "reco" : "PseudoTop_Reco_ttbar_m",
        "truth" : "MC_ttbar_afterFSR_m",
        "bins" : [325.00,400.00,480.00,580.00,700.00,860.00,1020.00,1250.00,1500.00,2000.00]
    },
}

def reportMemUsage():
    mcurrent, mpeak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {mcurrent*10**-6:.1f} MB; Peak usage: {mpeak*10**-6:.1f} MB")

def prepareHistograms(observables):
    hists_d = dict()

    for ob in observables:
        obCfg = obsConfig_dict.get(ob)
        if obCfg is None:
            print(f"WARNING: observable {ob} is not in obsConfig_dict. Skip...")
            continue

        binsx = obCfg['bins']
        nbinsx = len(binsx) - 1
        labelx = obCfg['reco']

        binsy = obCfg['bins'] # same reco and truth bins for now
        nbinsy = len(binsy) - 1
        labely = obCfg['truth']

        hname = f"h2d_{labely}_vs_{labelx}"

        hists_d[ob] = TH2F(hname, "", nbinsx, array('f',binsx), nbinsy, array('f', binsy))
        hists_d[ob].GetXaxis().SetTitle(labelx)
        hists_d[ob].GetYaxis().SetTitle(labely)

    return hists_d

def buildHashMapFromTTree(tree, keys=('runNumber', 'eventNumber'), fname_eventID=None):
    print("Build TTree index")

    hmap = dict()
    duplicates = set()

    nentries = tree.GetEntries()

    progress_mark = 0.1

    for i, ev in enumerate(tree):

        # print progress
        if i >= (nentries-1) * progress_mark:
            print(f"processing {i}/{nentries}")
            progress_mark += 0.1

        # key for hmap
        k = ()
        for kname in keys:
            k += (getattr(ev, kname),)

        # check if the key already exists
        if hmap.get(k) is None:
            hmap[k] = i
        else:
            # this is a duplicate
            duplicates.add(k)

    # Remove duplicate events from the map
    for dk in duplicates:
        hmap.pop(dk)

    print(f"Found {len(duplicates)} duplicated event IDs")
    if len(duplicates) > 0:
        if fname_eventID:
            # write to file
            with open(fname_eventID, 'w') as fid:
                #fid.write(f"{keys}\n")
                for dk in duplicates:
                    fid.write(" ".join(str(x) for x in dk) + "\n")
        else:
            # print to log
            print(*keys)
            for dk in duplicates:
                print(" ".join(str(x) for x in dk))

    return hmap

def loadTrees(inputfiles, treename, buildIndex=True, verbose=True, fname_eventID=None):

    # Read TTree from files
    t_load_start = time.time()

    intree = TChain(treename)
    for infile in inputfiles:
        intree.Add(infile)

    t_load_done = time.time()

    if verbose:
        print(f"Load TTree: {t_load_done-t_load_start:.2f} seconds")
        reportMemUsage()

    # Build index
    t_index_start = time.time()

    index_d = buildHashMapFromTTree(intree, fname_eventID=fname_eventID) if buildIndex else None

    t_index_done = time.time()

    if verbose:
        print(f"Build index: {t_index_done-t_index_start:.2f} seconds")
        reportMemUsage()

    return intree, index_d

def debugResponse(
    inputs_reco,
    inputs_truth,
    outname,
    observables, # ["th_pt", "mtt"]
    treename='nominal',
    fname_duplicate=None
    ):

    # file to store duplicated event ID if necessary
    if fname_duplicate:
        ftmp = os.path.splitext(fname_duplicate)
        fname_dup_reco = ftmp[0]+"_reco"+ftmp[1]
        fname_dup_truth = ftmp[0]+"_truth"+ftmp[1]
    else:
        fname_dup_reco, fname_dup_truth = None, None

    # Reco TTree
    print("Load reco trees")
    tree_reco, index_reco = loadTrees(
        inputs_reco,
        treename,
        buildIndex = True,
        fname_eventID = fname_dup_reco
        )

    nevents_reco =  tree_reco.GetEntries()
    print(f"Number of events in the reco trees: {nevents_reco}")

    # Truth TTree
    print("Load truth trees")
    tree_truth, index_truth = loadTrees(
        inputs_truth,
        treename,
        buildIndex = True,
        fname_eventID = fname_dup_truth
        )

    nevents_truth = tree_truth.GetEntries()
    print(f"Number of events in the truth trees: {nevents_truth}")

    # Prepare histograms
    print("Prepare histograms")
    histograms_d = prepareHistograms(observables)

    ###
    # loop over the reco tree
    print("Loop over reco tree")

    t_tree_start = time.time()
    progress_mark = 0.1

    for ireco in range(nevents_reco):
        if ireco >= (nevents_reco-1)*progress_mark:
            print(f"processing {ireco}/{nevents_reco}")
            progress_mark += 0.1

        tree_reco.GetEntry(ireco)

        eventID = (tree_reco.runNumber, tree_reco.eventNumber)

        # first check in the reco tree if this is a duplicate event
        if index_reco.get(eventID) is None:
            # this is a duplicate event
            continue

        # try to get the matched event in the truth tree
        itruth = index_truth.get(eventID)
        if itruth is None or itruth < 0 or itruth >= nevents_truth:
            continue

        # get the truth event
        tree_truth.GetEntry(itruth)

        # fill the histogram
        weight = tree_reco.totalWeight_nominal

        for ob, h2d in histograms_d.items():
            vname_reco = obsConfig_dict[ob]['reco']
            xval = getattr(tree_reco, vname_reco)

            vname_truth = obsConfig_dict[ob]['truth']
            yval = getattr(tree_truth, vname_truth)/1000. # MeV to GeV

            h2d.Fill(xval, yval, weight)

    # end of reco tree loop
    t_tree_done = time.time()
    print(f"Done iterating reco tree: {t_tree_done-t_tree_start:.2f} seconds")
    reportMemUsage()

    ###
    # Write to output file
    print(f"Write histograms to flle {outname}")
    outfile = TFile.Open(outname, "recreate")
    for k, h in histograms_d.items():
        outfile.WriteTObject(h)
    outfile.Close()

if __name__ == "__main__":

    from datasets import getInputFileNames

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--reco-inputs', required=True, nargs='+', type=str)
    parser.add_argument('-t', '--truth-inputs', required=True, nargs='+', type=str)
    parser.add_argument('-o', '--outname', type=str, default="histograms2d.root")
    parser.add_argument('-e', '--eventlistname', type=str, default="duplicate_eventID.txt")

    args = parser.parse_args()

    freco_list = getInputFileNames(args.reco_inputs)
    ftruth_list = getInputFileNames(args.truth_inputs)

    tracemalloc.start()

    debugResponse(
        freco_list,
        ftruth_list,
        outname = args.outname,
        fname_duplicate = args.eventlistname,
        observables = ['th_pt', 'mtt'],
        treename = 'nominal'
    )

    tracemalloc.stop()
