#!/usr/bin/env python3
import requests
import yaml
import re
import os

from datasets import read_config

def applyFilters(sample_name, expressions, case_sensitive=False):
    # Examples:
    # expressions = "!keyword1 && (keyword2 || keyword3)"
    # expressions = "keyword1 or keyword2 and not keyword3"

    # convert to syntax correct logic operators for python
    expressions = expressions.replace("!", " not ")
    expressions = expressions.replace("&&", " and ")
    expressions = expressions.replace("||", " or ")

    if not case_sensitive:
        expressions = expressions.lower()
        sample_name = sample_name.lower()

    # extract the list of keywords
    kw_list = re.split(r"not\W+|\W+and\W+|\W+or\W+|\(|\)", expressions)
    # remove empty string
    kw_list = list(filter(None, kw_list))

    # check the keyword in sample_name
    res_list = []
    for kw in kw_list:
        res_list.append(kw in sample_name)

    # replace the result for the corresponding keyword
    for kw, res in zip(kw_list, res_list):
        expressions = expressions.replace(kw, str(res))

    # evaluate the expression and return
    return eval(expressions)

def parseDataFileName(filename, scope, version_tag='v01_p4345'):
    # Example: data.2015.physics_Main.TTDIFFXS376_v2.MINI_v01
    results = {}

    fname_split = filename.split('.')

    # check it is data sample
    assert(fname_split[0] == 'data')
    results['label'] = 'data'

    year = fname_split[1]
    results['era'] = year
    # last two digits
    yy = year[-2:]

    # Because the file name is not exact the same as the dataset name in rucio
    # construct dataset name
    tag = f'grp{yy}_'+version_tag

    results['dataset_name'] = filename.replace(
        f'data.{year}.physics_Main',
        f'{scope}.AllYear.physics_Main.DAOD_TOPQ1.{tag}')

    return results

def parseMCFileName(filename, scope):
    # Example: mc.410470.PhPy8EG.e6337_s3126_r9364_p4514.TTDIFFXS376_v1.MINI_v01_tt.txt
    results = {}

    fname_split = filename.split('.')

    # check it is MC sample
    assert(fname_split[0] == 'mc')

    dsid = fname_split[1]
    physics_short = fname_split[2]
    tags = fname_split[3]

    # FIXME hard code the config file path here
    fpath_config = os.path.join(
        os.getenv("SourceDIR"), "configs/datasets/general_ttDiffXSRun2.yaml"
    )
    assert(os.path.isfile(fpath_config))
    dsgen_dict = read_config(fpath_config)

    results['label'] = None
    for l in dsgen_dict['dsid']:
        if int(dsid) in dsgen_dict['dsid'][l]:
            results['label'] = l
            break

    results['era'] = None
    for e, t in dsgen_dict['subcampaign_tag'].items():
        if t in tags:
            results['era'] = e
            break

    dsname = filename.replace('mc.', f'{scope}.')
    dsname = dsname.replace(physics_short, physics_short+'.DAOD_TOPQ1')
    results['dataset_name'] = dsname

    return results

def processPage(datasets_dict, json_from_requests, scope='user.mromano', filters=[]):

    for entry in json_from_requests:
        sample_name = entry['name']

        # Only need to check the file name that ends with '_tt.txt'
        if not sample_name.endswith('_tt.txt'):
            continue

        # filters
        if filters:
            expressions = ' and '.join(filters)
            pass_filters = applyFilters(sample_name, expressions)
            if not pass_filters:
                continue

        # strip the suffix
        dataset_name = sample_name.replace('_tt.txt','')
        #print(dataset_name)

        # Have to edit the file name in order to match the dataset name in rucio
        if dataset_name.startswith('data.'):
            # data sample
            sample_dict = parseDataFileName(dataset_name, scope=scope)
        elif dataset_name.startswith('mc.'):
            # MC sample
            sample_dict = parseMCFileName(dataset_name, scope=scope)
        else:
            raise RuntimeError(f"Cannot parse file name {dataset_name}")

        if sample_dict['label'] is None:
            print(f"Cannot determine the label for {dataset_name}")
            continue

        if sample_dict['era'] is None:
            print(f"Cannot determine the year/subcampaign for {dataset_name}")
            continue

        if not sample_dict['label'] in datasets_dict:
            datasets_dict[ sample_dict['label'] ] = {}

        if not sample_dict['era'] in datasets_dict[ sample_dict['label'] ]:
            datasets_dict[sample_dict['label']][sample_dict['era']] = list()

        datasets_dict[ sample_dict['label'] ][ sample_dict['era'] ].append(
            sample_dict['dataset_name'])

    # end of for entry in json_from_requests

    return datasets_dict

def isPreferredSample(sample_name, sample_name_ref):
    # Return True is sample_name is preferred compared to sample_name_ref
    # Otherwise, return False

    # sample_name example:
    # user.mromano.410470.PhPy8EG.DAOD_TOPQ1.e6337_a875_r9364_p4346.TTDIFFXS361_v08.MINI362_v1_klfitter"

    # first check the first part of sample names are the same
    # Assume all samples are DAOD_TOPQ1
    sname_tuple = sample_name.partition('.DAOD_TOPQ1.')
    sname_ref_tuple = sample_name_ref.partition('.DAOD_TOPQ1.')

    #assert(sname_tuple[0] == sname_ref_tuple[0])
    if sname_tuple[0] != sname_ref_tuple[0]:
        raise RuntimeError(f"Not same sample? {sample_name} {sample_name_ref}")

    suffix = sname_tuple[-1]
    suffix_ref = sname_ref_tuple[-1]

    # Pick the latest MINI ntuple version
    mini_ver_str = suffix.partition('MINI')[-1]
    if len(mini_ver_str.split('_')) < 2:
        # no version info
        mini_ver = 0
    else:
        mini_ver = int(mini_ver_str.split('_')[1].lstrip('v'))

    mini_ver_ref_str = suffix_ref.partition('MINI')[-1]
    if len(mini_ver_ref_str.split('_')) < 2:
        # no version info
        mini_ver_ref = 0
    else:
        mini_ver_ref = int(mini_ver_ref_str.split('_')[1].lstrip('v'))

    if mini_ver > mini_ver_ref:
        return True
    elif mini_ver < mini_ver_ref:
        return False

    # mini_ver == mini_ver_ref

    # Pick full sim ("_sxxxxx_") over fast sim ("_axxxxx_")
    tags = suffix.split('.')[0]
    isFastSim = '_a' in tags

    tags_ref = suffix_ref.split('.')[0]
    isFastSim_ref = '_a' in tags_ref

    if not isFastSim and isFastSim_ref:
        return True
    elif isFastSim and not isFastSim_ref:
        return False

    # A rare case: ntuple version
    # eg. TTDIFFXS361_v09 vs TTDIFFXS361_v08
    ttdiffxs_ver = suffix.partition('TTDIFFXS')[-1]
    ttdiffxs_ver_ref = suffix_ref.partition('TTDIFFXS')[-1]
    if ttdiffxs_ver > ttdiffxs_ver_ref:
        return True
    elif ttdiffxs_ver < ttdiffxs_ver_ref:
        return False

    # cannot decide
    # something's wrong
    raise RuntimeError(f"Cannot decide which to choose: {sample_name} {sample_name_ref}")

def removeDuplicates(datasets):
    # Clean up the sample list
    # Each datasets[label][era] should only contain one entry per dsid
    # Pick the latest/best version from duplicates

    # An 'unused' dict to hold the unused samples
    datasets_unused = {}

    for label in datasets:
        for era in datasets[label]:
            sample_list = datasets[label][era]

            dsid_dict = {}
            for i, name in enumerate(sample_list):
                try:
                    dsid = int(name.split('.')[2])
                except:
                    # Likely a data sample. Skip for now
                    dsid = int(era)

                if not dsid in dsid_dict:
                    dsid_dict[dsid] = name
                else:
                    # found a duplicate
                    if not label in datasets_unused:
                        datasets_unused[label] = {}
                    if not era in datasets_unused[label]:
                        datasets_unused[label][era] = list()

                    # name vs dsid_dict[dsid]
                    if isPreferredSample(name, dsid_dict[dsid]):
                        # Put the current one in 'unused'
                        datasets_unused[label][era].append(dsid_dict[dsid])
                        # Replace with the new one
                        dsid_dict[dsid] = name
                    else:
                        # add this one to the unused samples
                        datasets_unused[label][era].append(name)
            # end of for i, name in enumerate(sample_list)

            # update sample list
            datasets[label][era] = list(dsid_dict.values())

        # end of for era in datasets[label]
    # end of for label in datasets

    # add datasets_unused to datasets
    if datasets_unused:
        datasets['unused'] = datasets_unused

def produceSampleList(url, headers, output='dataset_list.yaml', filters=[]):
    datasets_dict = dict()

    r = requests.get(url, headers=headers)
    processPage(datasets_dict, r.json(), filters=filters)

    while 'next' in r.links:
        r = requests.get(r.links['next']['url'], headers=headers)
        processPage(datasets_dict, r.json(), filters=filters)

    # clean up the sample list
    removeDuplicates(datasets_dict)

    # write to file
    if datasets_dict:
        with open(output, 'w') as outfile:
            yaml.dump(datasets_dict, outfile)
    else:
        print("WARNING: no sample found")

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('token', type=str,
                        help="Gitlab access token")
    parser.add_argument('-s', '--sample-tag', type=str, default="MINI362_v1",
                        help="Mini-ntuple production tag")
    parser.add_argument('-f', '--filters', default=[], type=str, nargs='*',
                        help="List of filter words to select samples")
    parser.add_argument('-o', '--output', type=str, default='dataset_list.yaml',
                        help="Output file")

    args = parser.parse_args()

    # project info
    # https://gitlab.cern.ch:8443/ttbarDiffXs13TeV/pyTTbarDiffXs13TeV
    project = "17479"
    branch = "DM_ljets_resolved"
    sampletag = args.sample_tag
    headers={"PRIVATE-TOKEN": args.token}
    per_page=100

    url = f"https://gitlab.cern.ch/api/v4/projects/{project}/repository/tree?ref={branch}&path=data/CERN/filelists_{sampletag}&per_page={per_page}&pagination=keyset"

    produceSampleList(url, headers, args.output, filters=args.filters)
