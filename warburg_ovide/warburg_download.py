import requests, csv, logging
from bs4 import BeautifulSoup as bsp
from os import walk
from pathlib import Path as pth

#warburg_vpc_url = 'https://iconographic.warburg.sas.ac.uk/vpc/'
#warburg_search_url = warburg_vpc_url + 'VPC_search/'
#ovide_cycles_suffix = 'subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
##cycles_url = 'https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
#cycles_url = warburg_search_url + ovide_cycles_suffix
## if the downloaded html page doesn't exist, save it
# *** MORE OR LESS COVERED IN NEW download_page() METHOD
# **** cycles_fname = 'cycles.html'
# **** ## TODO check for existence of htmlpages dir
# **** cwd = 'htmlpages'
# **** pth('./'+cwd).mkdir(parents=True, exist_ok=True)
# **** htmlpages = []
# **** for _, _, fnames in walk(cwd):
# ****     htmlpages.extend(fnames)
# **** if cycles_fname not in htmlpages:
# ****     page = requests.get(cycles_url)
# ****     with open(cwd+'/'+cycles_fname, 'w') as f:
# ****         logger.debug('writing ' + cwd+'/'+cycles_fname + '...')
# ****         f.write(page.text)
# **** else:
# ****     logger.debug('file '+cwd+'/'+cycles_fname+' already exists')
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

