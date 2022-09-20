import os
import yaml

from datasets import read_config, listDataFiles
from ntupler import getSumWeights

def computeSumWeights(
    dataset_config,
    local_directory,
    host = '',
    subcampaigns = ['mc16a', 'mc16d', 'mc16e'],
    outdir = None,
    verbosity = 0
    ):

    sumw_map = dict()

    # Another map for ttbar fast sim samples
    sumw_afii_map = dict()

    if verbosity:
        print(f"Read dataset config from {dataset_config}")
    datasets_dict = read_config(dataset_config)

    for sample_name in datasets_dict:        
        # skip data
        if sample_name == 'data':
            continue

        if sample_name == 'unused':
            continue

        if sample_name == 'ttbar_AFII':
            sumw_map_tofill = sumw_afii_map
        else:
            sumw_map_tofill = sumw_map

        if verbosity:
            print(f"sample {sample_name}")

        for era in subcampaigns:
            if verbosity > 1:
                print(f"  {era}")

            dsname = datasets_dict[sample_name][era]
            if isinstance(dsname, str):
                dsname = [dsname]

            for dn in dsname:
                # e.g. user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_s3126_r9364_p4346.TTDIFFXS361_v05.MINI362_v1
                dsid = dn.split('.')[2]
                # try cast dsid to int, otherwise skip
                try:
                    dsid = int(dsid)
                except:
                    print(f"WARNING: DSID {dsid} not a number. Skip.")

                if verbosity > 1:
                    print(f"    {dsid}")

                if not dsid in sumw_map_tofill:
                    sumw_map_tofill[dsid] = {}

                # get the corresponding sumWeight files
                fname_sumw = dn.rstrip('_')+'_sumWeights.root'
                if verbosity > 2:
                    print(f"    Get sum weights from file {fname_sumw}")

                flist_sumw = listDataFiles(fname_sumw, local_directory, host)[0]

                # compute sum weights
                sumw = getSumWeights(flist_sumw)
                sumw_map_tofill[dsid][era] = sumw

    # save the sum weight dict to disk
    if not sumw_map or not sumw_afii_map:
        return

    # replace the prefix of the dataset config file name with 'sumWeights'
    fname_wcfg = os.path.basename(dataset_config)
    fname_wcfg = 'sumWeights'+fname_wcfg[fname_wcfg.find('_'):]

    if outdir is None:
        # save the sum weight file to the same directory as the dataset_config
        outdir = os.path.dirname(dataset_config)

    fname_wcfg = os.path.join(outdir, fname_wcfg)

    if verbosity:
        print(f"Write sum weight map to file {fname_wcfg}")

    with open(fname_wcfg, 'w') as outfile:
        yaml.dump(sumw_map, outfile)

    # write sumw_afii_map to a separate file if it is not empty
    if sumw_afii_map:
        fname_wcfg_base, fname_wcfg_ext = os.path.splitext(fname_wcfg)
        fname_wcfg_afii = fname_wcfg_base+'_AFII'+fname_wcfg_ext

        if verbosity:
            print(f"Write sum weight map to file {fname_wcfg_afii}")

        with open(fname_wcfg_afii, 'w') as outfile:
            yaml.dump(sumw_afii_map, outfile)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Compute sum weights of all samples in a given dataset config file")

    parser.add_argument('dataset_config', type=str,
                        help="Path to the dataset yaml config file")
    parser.add_argument('-l', '--local-dir', type=str,
                        help="Local directory to read sample files. If None, look for datasets via Rucio instead.")
    #parser.add_argument('-s', '--site', choices=['flashy', 'cedar'], default='flashy',
    #                    help="Site to run the script. (Deprecated)")
    parser.add_argument('-o', '--outdir', type=str, default=None,
                        help="Output directory. If None, use the same directory as the dataset_config")
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                        help="Verbosity level")

    args = parser.parse_args()

    computeSumWeights(
        args.dataset_config,
        args.local_dir,
        outdir = args.outdir,
        verbosity = args.verbosity
    )
