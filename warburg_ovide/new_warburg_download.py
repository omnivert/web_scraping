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
    def __init__(self, children=None, parent=None, **kwargs):
        self.children = children or []
        self.parent = parent
        self.data = kwargs
        for child in self.children:
            child.parent = self

# takes a node, naming regex, and outputs proper filename
# maybe expect namerules to be nameless function
# then the text of this method is more like
# node.data[path] + namerules(node.data[url])
# TODO test this out, mb move to new file, treat this one as reference?
def gen_filename(node, namerules):
    print('gen_filename')
    exit(0)

# another string gen that takes a function
# in this case we want to make a url
def gen_leaf_url(node, namerules):
    print('gen_leaf_url')
    exit(0)

# hmmmmmmm
# i think i just need to think about this on paper
# take site node
#   contains url, html data as soup, cwd, "location" ie search terms to find leaves
def find_leaves(node):
    print('find_leaves')
    exit(0)

# mkdir -p parent dir
# check if page present
# if not, download
def download_page(node):
    cwd = node.data['cwd']
    fname = node.data['fname']
    pth('./{}'.format(cwd)).mkdir(parents=True, exist_ok=True)
    htmlpages = []
    for _, _, fnames in walk(cwd):
        htmlpages.extend(fnames)
    if fname not in htmlpages:
        page = requests.get(node.data['url'])
        with open('./{}/{}'.format(cwd, fname), 'w') as f:
            logger.debug('writing {}/{}...'.format(cwd, fname))
            f.write(page.text)
    else:
        logger.debug('file {}/{} already exists'.format(cwd, fname))
    
###### DOWNLOAD ALL REQUIRED HTML PAGES ######

# so each time i'm downloading a bunch of stuff, what i'm actually doing is:
# setting correct URL
# setting correct cwd
# checking and making cwd
# downloading url html contents to memory (soup)
# finding and returning all URLs i care about

warburg_vpc_url = 'https://iconographic.warburg.sas.ac.uk/vpc/'
warburg_search_url = warburg_vpc_url + 'VPC_search/'
ovide_cycles_suffix = 'subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
#cycles_url = 'https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
cycles_url = warburg_search_url + ovide_cycles_suffix

cycles = Node([], url=cycles_url, fname='cycles.html', cwd='htmlpages')
download_page(cycles)
exit(0)
# TODO TEST TEST TEST
