from ROOT import TChain, TFile, TCanvas, gDirectory, gStyle

import argparse

parser = argparse.ArgumentParser()

parser.add_argument('inputfiles', nargs='+', type=str,
                    help="Input root files")
parser.add_argument('-o', '--output', default='response',
                    help="Output name")
parser.add_argument('-r', '--reco-tree', default='reco', type=str,
                    help="Reco tree name")
parser.add_argument('-t', '--truth-tree', default='parton',
                    choices=['particle','parton'], help="Truth tree name")

args = parser.parse_args()

print("Read trees from", args.inputfiles)

tree_reco = TChain(args.reco_tree)
for infile in args.inputfiles:
    tree_reco.Add(infile)

tree_truth = TChain(args.truth_tree)
for infile in args.inputfiles:
    tree_truth.Add(infile)

# make them friends!
tree_reco.AddFriend(tree_truth)

branches_reco = {}
branches_truth = {}
cuts = "isMatched"

if args.truth_tree == 'parton':
    branches_reco = {
        ('thad','pt') : 'klfitter_bestPerm_topHad_pt',
        ('thad','eta') : 'klfitter_bestPerm_topHad_eta',
        ('thad','y') : 'klfitter_bestPerm_topHad_y',
        ('thad','phi') : 'klfitter_bestPerm_topHad_phi',
        ('thad','m') : 'klfitter_bestPerm_topHad_m',
        ('tlep','pt') : 'klfitter_bestPerm_topLep_pt',
        ('tlep','eta') : 'klfitter_bestPerm_topLep_eta',
        ('tlep','y') : 'klfitter_bestPerm_topLep_y',
        ('tlep','phi') : 'klfitter_bestPerm_topLep_phi',
        ('tlep','m') : 'klfitter_bestPerm_topLep_m',
        ('ttbar','pt') : 'klfitter_bestPerm_ttbar_pt',
        ('ttbar','eta') : 'klfitter_bestPerm_ttbar_eta',
        ('ttbar','y') : 'klfitter_bestPerm_ttbar_y',
        ('ttbar','phi') : 'klfitter_bestPerm_ttbar_phi',
        ('ttbar','m') : 'klfitter_bestPerm_ttbar_m'
    }

    branches_truth = {
        ('thad','pt') : 'MC_thad_afterFSR_pt/1000',
        ('thad','eta') : 'MC_thad_afterFSR_eta',
        ('thad','y') : 'MC_thad_afterFSR_y',
        ('thad','phi') : 'MC_thad_afterFSR_phi',
        ('thad','m') : 'MC_thad_afterFSR_m/1000',
        ('tlep','pt') : 'MC_tlep_afterFSR_pt/1000',
        ('tlep','eta') : 'MC_tlep_afterFSR_eta',
        ('tlep','y') : 'MC_tlep_afterFSR_y',
        ('tlep','phi') : 'MC_tlep_afterFSR_phi',
        ('tlep','m') : 'MC_tlep_afterFSR_m/1000',
        ('ttbar','pt') : 'MC_ttbar_afterFSR_pt/1000',
        ('ttbar','eta') : 'MC_ttbar_afterFSR_eta',
        ('ttbar','y') : 'MC_ttbar_afterFSR_y',
        ('ttbar','phi') : 'MC_ttbar_afterFSR_phi',
        ('ttbar','m') : 'MC_ttbar_afterFSR_m/1000'
    }

    cuts += "&&klfitter_logLikelihood>-52"
    # ?? there are also parton events with nan or inf kinematic values
    cuts += "&&!isnan(MC_thad_afterFSR_y)"

elif args.truth_tree == 'particle':
    branches_reco = {
        ('thad','pt') : 'PseudoTop_Reco_top_had_pt',
        ('thad','eta') : 'PseudoTop_Reco_top_had_eta',
        ('thad','y') : 'PseudoTop_Reco_top_had_y',
        ('thad','phi') : 'PseudoTop_Reco_top_had_phi',
        ('thad','m') : 'PseudoTop_Reco_top_had_m',
        ('tlep','pt') : 'PseudoTop_Reco_top_lep_pt',
        ('tlep','eta') : 'PseudoTop_Reco_top_lep_eta',
        ('tlep','y') : 'PseudoTop_Reco_top_lep_y',
        ('tlep','phi') : 'PseudoTop_Reco_top_lep_phi',
        ('tlep','m') : 'PseudoTop_Reco_top_lep_m',
        ('ttbar','pt') : 'PseudoTop_Reco_ttbar_pt',
        ('ttbar','eta') : 'PseudoTop_Reco_ttbar_eta',
        ('ttbar','y') : 'PseudoTop_Reco_ttbar_y',
        ('ttbar','phi') : 'PseudoTop_Reco_ttbar_phi',
        ('ttbar','m') : 'PseudoTop_Reco_ttbar_m'
    }

    branches_truth = {
        ('thad','pt') : 'PseudoTop_Particle_top_had_pt',
        ('thad','eta') : 'PseudoTop_Particle_top_had_eta',
        ('thad','y') : 'PseudoTop_Particle_top_had_y',
        ('thad','phi') : 'PseudoTop_Particle_top_had_phi',
        ('thad','m') : 'PseudoTop_Particle_top_had_m',
        ('tlep','pt') : 'PseudoTop_Particle_top_lep_pt',
        ('tlep','eta') : 'PseudoTop_Particle_top_lep_eta',
        ('tlep','y') : 'PseudoTop_Particle_top_lep_y',
        ('tlep','phi') : 'PseudoTop_Particle_top_lep_phi',
        ('tlep','m') : 'PseudoTop_Particle_top_lep_m',
        ('ttbar','pt') : 'PseudoTop_Particle_ttbar_pt',
        ('ttbar','eta') : 'PseudoTop_Particle_ttbar_eta',
        ('ttbar','y') : 'PseudoTop_Particle_ttbar_y',
        ('ttbar','phi') : 'PseudoTop_Particle_ttbar_phi',
        ('ttbar','m') : 'PseudoTop_Particle_ttbar_m'
    }

foutroot = TFile.Open(args.output+'.root', 'recreate')

histnames = []

for t in ['tlep', 'thad', 'ttbar']:
    for v in ['pt', 'eta', 'y', 'phi', 'm']:
        breco = branches_reco[(t, v)]
        btruth = branches_truth[(t,v)]

        hname = "h_"+t+"_"+v
        histnames.append(hname)

        tree_reco.Draw(btruth+":"+breco+">>"+hname, cuts, "goff")
        hresp = gDirectory.Get(hname)
        hresp.SetTitle(t+"_"+v)
        hresp.GetXaxis().SetTitle(breco)
        hresp.GetYaxis().SetTitle(btruth)
        hresp.Write()

foutroot.Close()

# Get all histograms and plot them
foutroot = TFile.Open(args.output+'.root', 'read')

gStyle.SetPaintTextFormat("2.2f")
gStyle.SetOptStat(11)

plotname = args.output+'.pdf'
canvas = TCanvas("c")
canvas.Print(plotname+'[')

for hname in histnames:
    hresp = foutroot.Get(hname)

    # rebin
    hresp = hresp.Rebin2D(2, 2)

    # normalize per truth bins
    nbinsY = hresp.GetNbinsY()
    nbinsX = hresp.GetNbinsX()
    for ibiny in range(1, nbinsY+1): # bin #0 is the underflow bin
        norm_y = hresp.Integral(1, nbinsX, ibiny, ibiny)

        for ibinx in range(1, nbinsX+1):
            rescaled_entry = hresp.GetBinContent(ibinx, ibiny) / norm_y if norm_y>0 else 0
            rescaled_error = hresp.GetBinError(ibinx, ibiny) / norm_y if norm_y>0 else 0

            hresp.SetBinContent(ibinx, ibiny, rescaled_entry)
            hresp.SetBinError(ibinx, ibiny, rescaled_error)

    # draw the historam
    #hresp.SetStats(False)
    hresp.Draw("col text")
    canvas.Print(plotname)

canvas.Print(plotname+']')
