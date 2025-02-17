import re, requests, csv, logging
from bs4 import BeautifulSoup as bsp
from os import walk
from pathlib import Path as pth
from itertools import chain

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
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# don't need all this shit, is mainly just confusing
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(levelname)s > %(message)s')
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

    def assign_branches(self, branchlist):
        #logger.debug('{}.assign_branches({})'.format(self.data['fname'], branchlist))
        for branch in branchlist:
            branch.trunk = self
            self.branches.append(branch)
            #logger.debug('varcheck. trunk should = {}.\nvars: {}'.format(branch.trunk, vars(branch)))

    def print_info(self):
        print('self.trunk: {}'.format(self.trunk))
        print('self: {}'.format(self))
        print('self.branches: {}'.format(self.branches))
        print('self.trunk.branches: {}'.format(self.trunk.branches))

    def print_tree(self, maxdepth=5, level=0):
        # this is kinda specific for this site, but eh
        if maxdepth > 0:
            prefix = '+-- '
            for _ in range(level):
                prefix = '|   ' + prefix
            # fname = self.data['fname'] if len(self.data['fname']) < 20 else self.data['fname'][:18] + '...'
            fname = self.data['fname']
            print(prefix + fname)
            print(prefix[:-4] + '    ' + self.data['cwd'] + '/' + self.data['fname'])
            # this was useful and the right way to find obj attrs
            # but for now, need to put these prints somewhere else to 
            # trace things
            #allvars = vars(self)
            #print(prefix[:-4] + '    ' + '(allvars: {})'.format(allvars))
            if 'jpeg' in self.data['fname'] or 'pdf' in self.data['fname']:
                #print(prefix[:-4] + '    ' + '>> IMG SPECIFIC INFO <<')
                print(prefix[:-4] + '    ' + self.data['url'])
            if 'metadata' in self.data:
                print(prefix[:-4] + '    ' + self.data['metadata'])
                print(prefix[:-4] + '  - {}'.format(self.data['metadata_dict']))
                print(prefix[:-4] + '  - ' + self.data['fol'])
            for branch in self.branches:
                branch.print_tree(maxdepth=maxdepth-1, level=level+1)

    def swap_for(self, node):
        #self.print_info()
        if self.trunk:
            self.trunk.branches.append(node)
            self.trunk.branches.remove(self)
        # this self.branches is probably the issue
        node.trunk = self.trunk
        node.assign_branches(self.branches)
        #logger.debug('varcheck. trunk should = {}.\nvars: {}'.format(self.trunk, vars(node)))

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
def expand_branches(node, branchrules, dirnamerules, urlrules, fnamerules, debug=False, sort=False, limit=0):
    # to deal with the case of images, i think what we want to do is treat branchrules
    # as a dict of { content check : branchrule }, so like 
    #   soup.text.contains('external site') : branchrules 
    # or something like that
    # remember some way to preserve the file extension
    # ...urlrules might also have to be a dict. gross

    cwd = node.data['cwd']
    fname = node.data['fname']    
    with open(cwd+'/'+fname) as f:
        content = f.read()
    logger.debug('    > expanding {} branches...'.format(fname))
    soup = bsp(content, 'html5lib')
    # this applies the branchrules lambda to the parsed soup
    branch_url_list = branchrules(soup)
    # TODO BS4 Tag has no compare operator for < and >
    #if sort:
    #    branch_url_list = sorted(branch_url_list)
    # this applies the dirnamerules lambda to cwd and fname
    cwd = dirnamerules(cwd, fname)
    pth('./{}'.format(cwd)).mkdir(parents=True, exist_ok=True)
    # now for the population of branch nodes
    branches = []
    urls = []
    for i, branch_url_suffix in enumerate(branch_url_list):
        if limit > 0 and i >= limit:
            break
        # TODO we need this on the last pass to just make the correct format
        # final image URL - template is listed in the last call to branchnodes
        branch_url = urlrules(branch_url_suffix)
        if branch_url in urls:
            continue
        urls.append(branch_url)
        # crazy this next line actually works
        branch_fname = fnamerules(branch_url)
        branches.append(Node(trunk=node, url=branch_url, fname=branch_fname, cwd=cwd))
        if debug:
            logger.debug('cwd {}; fname {}; url {}'.format(cwd, branch_fname, branch_url))
    return branches

# deals with downloading URL and saving it to the filesystem
# mkdir -p parent dir
# check if page present
# if not, download 
def download_pages(nodelist):
    logger.debug('    > downloading pages...')
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

def scrape_metadata(node):
    # this is only about the images
    # so node.trunk is where we get metadata from
    # we use it to populate metadata field

    # for record 94072
    # t1 is grey_larger
    # t2 grey_small
    # everything else is content
    # it feels like the easiest way to do this is to parse first
    # list whatever order you see, t1 t2 c t2 c t1 t2 c whatever
    # then convert that to a tree
    # THEN find some way of representing that in text / csv form
    # then that's the metadata and maybe we can finally download
    # these goddamn things? 
    # i'd really like to get this done. and the holiday letter 
    # 
    # after getting the above done, we need to get everything ready
    # for the csv. i think i want to do that before download / 
    # download logic.
    # broad strokes:
    # - we want something that likes multiple lines for the metadata
    # - other than that save like csv, commas and newlines
    #   or whatever, just need to be able to import into excel
    # - fields to export:
    #   - fname/loc
    #   - url
    #   - fol.
    #   - metadata
    # - export like that
    # - then, downloading is weird. generating the file with all
    #   the curl commands seemed to be the best way to do things?
    # - then.... we're good?
    #   
    # doesn't seem too bad. keep a level head, slow pace, breaks 
    # for the brain.

    #metadata = node.data['fname'] + ' testdata'
    new_node = Node()
    new_node.data = node.data
    # this is where we're actually pulling the metadata
    # i can't believe it, we're actually pulling the metadata we need
    metadata = 'placeholder'
    trunknode = node.trunk

    cwd = trunknode.data['cwd']
    fname = trunknode.data['fname']    
    with open(cwd+'/'+fname) as f:
        content = f.read()
    logger.debug('    > scraping {} metadata...'.format(fname))
    soup = bsp(content, 'html5lib')
    metadata = soup.body.table.find_next_sibling()
    metadata_text = metadata.text
    # build our silly little metadata dict
    metadata_dict = {}
    cur_key = ''
    # TODO TODO TODO
    # this is reading certain lines as > just a heading / class
    # for instance: 
    # 'found metadata class: -> the story of cadmus .... LITERATUREAncient -> ...' 
    # and so on
    for tr in metadata.find_all('tr')[1:]:
        if tr.find('span', class_='grey_small') is not None:
            #logger.debug('found metadata class: {}'.format(tr.text))
            cur_key = tr.text
            metadata_dict[cur_key] = ''
        else:
            if cur_key != '':
                metadata_dict[cur_key] = metadata_dict[cur_key] + tr.text
                
    tables = soup.body.table.find_next_siblings()
    fol_text_raw = [x.text for x in tables[1].find_all('tr') if 'fol.' in x.text]
    if len(fol_text_raw) > 0:
        fol = fol_text_raw[0][fol_text_raw[0].find('fol.'):]
    else:
        fol = ''

    new_node.data['metadata'] = metadata_text
    new_node.data.update(metadata_dict)
    new_node.data['fol'] = fol
    cycle_fname = trunknode.trunk.data['fname']
    new_node.data['fname'] = ''.join('_' if c in '(),' else c for c in new_node.data['fname'].replace('template', cycle_fname.replace('.html', '-') + fol.replace('.', '').replace(' ', '_')))
    if 'LITERATURE' in new_node.data:
        new_node.data['cycle'] = new_node.data['LITERATURE'][new_node.data['LITERATURE'].find('Cycles')+9:]
    new_node.data['cycle_code'] = new_node.data['fname'][:new_node.data['fname'].find('-')]
    node.swap_for(new_node)
    #logger.debug('newnode metadata = {}'.format(new_node.data['metadata']))
    return node

def dictify(nodelist):
    # first we make a dict w every node
    dictlist = []
    for node in nodelist:
        data = node.data.copy()
        dictlist.append(data)

    # https://stackoverflow.com/questions/10482439/make-sure-all-dicts-in-a-list-have-the-same-keys
    all_keys = set(chain.from_iterable(dictlist))
    for item in dictlist:
         item.update({key: '' for key in all_keys if key not in item})
    return dictlist

def gen_wget_commands(nodelist):
    wgetlist = []
    for node in nodelist:
        wgetlist.append('wget -q -O {}/{} {}'.format(node.data['cwd'], node.data['fname'], node.data['url']))
    return list(set(wgetlist))

    
def check_collisions(nodelist, key):
    print('checking for {} collisions...'.format(key))
    checked = {}
    collided = 0
    for node in nodelist:
        to_check = node.data[key]
        #print('checking {}...'.format(to_check))
        if to_check in checked:
            print('{} COLLISION: {} is a duplicate'.format(key, to_check))
            print('    collision info:')
            print('    - collider')
            print('      - trunk: {}/{}'.format(node.trunk.data['cwd'], node.trunk.data['fname']))
            print('      - url: {}'.format(node.trunk.data['url']))
            print('    - collidee')
            print('      - trunk: {}/{}'.format(checked[to_check][0].trunk.data['cwd'], checked[to_check][0].trunk.data['fname']))
            print('      - url: {}'.format(checked[to_check][0].trunk.data['url']))
            collided += 1
            checked[to_check].append(node)
        else:
            checked[to_check] = [node]
    if collided == 0:
        print('no collisions detected')
    else:
        print('detected {} collisions'.format(collided))
    
###### DOWNLOAD ALL REQUIRED HTML PAGES ######

# NOTE i think this structure has merit, but it gets kinda gross too...
# i want to just do something like f ( g ( h ( x ) ) ) or something, but 
# that also strikes me as really messy

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
                         (lambda x: 'cycle_' + x[111:] + '.html'),
                         sort=True)
cycles_trunk.assign_branches(cycles)
download_pages(cycles)

# now branches of first level, fols in a cycle
for cycle in cycles_trunk.get_level(1):
    fols = expand_branches(cycle,
                          (lambda x: list(set(x.div.table.find_all_next('a')[1:]))), 
                          (lambda x, y: x + '/' + y.split('.')[0] + '.d'), 
                          (lambda x: warburg_search_url + x['href']), 
                          (lambda x: 'record_' + x[72:] + '.html'),
                          sort=True, debug=True)
    cycle.assign_branches(fols)
    download_pages(fols)

# now for the images, eg branches of the seconds level
# gallica urls: 
#   http://gallica.bnf.fr/ark:/12148/bpt6k8523959/f747.item
#   http://gallica.bnf.fr/ark:/12148/bpt6k8523959/f89.image.html
#       or
#   https://gallica.bnf.fr/ark:/12148/bpt6k8523959/f89.highres
#
# warburg urls:
#   pdf_portal.php?image=00012901
#   https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/pdf_portal.php?image=00028680
#   https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/pdf_frame.php?image=00028680
#       or
#   https://iconographic.warburg.sas.ac.uk/vpc/pdfs_wi_id/00028680.pdf
#   https://iconographic.warburg.sas.ac.uk/vpc/pdfs_wi_id/00028642.pdf


for fol in cycles_trunk.get_level(2):
    images = expand_branches(fol,
                            (lambda x: [x.img.find_parent()['href']]), 
                            (lambda x, y: 'images'), 
                            (lambda x: re.sub(r'(\.[a-z]+)+$', '.jpeg', x) if 'gallica' in x else warburg_vpc_url + 'pdfs_wi_id/' + x[21:] + '.pdf'), 
                            (lambda x: 'template-'+x.split('/')[-1]),
                            debug=True)
    # annoyingly, i think this needs to have info from fol and images
    # fol is a single node
    # images is a length-1 list
    # NEVER MIND WE CAN DO images[0].trunk
    fol.assign_branches(images)
    images = scrape_metadata(images[0])


# cycles_trunk.print_tree()
#dictlist = dictify(cycles_trunk.get_level(3))
#for d in dictlist:
#    print(d['cycle'], '|', d['cycle_code'], '|', d['fname'])

l1 = cycles_trunk.get_level(1)
l2 = cycles_trunk.get_level(2)
l3 = cycles_trunk.get_level(3)
#check_collisions(l1, 'fname')
#check_collisions(l2, 'fname')
#check_collisions(l3, 'fname')
wgets = gen_wget_commands(l3)
for wget in wgets:
    print(wget)
