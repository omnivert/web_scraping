import requests, csv, logging
from bs4 import BeautifulSoup as bsp
from os import walk
from pathlib import Path as pth

# TINY LITTLE RETHINK
# i need to track the tree: ovide -> cycle name -> fol no.
# that needs to be the directory structure for chris
# and the naming scheme should reflect info, so like
# 'bruges_colard_mansion_fol_6v_55831.pdf
# the last group of numbers being the record id, which i'm 
# pretty sure are globally (if not locally) unique.

# so this all means i should do a few things
# 1st -> refactor into reusable pieces, there's a lot of 
# duplicated effort in this program
# 2nd -> add argparse, -v option, -h option, --gen-wget option
# 3rd -> add internal structure that maintains site tree
# ### tree structure added ###
# 4th -> implement --gen-wget output
# 5th -> write internal tree to csv. hm.
# that's all for now, more work to follow

###### SETUP THINGS ######

# logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# basic tree with arbitrary children, thank you stackoverflow
# data is expected to be a dict with the following values:
#   url
#   name (might have to specify regex or something)
#   parent (path on filesystem)

class Node:
    def __init__(self, branches=None, trunk=None, **kwargs):
        self.branches = branches or []
        self.data = kwargs
        self.trunk = trunk
        for branch in self.branches:
            branch.trunk = self

    # TODO might not need this
    def assign_branches(self, branchlist):
        for branch in branchlist:
            branch.trunk = self
            self.branches.append(branch)

    def get_level(self, level):
        if level == 0:
            return [self]
        elif self.branches == []:
            return []
        else:
            level_n_nodes = []
            for branch in self.branches:
                level_n_nodes = level_n_nodes + branch.get_level(level-1)
            return level_n_nodes

# hmmmmmmm
# i think i just need to think about this on paper
# take site node, branchrules (function)
# return list of branches
## IMPORTANT CONVENTION ##
# fname is the filename, not the full path. we're patching things together
# when we write files with cwd + filename. only reason for this is to 
# simplify the creation and standardization of the fname.d subdirs
def expand_branches(node, branchrules, dirnamerules, urlrules, fnamerules):
    cwd = node.data['cwd']
    fname = node.data['fname']    
    with open(cwd+'/'+fname) as f:
        content = f.read()
    logger.debug('expanding {} branches...'.format(fname))
    soup = bsp(content, 'html.parser')
    # this applies the branchrules lambda to the parsed soup
    branch_url_list = branchrules(soup)
    # this applies the dirnamerules lambda to cwd and fname
    cwd = dirnamerules(cwd, fname)
    pth('./{}'.format(cwd)).mkdir(parents=True, exist_ok=True)
    # now for the population of branch nodes
    branches = []
    for branch_url_suffix in branch_url_list:
        branch_url = urlrules(branch_url_suffix)
        branch_fname = fnamerules(branch_url)
        branches.append(Node(trunk=node, url=branch_url, fname=branch_fname, cwd=cwd))
    return branches

# deals with downloading URL and saving it to the filesystem
# mkdir -p parent dir
# check if page present
# if not, download 
def download_pages(nodelist):
    # WARNING this is a big assumption, but it's our code so fuck it
    # EVERYTHING IN NODELIST MUST HAVE THE SAME CWD
    cwd = nodelist[0].data['cwd']
    pth('./{}'.format(cwd)).mkdir(parents=True, exist_ok=True)
    htmlpages = []
    for _, _, fnames in walk(cwd):
        htmlpages.extend(fnames)
    for node in nodelist:
        fname = node.data['fname']
        if fname not in htmlpages:
            page = requests.get(node.data['url'])
            with open('./{}/{}'.format(cwd, fname), 'w') as f:
                logger.debug('writing {}/{}...'.format(cwd, fname))
                f.write(page.text)
        else:
            logger.debug('file {}/{} already exists'.format(cwd, fname))
    
###### DOWNLOAD ALL REQUIRED HTML PAGES ######

warburg_vpc_url = 'https://iconographic.warburg.sas.ac.uk/vpc/'
warburg_search_url = warburg_vpc_url + 'VPC_search/'
ovide_cycles_suffix = 'subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
#cycles_url = 'https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
cycles_url = warburg_search_url + ovide_cycles_suffix

cycles_trunk = Node([], url=cycles_url, fname='cycles.html', cwd='htmlpages')
download_pages([cycles_trunk])
# def expand_branches(node, branchrules, dirnamerules, urlrules, fnamerules):
# expand and dl first level, just the cycle mainpages
cycles = expand_branches(cycles_trunk, 
                         (lambda x: x.div.table.find_all_next('a')), 
                         (lambda x, y: x + '/' + y.split('.')[0] + '.d'), 
                         (lambda x: warburg_search_url + x['href']), 
                         (lambda x: 'cycle_' + x[111:] + '.html'))
cycles_trunk.branches = cycles
download_pages(cycles)
# expand and dl second level, image info pages
# TESTING get_level FUNCTION
l_0 = cycles_trunk.get_level(0)
l_1 = cycles_trunk.get_level(1)
print('level 0')
for node in l_0:
    print(node.data['fname'])
print('level 1')
for node in l_1:
    print(node.data['fname'])

