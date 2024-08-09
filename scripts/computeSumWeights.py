import os
import yaml
import numpy as np
from ROOT import RDataFrame

from datasets import read_config, listDataFiles

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

def getSumWeights(infiles_sumw, treename='sumWeights'):
    df_sumw = RDataFrame(treename, infiles_sumw)
    sumw = df_sumw.Sum("totalEventsWeighted").GetValue()
    return sumw

def getSumWeightsVariations(infiles_sumw, treename='sumWeights'):
    df_sumw = RDataFrame(treename, infiles_sumw)

    # names of the generator weights
    branch_wnames = "names_mc_generator_weights"
    if df_sumw.HasColumn(branch_wnames):
        names_mc_gen_weights = list(df_sumw.Range(1).AsNumpy([branch_wnames])[branch_wnames][0])
    else:
        names_mc_gen_weights = []

    # total weights
    branch_weights = "totalEventsWeighted_mc_generator_weights"
    if df_sumw.HasColumn(branch_weights):
        w_arr_of_vec = df_sumw.AsNumpy([branch_weights])[branch_weights]
        mc_gen_weights = np.asarray([np.asarray(w_vec) for w_vec in w_arr_of_vec]).sum(axis=0).tolist()
    else:
        mc_gen_weights = []

    return mc_gen_weights, names_mc_gen_weights

def computeSumWeights(
    dataset_config,
    local_directory,
    host = '',
    subcampaigns = ['mc16a', 'mc16d', 'mc16e'],
    outdir = None,
    verbosity = 0
    ):

    if verbosity > 1:
        logger.setLevel(logging.DEBUG)
    elif verbosity > 0:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)

    sumw_map = dict()
    sumw_vars_map = dict() # mc generator weight variations

    # maps for fast sim samples
    sumw_afii_map = dict()
    sumw_vars_afii_map = dict()

    logger.info(f"Read dataset config from {dataset_config}")
    datasets_dict = read_config(dataset_config)

    for sample_name in datasets_dict:        
        # skip data
        if sample_name == 'data':
            continue

        if sample_name == 'unused':
            continue

        if sample_name == 'ttbar_AFII':
            sumw_map_tofill = sumw_afii_map
            sumw_vars_map_tofill = sumw_vars_afii_map
        else:
            sumw_map_tofill = sumw_map
            sumw_vars_map_tofill = sumw_vars_map

        logger.info(f"sample {sample_name}")

        for era in subcampaigns:
            logger.info(f"  {era}")

            if not era in datasets_dict[sample_name]:
                logger.warning(f"  {era} not available")
                continue

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
                    logger.warning(f"DSID {dsid} not a number. Skip.")

                logger.debug(f"    {dsid}")

                if not dsid in sumw_map_tofill:
                    sumw_map_tofill[dsid] = {}

                # get the corresponding sumWeight files
                fname_sumw = dn.rstrip('_')+'_sumWeights.root'
                logger.debug(f"    Get sum weights from file {fname_sumw}")

                flist_sumw = listDataFiles(fname_sumw, local_directory, host)[0]

                # compute sum weights
                sumw = getSumWeights(flist_sumw)
                sumw_map_tofill[dsid][era] = sumw

                # compute sum weight variations
                sumw_variations, sumw_names = getSumWeightsVariations(flist_sumw)

                if sumw_variations:
                    if not dsid in sumw_vars_map_tofill:
                        sumw_vars_map_tofill[dsid] = {}
                    logger.debug("File list sum weights:")
                    logger.debug(flist_sumw)
                    sumw_vars_map_tofill[dsid][era] = sumw_variations

                    if sumw_names and "names" not in sumw_vars_map_tofill[dsid]:
                        sumw_vars_map_tofill[dsid]["names"] = sumw_names

    # save the sum weight dict to disk
    if not sumw_map and not sumw_afii_map:
        logger.warning("No sum weight map produced!")
        return

    # replace the prefix of the dataset config file name with 'sumWeights'
    fname_wcfg = os.path.basename(dataset_config)
    fname_wcfg = 'sumWeights'+fname_wcfg[fname_wcfg.find('_'):]

    if outdir is None:
        # save the sum weight file to the same directory as the dataset_config
        outdir = os.path.dirname(dataset_config)

    fname_wcfg = os.path.join(outdir, fname_wcfg)

    if sumw_map:
        logger.info(f"Write sum weight map to file {fname_wcfg}")
        with open(fname_wcfg, 'w') as outfile:
            yaml.dump(sumw_map, outfile)

    # write sumw_afii_map to a separate file if it is not empty
    if sumw_afii_map:
        fname_wcfg_base, fname_wcfg_ext = os.path.splitext(fname_wcfg)
        fname_wcfg_afii = fname_wcfg_base+'_AFII'+fname_wcfg_ext

        logger.info(f"Write sum weight map to file {fname_wcfg_afii}")

        with open(fname_wcfg_afii, 'w') as outfile:
            yaml.dump(sumw_afii_map, outfile)

    # write sum weight variations to files
    if sumw_vars_map:
        fname_wvars_cfg = fname_wcfg.replace("sumWeights", "sumWeights_variations")
        logger.info(f"Write sum weight variations to file {fname_wvars_cfg}")

        with open(fname_wvars_cfg, 'w') as outfile:
            yaml.dump(sumw_vars_map, outfile)

    if sumw_vars_afii_map:
        fname_wvars_afii_cfg = fname_wcfg_afii.replace("sumWeights", "sumWeights_variations")

        logger.info(f"Write sum weight variations to file {fname_wvars_afii_cfg}")

        with open(fname_wvars_afii_cfg, 'w') as outfile:
            yaml.dump(sumw_vars_afii_map, outfile)

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
