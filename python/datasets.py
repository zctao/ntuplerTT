"""
Utilities to handle datasets
"""

import os
import subprocess
import yaml
import rucio.client

def read_config(config_filepath):
    f = open(config_filepath, 'r')
    return yaml.load(f, yaml.FullLoader)

def did_str2dict(did, scope=None):
    """
    Convert a DID string to a dictionary with keys 'scope' and 'name'
    """
    dlist = did.split(':')
    if len(dlist) == 2:
        if scope is not None:
            print("WARNING: overwrite dataset scope!")
            dlist[0] = scope
        return {'scope': dlist[0], 'name': dlist[1]}
    elif len(dlist) == 1:
        if scope is not None:
            return {'scope': scope, 'name': did}
        else:
            # try guessing the scope if the DID starts with 'user.<username>'
            if did.startswith('user.'):
                scope = '.'.join(did.split('.')[:2])
                return {'scope': scope, 'name': did}

    raise RuntimeError("Failed to get the scope of dataset {}".format(did))

def listFiles_local(dids, directory):
    if not isinstance(dids, list):
        dids = [dids]

    filelist, sizelist = [], []
    for r, dirs, files in os.walk(directory):
        # check if the current root directory matches one of the dids
        matchdir = False
        for did in list(dids):
            if r.endswith(did):
                matchdir = True
                break
        if not matchdir:
            continue

        # add files to the list if they are root files
        for f in files:
            if f.endswith('.root'):
                fullpath = os.path.join(r, f)
                filelist.append(fullpath)
                sizelist.append(os.path.getsize(fullpath))

    return filelist, sizelist

def listFiles_rucio(dids, localSite='CA-SFU-T2_LOCALGROUPDISK', getLocalPath=False):
    if not isinstance(dids, list):
        dids = [dids]

    filelist, sizelist = [], []

    # Rucio client
    rc = rucio.client.Client()

    # get dataset replicas
    replicas = rc.list_replicas([ did_str2dict(d) for d in dids ], schemes=['root'])

    for replica in replicas:
        sites = replicasites = replica['rses'].keys()
        file_path = ''
        if localSite in sites:
            # the data file is available at local site
            file_path = replica['rses'][localSite][0]

            if getLocalPath:
                try:
                    file_path = subprocess.check_output(['getLocalDataPath', 'echo', file_path]).strip('\n')
                except:
                    print("Failed to get local file paths")
        else:
            # the data file is not available at the local site
            # access the file via xrootd
            if replica['pfns']:
                # pick the one with the highest priority
                file_path = max(replica['pfns'].items(), key=lambda pfns:pfns[1]['priority'])[0]

        if file_path:
            filelist.append(file_path)
            sizelist.append(replica['bytes'])

    return filelist, sizelist

def listDataFiles(dids, local_directory=None):
    """ List data file paths and sizes given DIDs
    ______
    Arguments
    dids: str or a list of str; dataset identifiers
    local_directory: str of a list of str; if provided, look for files in this directory

    Return
    A list of str for data file paths, a list int for file sizes in bytes
    """
    if local_directory is not None:
        # look for data files in the local directory
        return listFiles_local(dids, local_directory)
    else:
        # use rucio client API
        # special case on CC Cedar and data files can be accessed directly from local disks
        get_local = 'cedar.computecanada.ca' in os.getenv('HOSTNAME')
        try:
            return listFiles_rucio(dids,getLocalPath=get_local)
        except Exception as e:
            print(e)
            return [],[]

def writeDataFileLists(dataset_config,
                       sample_name,
                       subcampaigns=['mc16a', 'mc16d', 'mc16e'],
                       outdir = '.',
                       njobs=1):
    """ List input file names to be processed to txt files
    These txt files can be used as inputs to the processMiniNtuples.py
    ______
    Arguments
    dataset_config: str; path of the yaml config file for datasets
    sample_name:    str; sample name, key to the yaml dataset config
    subcampaigns:   list of str; subcampaign names, secondary key to the dataset config
    outdir:         str; output directory for the file lists
    njobs:          int; number of jobs to divide the data files into

    Return
    A dictionary of data list file paths.
    Keys: 'tt', 'tt_truth', 'tt_PL', 'sumWeights'
    """

    if not isinstance(subcampaigns, list):
        subcampaigns = [subcampaigns]

    # read dataset config files
    datasets = read_config(dataset_config)

    # suffix to be added to DID
    suffix = ['tt', 'tt_truth', 'tt_PL', 'sumWeights']
    # reco, parton level, particle level, sum of weights

    # get lists of file names and sizes
    datafiles = dict()
    filesizes = dict()
    for s in suffix:
        datafiles[s] = []
        filesizes[s] = []

    for era in subcampaigns:
        data = datasets[sample_name][era]
        for s in suffix:
            lists = listDataFiles(data.rstrip('_')+'_'+s+'.root',
                                  local_directory = datasets.get('directory'))
            datafiles[s] += lists[0]
            filesizes[s] += lists[1]

    # output files
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    fnames_template = dict()
    for s in suffix:
        fnames_template[s] = os.path.join(outdir, 'filelist_'+sample_name+'_'+s+'_{}.txt')

    fnames = dict()
    foutputs = dict()
    for s in suffix:
        fnames[s] = [fnames_template[s].format(0)]
        foutputs[s] = open( fnames[s][0], 'w')
        print("Create file {}".format(fnames[s][0]))

    # iterate over the file list and split files into lists based on size
    total_size = sum(filesizes['tt'])
    ijob = 0
    current_size = 0

    for fsize, freco, ftruth, fPL, fsumw in zip(filesizes['tt'], datafiles['tt'], datafiles['tt_truth'], datafiles['tt_PL'], datafiles['sumWeights']):
        # check the file names are compatible
        i_reco = os.path.basename(freco).split('.')[-3]
        i_truth = os.path.basename(ftruth).split('.')[-3]
        i_PL = os.path.basename(fPL).split('.')[-3]
        i_sumw = os.path.basename(fsumw).split('.')[-3]
        assert(i_reco == i_truth and i_truth == i_PL and i_PL == i_sumw)

        if current_size > total_size / njobs:
            ijob += 1
            current_size = 0
            # close the current output files and create new ones
            for s in foutputs:
                foutputs[s].close()
                fnames[s].append(fnames_template[s].format(ijob))
                foutputs[s] = open( fnames[s][-1], 'w')
                print("Create file {}".format(fnames[s][-1]))

        # write to the output files
        foutputs['tt'].write(freco+'\n')
        foutputs['tt_truth'].write(ftruth+'\n')
        foutputs['tt_PL'].write(fPL+'\n')
        foutputs['sumWeights'].write(fsumw+'\n')

        current_size += fsize

    # close files
    for s in foutputs:
        foutputs[s].close()

    if ijob+1 < njobs:
        print("Warning: not enough data files to split into {} jobs".format(njobs))

    # return a dictionary of the file names
    return fnames
