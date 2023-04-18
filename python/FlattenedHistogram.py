import os
import array
import math

from ROOT import TH1, TH1D, TH2D, gDirectory
TH1.SetDefaultSumw2()

import logging
logger = logging.getLogger("FlattenedHistogram")

class FlattenedHistogram2D():
    def __init__(
        self,
        hname="h",
        binning_d={}, # dict, binning configuration
        varname_x='x', # str
        varname_y='y', # str
        ):

        self.name = hname

        self._xhists = {}

        ybin_edges = []
        for ybin_label in binning_d:
            if not ybin_label.startswith('y_bin'):
                continue

            # y bins
            ylow, yhigh = binning_d[ybin_label]["edge"]
            if not ybin_edges:
                ybin_edges.append(ylow)
            else:
                assert(ylow==ybin_edges[-1])
            ybin_edges.append(yhigh)

            # make x histogram
            xbins = array.array('f', binning_d[ybin_label]['x_bins'])
            nbins_x = len(xbins) - 1
            self._xhists[ybin_label] = TH1D(f"{hname}/{ybin_label}", "", nbins_x, xbins)
            self._xhists[ybin_label].GetXaxis().SetTitle(varname_x)

        # make a y histogram
        self._yhist = None
        if ybin_edges:
            ybins = array.array('f', ybin_edges)
            nbins_y = len(ybins) - 1
            self._yhist = TH1D(f"{hname}/_yhist", "", nbins_y, ybins)
            self._yhist.GetXaxis().SetTitle(varname_y)

        if binning_d and (not self._xhists or not self._yhist):
            logger.error("Something is wrong with the binning config:")
            logger.error(f"{binning_d}")
            raise RuntimeError("Fail to initialize FlattenedHistogram2D")

        # make flattened histogram
        self._flatten(hname)

    def __len__(self):
        return len(self._xhists)

    def __iter__(self):
        return iter(self._xhists)

    def __getitem__(self, bin_label):
        return self._xhists[bin_label]

    def __setitem__(self, bin_label, newth1d):
        self._xhists[bin_label] = newth1d

    def _flatten(self, hname):
        self._flat = None

        if not self._yhist or not self._xhists:
            return

        # make new bin edges
        flat_bin_edges = []

        nbins_y = self._yhist.GetNbinsX()

        for ybin in range(1, nbins_y+1):
            ylow = self._yhist.GetBinLowEdge(ybin)
            yhigh = self._yhist.GetBinLowEdge(ybin+1)

            ybin_label = f'y_bin{ybin}'
            xbin_edges = list(self[ybin_label].GetXaxis().GetXbins())

            xbins_edges_new = [(xedge - xbin_edges[0]) / (xbin_edges[-1] - xbin_edges[0]) * (yhigh - ylow) + ylow for xedge in xbin_edges]

            if ybin < nbins_y:
                flat_bin_edges += xbins_edges_new[:-1]
            else:
                # last bin, include the upper edge too
                flat_bin_edges += xbins_edges_new

        # make a 1D histogram
        nbins_flat = len(flat_bin_edges) - 1
        self._flat = TH1D(f"{hname}/_flat", "", nbins_flat, array.array('f', flat_bin_edges))

        assert(self._flat.GetNbinsX() == self.GetNbins())

    def copy(self, newname="", skipFlat=False):
        fh2d_copy = FlattenedHistogram2D(newname)

        if self._yhist:
            newname_yhist = self._yhist.GetName().replace(self.name, newname) if newname else ""
            fh2d_copy._yhist = self._yhist.Clone(newname_yhist)

        for ybin_label in self:
            newname_xhist = self[ybin_label].GetName().replace(self.name, newname) if newname else ""
            fh2d_copy[ybin_label] = self[ybin_label].Clone(newname_xhist)

        if not skipFlat and self._flat:
            newname_flat = self._flat.GetName().replace(self.name, newname) if newname else ""
            fh2d_copy._flat = self._flat.Clone(newname_flat)

        return fh2d_copy

    def fromFlat(self, h_flat):
        # reset
        self.Reset()

        assert(len(self)>0)
        assert(h_flat.GetNbinsX() == self.GetNbins())

        self._flat = h_flat.Clone(self._flat.GetName()) # use the old name

        nbins_y = self._yhist.GetNbinsX()

        ibin = 0

        for ybin in range(1, nbins_y+1): # ignore y underflow and overflow bins
            ybin_label = f"y_bin{ybin}"

            ybin_content = 0.
            ybin_sumw2 = 0.

            nbins_x = self[ybin_label].GetNbinsX()
            for xbin in range(1, nbins_x+1):

                ibin += 1
                bin_content = h_flat.GetBinContent(ibin)
                bin_error = h_flat.GetBinError(ibin)

                self[ybin_label].SetBinContent(xbin, bin_content)
                self[ybin_label].SetBinError(xbin, bin_error)

                ybin_content += bin_content
                ybin_sumw2 += bin_error * bin_error

            self._yhist.SetBinContent(ybin, ybin_content)
            self._yhist.SetBinError(ybin, math.sqrt(ybin_sumw2))

    def Reset(self):
        if self._flat:
            self._flat.Reset()

        if self._yhist:
            self._yhist.Reset()

        for ybin_label in self:
            self[ybin_label].Reset()

    def FindBin(self, xval, yval):
        ybin = self._yhist.FindBin(yval)
        if ybin < 1 or ybin > self._yhist.GetNbinsX():
            # underflow or overflow
            return None

        xbin_offset = 0
        for yb in range(1,ybin):
            xbin_offset += self[f"y_bin{yb}"].GetNbinsX()

        xbin = self[f"y_bin{ybin}"].FindBin(xval)
        if xbin < 1 or xbin > self[f"y_bin{ybin}"].GetNbinsX():
            # underflow or overflow
            return None
        else:
            return xbin_offset + xbin

    def FindBins(self, xval, yval):
        ybin = self._yhist.FindBin(yval)
        if ybin < 1 or ybin > self._yhist.GetNbinsX():
            # underflow or overflow
            return None, None

        xbin = self[f"y_bin{ybin}"].FindBin(xval)
        if xbin < 1 or xbin > self[f"y_bin{ybin}"].GetNbinsX():
            # underflow or overflow
            xbin = None

        return xbin, ybin

    def GetNbins(self):
        nbins_total = 0

        for ybin_label in self:
            nbins_total += self[ybin_label].GetNbinsX()

        return nbins_total

    def Fill(self, x, y, w=1., skipFlat=False):
        # Fill the y histogram and get the bin index of y
        self._yhist.Fill(y, w)
        ybin = self._yhist.FindBin(y)
        ybin_label = f"y_bin{ybin}"

        # Fill the x histogram
        if ybin_label in self:
            self[ybin_label].Fill(x, w)

        if not skipFlat and self._flat:
            # Fill the flattened histogram
            ibin = self.FindBin(x, y)
            if ibin is not None:
                self._flat.AddBinContent(ibin, w)

    def GetFlat(self):
        return self._flat

    def Divide(self, fh2d_denom):
        self._yhist.Divide(fh2d_denom._yhist)

        if self._flat:
            self._flat.Divide(fh2d_denom._flat)

        for ybin_label in self:
            self[ybin_label].Divide(fh2d_denom[ybin_label])

    def Write(self, skipFlat=False, savedir=None):
        curdir = gDirectory.GetPath()

        if savedir is None:
            savedir = self.name

        gDirectory.mkdir(savedir)
        gDirectory.cd(savedir)

        if self._yhist:
            self._yhist.SetName(os.path.basename(self._yhist.GetName()))
            self._yhist.Write()

        for ybin_label in self:
            self[ybin_label].SetName(os.path.basename(self[ybin_label].GetName()))
            self[ybin_label].Write()

        if not skipFlat and self._flat:
            self._flat.SetName(os.path.basename(self._flat.GetName()))
            self._flat.Write()

        gDirectory.cd(curdir)

class FlattenedHistogram3D():
    def __init__(
        self,
        hname="h",
        binning_d={},
        varname_x='x',
        varname_y='y',
        varname_z='z'
        ):

        self.name = hname

        self._xyhists = {}

        zbin_edges = []

        for zbin_label in binning_d:
            if not zbin_label.startswith("z_bin"):
                continue

            # z bins
            zlow, zhigh = binning_d[zbin_label]["edge"]
            if not zbin_edges:
                zbin_edges.append(zlow)
            else:
                assert(zlow==zbin_edges[-1])
            zbin_edges.append(zhigh)

            binning_xy_d = binning_d[zbin_label]
            self._xyhists[zbin_label] = FlattenedHistogram2D(
                f"{hname}/{zbin_label}", binning_xy_d, varname_x, varname_y
            )

        # make a z histogram
        self._zhist = None
        if zbin_edges:
            zbins = array.array('f', zbin_edges)
            nbins_z = len(zbins) - 1
            self._zhist = TH1D(f"{hname}/_zhist", "", nbins_z, zbins)
            self._zhist.GetXaxis().SetTitle(varname_z)

        if binning_d and (not self._zhist or not self._xyhists):
            logger.error("Something is wrong with the binning config:")
            logger.error(f"{binning_d}")
            raise RuntimeError("Fail to initialize FlattenedHistogram3D")

        # make flattened histogram
        self._flatten(hname)

    def __len__(self):
        return len(self._xyhists)

    def __iter__(self):
        return iter(self._xyhists)

    def __getitem__(self, bin_label):
        return self._xyhists[bin_label]

    def __setitem__(self, bin_label, newfh2d):
        self._xyhists[bin_label] = newfh2d

    def _flatten(self, hname):
        self._flat = None

        if not self._zhist or not self._xyhists:
            return

        # make new bin edges
        flat_bin_edges = []

        nbins_z = self._zhist.GetNbinsX()

        for zbin in range(1, nbins_z+1):
            zlow = self._zhist.GetBinLowEdge(zbin)
            zhigh = self._zhist.GetBinLowEdge(zbin+1)

            zbin_label = f'z_bin{zbin}'
            xybin_edges = list(self[zbin_label]._flat.GetXaxis().GetXbins())

            xybin_edges_new = [(xy_edge - xybin_edges[0]) / (xybin_edges[-1] - xybin_edges[0]) * (zhigh - zlow) + zlow for xy_edge in xybin_edges]

            if zbin < nbins_z:
                flat_bin_edges += xybin_edges_new[:-1]
            else:
                # last bin, include the upper edge too
                flat_bin_edges += xybin_edges_new

        # make a 1D histogram
        nbins_flat = len(flat_bin_edges) - 1
        self._flat = TH1D(f"{hname}/_flat", "", nbins_flat, array.array('f', flat_bin_edges))

        assert(self._flat.GetNbinsX() == self.GetNbins())

    def copy(self, newname="", skipFlat=False):
        fh3d_copy = FlattenedHistogram3D(newname)

        if self._zhist:
            newname_zhist = self._zhist.GetName().replace(self.name, newname) if newname else ""
            fh3d_copy._zhist = self._zhist.Clone(newname_zhist)

        for zbin_label in self:
            newname_xyhist = self[zbin_label].name.replace(self.name, newname) if newname else ""
            fh3d_copy[zbin_label] = self[zbin_label].copy(newname_xyhist, skipFlat=True)

        if not skipFlat and self._flat:
            newname_flat = self._flat.GetName().replace(self.name, newname) if newname else ""
            fh3d_copy._flat = self._zhist.Clone(newname_flat)

        return fh3d_copy

    def fromFlat(self, h_flat):
        # reset
        self.Reset()

        assert(len(self)>0)
        assert(h_flat.GetNbinsX() == self.GetNbins())

        self._flat = h_flat.Clone(self._flat.GetName()) # use the old name

        nbins_z = self._zhist.GetNbinsX()

        ibin = 0

        for zbin in range(1, nbins_z+1): # ignore z underflow and overflow bins
            zbin_label = f"z_bin{zbin}"

            zbin_content = 0.
            zbin_sumw2 = 0.

            nbins_y = len(self[zbin_label])

            for ybin in range(1, nbins_y+1):
                ybin_label = f"y_bin{ybin}"

                ybin_content = 0.
                ybin_sumw2 = 0.

                nbins_x = self[zbin_label][ybin_label].GetNbinsX()
                for xbin in range(1, nbins_x+1):

                    ibin += 1
                    bin_content = h_flat.GetBinContent(ibin)
                    bin_error = h_flat.GetBinError(ibin)

                    self[zbin_label][ybin_label].SetBinContent(xbin, bin_content)
                    self[zbin_label][ybin_label].SetBinError(xbin, bin_error)

                    ybin_content += bin_content
                    ybin_sumw2 += bin_error*bin_error

                self[zbin_label]._yhist.SetBinContent(ybin, ybin_content)
                self[zbin_label]._yhist.SetBinError(ybin, math.sqrt(ybin_sumw2))

                zbin_content += ybin_content
                zbin_sumw2 += ybin_sumw2

            self._zhist.SetBinContent(zbin, zbin_content)
            self._zhist.SetBinError(zbin, math.sqrt(zbin_sumw2))

    def Reset(self):
        if self._flat:
            self._flat.Reset()

        if self._zhist:
            self._zhist.Reset()

        for zbin_label in self:
            self[zbin_label].Reset()

    def FindBin(self, xval, yval, zval):
        zbin = self._zhist.FindBin(zval)
        if zbin < 1 or zbin > self._zhist.GetNbinsX():
            # underflow or overflow
            return None

        fbin_offset = 0
        for zb in range(1,zbin):
            fbin_offset += self[f"z_bin{zb}"].GetNbins()

        fbin = self[f"z_bin{zbin}"].FindBin(xval,yval)
        if fbin is None:
            # underflow or overflow
            return None
        else:
            return fbin_offset + fbin

    def FindBins(self, xval, yval, zval):
        zbin = self._zhist.FindBin(zval)
        if zbin > 1 or zbin > self._zhist.GetNbinsX():
            # underflow or overflow
            return None, None, None

        xbin, ybin = self[f"z_bin{zbin}"].FindBins(xval, yval)

        return xbin, ybin, zbin

    def GetNbins(self):
        nbins_total = 0

        for zbin_label in self:
            nbins_total += self[zbin_label].GetNbins()

        return nbins_total

    def Fill(self, x, y, z, w=1., skipFlat=False):
        # Fill the z histogram and get the bin index of z
        self._zhist.Fill(z, w)
        zbin = self._zhist.FindBin(z)
        zbin_label = f'z_bin{zbin}'

        # Fill the x and y histogram
        if zbin_label in self:
            self[zbin_label].Fill(x, y, w, skipFlat=True)

        if not skipFlat and self._flat:
            # Fill the flattened histogram
            ibin = self.FindBin(x, y, z)
            if ibin is not None:
                self._flat.AddBinContent(ibin, w)

    def GetFlat(self):
        return self._flat

    def Divide(self, fh3d_denom):
        self._zhist.Divide(fh3d_denom._zhist)

        if self._flat:
            self._flat.Divide(fh3d_denom._flat)

        for zbin_label in self._xyhists:
            self[zbin_label].Divide(fh3d_denom[zbin_label])

    def Write(self, skipFlat=False, savedir=None):
        curdir = gDirectory.GetPath()

        if savedir is None:
            savedir = self.name

        gDirectory.mkdir(savedir)
        gDirectory.cd(savedir)

        if self._zhist:
            self._zhist.SetName(os.path.basename(self._zhist.GetName()))
            self._zhist.Write()

        for zbin_label in self:
            self[zbin_label].Write(skipFlat=True, savedir=zbin_label)

        if not skipFlat and self._flat:
            self._flat.SetName(os.path.basename(self._flat.GetName()))
            self._flat.Write()

        gDirectory.cd(curdir)

class FlattenedResponse():
    def __init__(
        self,
        hname,
        flattenedHist_reco,
        flattenedHist_truth
        ):

        nbins_reco = flattenedHist_reco.GetNbins()
        flat_bins_reco = list(flattenedHist_reco._flat.GetXaxis().GetXbins())

        nbins_truth = flattenedHist_truth.GetNbins()
        flat_bins_truth = list(flattenedHist_truth._flat.GetXaxis().GetXbins())

        self._resp = TH2D(hname, "", nbins_reco, array.array('f', flat_bins_reco), nbins_truth, array.array('f',flat_bins_truth))

        self._fh_reco = flattenedHist_reco
        self._fh_truth = flattenedHist_truth

    def GetResponse(self):
        return self._resp

    def Fill(self, vals_reco, vals_truth, w=1.):
        ibin_reco = self._fh_reco.FindBin(*vals_reco)
        ibin_truth = self._fh_truth.FindBin(*vals_truth)

        if ibin_reco is not None and ibin_truth is not None:
            ibin = self._resp.GetBin(ibin_reco, ibin_truth)
            if ibin is not None:
                self._resp.AddBinContent(ibin, w)

    def GetNbinsX(self):
        return self._resp.GetNbinsX()

    def GetNbinsY(self):
        return self._resp.GetNbinsY()

    def ProjectionX(self, name="_px", firstybin=0, lastybin=-1, options="e"):
        fh_projx = self._fh_reco.copy(name)

        fh_projx.fromFlat(
            self._resp.ProjectionX(name, firstybin, lastybin, options)
        )

        return fh_projx

    def ProjectionY(self, name="_py", firstxbin=0, lastxbin=-1, options="e"):
        fh_projy = self._fh_truth.copy(name)

        fh_projy.fromFlat(
            self._resp.ProjectionY(name, firstxbin, lastxbin, options)
        )

        return fh_projy

    def Write(self):
        self._resp.Write()
