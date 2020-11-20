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
    cwd = node.data[cwd]
    fname = node.data[fname]
    pth('./{}'.format(cwd)).mkdir(parents=True, exist_ok=True)
    htmlpages = []
    for _, _, fnames in walk(cwd):
        htmlpages.extend(fnames)
    if fname not in htmlpages:
        page = requests.get(node.data[url])
        with open('./{}/{}'.format(cwd, fname), 'w') as f:
            logger.debug('writing {}/{}...'.format(cwd, fname))
            f.write(page.text)
    
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

#warburg_vpc_url = 'https://iconographic.warburg.sas.ac.uk/vpc/'
#warburg_search_url = warburg_vpc_url + 'VPC_search/'
#ovide_cycles_suffix = 'subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
##cycles_url = 'https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
#cycles_url = warburg_search_url + ovide_cycles_suffix
## if the downloaded html page doesn't exist, save it
cycles_fname = 'cycles.html'
## TODO check for existence of htmlpages dir
cwd = 'htmlpages'
pth('./'+cwd).mkdir(parents=True, exist_ok=True)
htmlpages = []
for _, _, fnames in walk(cwd):
    htmlpages.extend(fnames)
if cycles_fname not in htmlpages:
    page = requests.get(cycles_url)
    with open(cwd+'/'+cycles_fname, 'w') as f:
        logger.debug('writing ' + cwd+'/'+cycles_fname + '...')
        f.write(page.text)
else:
    logger.debug('file '+cwd+'/'+cycles_fname+' already exists')
# now parse all the cycles in the list:
with open(cwd+'/'+cycles_fname) as f:
    content = f.read()
logger.debug('parsing cycle list...')
soup = bsp(content, 'html.parser')
cycle_list = soup.div.table.find_all_next('a')
cycle_url_list = []
for cycle_url in cycle_list:
    cycle_full_url = warburg_search_url+cycle_url['href']
    cycle_url_list.append(cycle_full_url)
# now we move one dir down
htmlpages_cyclesd = []
cwd = 'htmlpages/cycles.d'
pth('./'+cwd).mkdir(parents=True, exist_ok=True)
# like above, make a list of what's already in the dir for checks
for _, _, fnames in walk(cwd):
    htmlpages_cyclesd.extend(fnames)
# now for each cycle url name the html page the cat5 number in the url,
# check if that file exists, if not download and save
for c_url in cycle_url_list:
    c_fname = 'cycle_'+c_url[111:]+'.html'
    if c_fname not in htmlpages_cyclesd:
        page = requests.get(c_url)
        with open(cwd+'/'+c_fname, 'w') as f:
            logger.debug('writing ' + cwd+'/'+c_fname + ' ...')
            f.write(page.text)
    else:
        logger.debug('file '+cwd+'/'+c_fname+' already exists')

# now for the large group download
# so this is for each cycle, download all associated
# fol. html files, then all the corresponding pdfs
for c_url in cycle_url_list:
    cwd = 'htmlpages/cycles.d'
    with open(cwd+'/'+'cycle_'+c_url[111:]+'.html') as f:
        c_content = f.read()
    logger.debug('parsing cycle_{}.html...'.format(c_url[111:]))
    sp = bsp(c_content, 'html.parser')
    pg_list = sp.div.table.find_all_next('a')[1:]
    pg_url_list = []
    for pg in pg_list:
        pg_url = warburg_search_url+pg['href']
        pg_url_list.append(pg_url)
    pg_url_list = list(set(pg_url_list[:]))
    c_dname = 'cycle_'+c_url[111:]+'.d'
    cwd = 'htmlpages/cycles.d/'+c_dname
    pth('./'+cwd).mkdir(parents=True, exist_ok=True)
    pg_htmlpages = []
    for _, _, fnames in walk(cwd):
        pg_htmlpages.extend(fnames)
    # now at last, we've parsed things, time to download things
    for pg_url in pg_url_list:
        pg_fname = 'record_'+pg_url[72:]+'.html'
        if pg_fname not in pg_htmlpages:
            page = requests.get(pg_url)
            with open(cwd+'/'+pg_fname, 'w') as f:
                logger.debug('writing ' + cwd+'/'+pg_fname + ' ...')
                f.write(page.text)
        else:
            logger.debug('file '+cwd+'/'+pg_fname+' already exists')

        # now to download the pdfs
        # BECAUSE I'M SO GREAT, i can build the link directly without
        # even dealing with the iframe garbage.
        img_cwd = 'pdfs'
        with open(cwd+'/'+pg_fname) as f:
            r_content = f.read()
        record_sp = bsp(r_content, 'html.parser')
# lol TODO 
# some of these images / pdfs are hosted externally. 
# at least the ones on BnF gallica look pretty simple to pull
# no iframe bs

        logger.debug(pg_fname)
        logger.debug(pg_url)
        external_img = 'photo on external web page' in r_content
        logger.debug(external_img)
        img_id = record_sp.img.find_parent()['href']
        logger.debug(img_id)
        if not external_img:
            # pdfs are of the form
            # https://iconographic.warburg.sas.ac.uk/vpc/pdfs_wi_id/00028642.pdf
            img_link = warburg_vpc_url + 'pdfs_wi_id/' + img_id[21:] + '.pdf'
            
            logger.debug(img_link)
        exit(0)

