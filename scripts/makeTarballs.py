import os
import tarfile

from datasets import getSystTreeNames

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-7s %(name)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
logger = logging.getLogger(__name__)

# Data and data-driven backgrounds
samples_data = ['obs', 'fakes']

# Simulated samples
samples_MC = ['ttbar', 'singleTop_sch', 'singleTop_tch', 'singleTop_tW_DR_dyn', 'Wjets', 'Zjets', 'ttV', 'VV', 'ttH']

# Alternative samples
samples_alt_ttbar = ['ttbar_AFII', 'ttbar_hw', 'ttbar_amchw', 'ttbar_mt169', 'ttbar_mt176', 'ttbar_hdamp', 'ttbar_madspin', 'ttbar_sh2212', 'ttbar_pthard1', 'ttbar_pthard2', 'ttbar_recoil']

samples_alt_bkg = ['singleTop_tW_DS_dyn']

subcampaigns = ['mc16a', 'mc16d', 'mc16e']
years = ['2015', '2016', '2017', '2018']

def makeTarballMC(
    sample_names,
    syst_name,
    sample_top_dir,
    tarfile_name,
    mode = 'w' # or 'a' to append to the existing file
    ):
    logger.info(syst_name)

    with tarfile.open(tarfile_name, mode) as tar:
        # loop over samples
        for sample in sample_names:
            # check if sample directory exists
            sample_dir = os.path.join(sample_top_dir, sample, syst_name)
            if not os.path.isdir(sample_dir):
                logger.debug(f" Directory not found: {sample_dir}")
                continue

            logger.info(f" adding {sample}")

            for era in subcampaigns:
                era_dir = os.path.join(sample_dir, era)
                if not os.path.isdir(era_dir):
                    logger.warning(f"Found no directory {era_dir}! Skipping")
                    continue

                for f in os.listdir(era_dir):
                    arcname = os.path.join(sample, syst_name, era, f)
                    fullname = os.path.join(sample_top_dir, arcname)

                    # only include h5 files
                    if not os.path.isfile(fullname) or os.path.splitext(f)[-1]!=".h5":
                        continue

                    logger.debug(f" {fullname} --> {arcname}")
                    tar.add(fullname, arcname=arcname)

def makeTarballData(
    sample_names,
    sample_top_dir,
    tarfile_name,
    mode = 'w' # or 'a' to append to the existing file
    ):

    with tarfile.open(tarfile_name, mode) as tar:
        for sample in sample_names:
            # check if sample directory exists
            sample_dir = os.path.join(sample_top_dir, sample)
            if not os.path.isdir(sample_dir):
                logger.debug(f" Directory not found: {sample_dir}")
                continue

            logger.info(f" adding {sample}")

            for year in years:
                year_dir = os.path.join(sample_dir, year)
                if not os.path.isdir(year_dir):
                    logger.warning(f"Found no directory: {year_dir}! Skipping")
                    continue

                for f in os.listdir(year_dir):
                    arcname = os.path.join(sample, year, f)
                    fullname = os.path.join(sample_top_dir, arcname)

                    # only include h5 files
                    if not os.path.isfile(fullname) or os.path.splitext(f)[-1]!=".h5":
                        continue

                    logger.debug(f" {fullname} --> {arcname}")
                    tar.add(fullname, arcname)

def makeTarballs(
    data_dir,
    output_dir=None,
    systematics = [],
    ):

    # input sample directory
    top_sample_dir = os.path.expanduser(data_dir)
    if not os.path.isdir(top_sample_dir):
        logger.error(f"Found no sample directory: {top_sample_dir}")
        return

    # output directory
    if output_dir is None:
        # set the output directory under the same directory as the input directory
        output_dir = os.path.join(top_sample_dir, 'tarballs')

    if not os.path.isdir(output_dir):
        logger.info(f"Create a new output directory: {output_dir}")
        os.makedirs(output_dir)

    # systematics config
    SourceDir = os.getenv('SourceDIR')
    if SourceDir is None:
        logger.error("Environment variable 'SourceDIR' is not set.")
        return
    syst_config = os.path.join(SourceDir, 'configs/datasets/systematics.yaml')

    # nominal and systematics
    if not systematics:
        # Take all possible ones if no systematics are provided
        systematics = ['nominal'] + getSystTreeNames(syst_config)

    for syst in systematics:
        makeTarballMC(
            samples_MC,
            syst,
            top_sample_dir,
            tarfile_name = os.path.join(output_dir, f"{syst}.tar"),
        )

        # add alternative background samples here too
        makeTarballMC(
            samples_alt_bkg,
            syst,
            top_sample_dir,
            tarfile_name = os.path.join(output_dir, f"{syst}.tar"),
            mode = 'a' # append
        )

        if syst == 'nominal':
            # add data samples
            makeTarballData(
                samples_data,
                top_sample_dir,
                tarfile_name = os.path.join(output_dir, f"nominal.tar"),
                mode = 'a' # append
            )

    # alternative ttbar samples
    for ttbar_alt in samples_alt_ttbar:
        makeTarballMC(
            [ttbar_alt],
            "nominal",
            top_sample_dir,
            tarfile_name = os.path.join(output_dir, f"{ttbar_alt}.tar")
        )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--data-dir", type=str,
                        default="~/data/ntuplerTT/latest/",
                        help="Local directory where input sample files are stored")
    parser.add_argument("-o", "--output-dir", type=str, 
                        help="Output tarball name")
    parser.add_argument("-s", "--systematics", type=str, nargs="*", default=[],
                        help="List of systematics. If not provided, take all available")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If True, set logging level to debug")
    
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    makeTarballs(args.data_dir, args.output_dir, args.systematics)