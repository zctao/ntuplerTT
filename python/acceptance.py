from ROOT import TH1, TH1F

class HistogramsTTbar():
    def __init__(self, label, thad_prefix, tlep_prefix, ttbar_prefix):
        # prefix of branch names for hadronic top, leptonic top, and ttbar
        self.thad_prefix = thad_prefix.rstrip('_')
        self.tlep_prefix = tlep_prefix.rstrip('_')
        self.ttbar_prefix = ttbar_prefix.rstrip('_')

        # Some parton MC truth variables have unit MeV instead of GeV
        sf_unit = 1000. if self.ttbar_prefix.startswith('MC_') else 1.

        # histograms
        TH1.SetDefaultSumw2()
        self.hist_th_pt = TH1F(label+"_th_pt", "p_{T}^{t,had}", 100, 0, 1000*sf_unit)
        self.hist_th_y = TH1F(label+"_th_y", "y^{t,had}", 100, -2.5, 2.5)
        self.hist_mtt = TH1F(label+"_mtt", "m^{ttbar}", 100, 300*sf_unit, 2000*sf_unit)
        self.hist_ptt = TH1F(label+"_ptt", "p_{T}^{ttbar}", 100, 0, 800*sf_unit)
        self.hist_ytt = TH1F(label+"_ytt", "y^{ttbar}", 100, -2.5, 2.5)
        self.hist_dphi = TH1F(label+"_dphi", "|\Delta\phi(t, tbar)|", 100, 0, 3.15)

    def fill(self, tree, extra_variables, ievent=None, weight_name=None):
        if ievent is not None:
            tree.GetEntry(ievent)

        w = 1 if weight_name is None else getattr(tree, weight_name)

        self.hist_th_pt.Fill( getattr(tree, self.thad_prefix+'_pt'), w )
        self.hist_th_y.Fill( getattr(tree, self.thad_prefix+'_y'), w )
        self.hist_mtt.Fill( getattr(tree, self.ttbar_prefix+'_m'), w )
        self.hist_ptt.Fill( getattr(tree, self.ttbar_prefix+'_pt'), w )
        self.hist_ytt.Fill( getattr(tree, self.ttbar_prefix+'_y'), w )

        self.hist_dphi.Fill( extra_variables.ttbar_dphi[0], w )

class CorrectionFactors():
    def __init__(self, label, thad_prefix, tlep_prefix, ttbar_prefix, wname):

        self.hists_numer = HistogramsTTbar(
            label+'_numer', thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.hists_denom = HistogramsTTbar(
            label+'_denom', thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.hists_ratio = HistogramsTTbar(
            label, thad_prefix, tlep_prefix, ttbar_prefix
            )

        self.weight_name = wname

    def fill_denominator(self, tree, extra_vars, ievent=None):
        self.hists_denom.fill(tree, extra_vars, ievent, self.weight_name)

    def fill_numerator(self, tree, extra_vars, ievent=None):
        self.hists_numer.fill(tree, extra_vars, ievent, self.weight_name)

    def compute_factors(self, xtitle=None, ytitle=None):
        for vname, histogram in vars(self.hists_ratio).items():
            if not isinstance(histogram, TH1):
                continue

            histogram.Divide(
                getattr(self.hists_numer, vname),
                getattr(self.hists_denom, vname)
            )

            if xtitle:
                histogram.GetXaxis().SetTitle(xtitle)
            if ytitle:
                histogram.GetYaxis().SetTitle(ytitle)
