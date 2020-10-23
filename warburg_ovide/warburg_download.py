import requests, csv
from bs4 import BeautifulSoup as bsp
from os import walk

###### DOWNLOAD ALL REQUIRED HTML PAGES ######

cycles_url = 'https://iconographic.warburg.sas.ac.uk/vpc/VPC_search/subcats.php?cat_1=8&cat_2=16&cat_3=1524&cat_4=2079'
# if the downloaded html page doesn't exist, save it
cycles_fname = 'cycles.html'
## TODO check for existence of htmlpages dir
htmlpages = []
cwd = 'htmlpages'
for _, _, fnames in walk(cwd):
    htmlpages.extend(fnames)
if cycles_fname not in htmlpages:
    page = requests.get(cycles_url)
    with open(cwd+'/'+cycles_fname, 'w') as f:
        print('writing ' + cycles_fname + '...')
        f.write(page.text)
else:
    print('file '+cwd+'/'+cycles_fname+' already exists')
    

'''
urls = [url + '-{}'.format(x) for x in range(1312)]
urls = [url] + urls

urlmap = []

# save all page info locally
for i, u in enumerate(urls):
    page = requests.get(u)
    fname = 'url{}.html'.format(i)
    with open('htmlpages/'+fname, 'w') as f:
        print('writing ' + fname + '...')
        f.write(page.text)
    urlmap.append([fname, u])

with open('urlmap.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    print('writing csv file...')
    for row in urlmap:
        csvwriter.writerow(row) 

print('done')
'''
