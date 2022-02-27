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

    if verbosity:
        print(f"Read dataset config from {dataset_config}")
    datasets_dict = read_config(dataset_config)

    for sample_name in datasets_dict:        
        # skip data
        if sample_name == 'data':
            continue

        if sample_name == 'unused':
            continue

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
                dsid = int(dn.split('.')[2])
                if verbosity > 1:
                    print(f"    {dsid}")

                if not dsid in sumw_map:
                    sumw_map[dsid] = {}

                # get the corresponding sumWeight files
                fname_sumw = dn.rstrip('_')+'_sumWeights.root'
                if verbosity > 2:
                    print(f"    Get sum weights from file {fname_sumw}")

                flist_sumw = listDataFiles(fname_sumw, local_directory, host)[0]

                # compute sum weights
                sumw = getSumWeights(flist_sumw)
                sumw_map[dsid][era] = sumw

    # save the sum weight dict to disk
    if not sumw_map:
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
