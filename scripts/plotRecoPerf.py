from ROOT import TChain, TFile, gDirectory

def drawFromTree(
    tree,
    label = "ttbar",
    reco_prefix = "PseudoTop_Reco_ttbar",
    truth_prefix = "MC_ttbar_afterFSR",
    selections = "",
    good_events_cut = "!isnan(MC_thad_afterFSR_y)&&isDummy==0"
    ):

    print(label)

    if not selections:
        selections = good_events_cut
    else:
        selections += "&&"+good_events_cut

    # pt resolution
    pt_reco = f"{reco_prefix}_pt"
    pt_truth = f"({truth_prefix}_pt/1000)" # convert MeV to GeV
    hname_pt = f"h_{label}_res_pt"
    bins_pt = "(100, -1, 5)"

    tree.Draw(f"({pt_reco}/{pt_truth})-1>>{hname_pt}{bins_pt}", selections)
    h_res_pt = gDirectory.Get(hname_pt)
    h_res_pt.Write()

    # y residual
    y_reco = f"{reco_prefix}_y"
    y_truth = f"{truth_prefix}_y"
    hname_y = f"h_{label}_res_y"
    bins_y = "(100, -2, 2)"

    tree.Draw(f"{y_reco}-{y_truth}>>{hname_y}{bins_y}", selections)
    h_res_y = gDirectory.Get(hname_y)
    h_res_y.Write()

    # phi residual
    phi_reco = f"{reco_prefix}_phi"
    phi_truth = f"{truth_prefix}_phi"
    hname_phi = f"h_{label}_res_phi"
    bins_phi = "(100, -3.2, 3.2)"

    tree.Draw(f"TVector2::Phi_mpi_pi({phi_reco}-{phi_truth})>>{hname_phi}{bins_phi}", selections)
    h_res_phi = gDirectory.Get(hname_phi)
    h_res_phi.Write()

def plotRecoPerf(inputfiles, output, treename_reco, treename_truth=None):
    print("Read trees from", inputfiles)

    tree_reco = TChain(treename_reco)
    for infile in inputfiles:
        print(f"Add file {infile}")
        tree_reco.Add(infile)

    if treename_truth:
        tree_truth = TChain(treename_truth)
        for infile in inputfiles:
            tree_truth.Add(infile)

        # make them friends!
        tree_reco.AddFriend(tree_truth)

    # output file
    outfile = TFile.Open(output, 'recreate')
    outfile.cd()

    # PseudoTop
    print("PseudoTop")
    outfile.mkdir("PseudoTop")
    outfile.cd("PseudoTop")

    drawFromTree(
        tree_reco, "ttbar",
        reco_prefix = "PseudoTop_Reco_ttbar",
        truth_prefix = "MC_ttbar_afterFSR")

    drawFromTree(
        tree_reco, "thad",
        reco_prefix = "PseudoTop_Reco_top_had",
        truth_prefix = "MC_thad_afterFSR")

    drawFromTree(
        tree_reco, "tlep",
        reco_prefix = "PseudoTop_Reco_top_lep",
        truth_prefix = "MC_tlep_afterFSR")

    print("PseudoTop high pT")
    outfile.mkdir("PseudoTop_highPt")
    outfile.cd("PseudoTop_highPt")
    drawFromTree(
        tree_reco, "ttbar",
        reco_prefix = "PseudoTop_Reco_ttbar",
        truth_prefix = "MC_ttbar_afterFSR",
        selections="MC_ttbar_afterFSR_pt/1000>250")

    drawFromTree(
        tree_reco, "thad",
        reco_prefix = "PseudoTop_Reco_top_had",
        truth_prefix = "MC_thad_afterFSR",
        selections="MC_ttbar_afterFSR_pt/1000>250")

    drawFromTree(
        tree_reco, "tlep",
        reco_prefix = "PseudoTop_Reco_top_lep",
        truth_prefix = "MC_tlep_afterFSR",
        selections="MC_ttbar_afterFSR_pt/1000>250")

    outfile.Close()

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('inputfiles', nargs='+', type=str,
                        help="Input root files")
    parser.add_argument('-o', '--output', default='histograms_perf.root',
                        help="Output name")
    parser.add_argument('-r', '--treename-reco', default='reco', type=str,
                        help="Reco tree name")
    parser.add_argument('-t', '--treename-truth', default='parton', type=str,
                        help="Truth tree name")

    args = parser.parse_args()

    plotRecoPerf(
        args.inputfiles, args.output,
        args.treename_reco, args.treename_truth
        )
