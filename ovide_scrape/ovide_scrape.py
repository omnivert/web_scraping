import re
from bs4 import BeautifulSoup
from os import walk
import csv

pages = []

# operating now on local files
filenames = []
for _, _, fnames in walk('htmlpages'):
    filenames.extend(fnames)
for fname in filenames:
    #print(fname)
    content = ''
    with open('htmlpages/'+fname) as f:
        content = f.read()
    print('parsing {} ...'.format(fname))
    
    soup = BeautifulSoup(content, 'html.parser')
    img_link = soup.find('a', href=re.compile("[0-9][0-9][0-9][0-9]\.jpg"))
    img_url = img_link['href']
    #print(img_url)

    page_info = soup.find('a', alt=re.compile("Ms O 4"))
    page_num = page_info["title"][10:]
    #print(page_num)

    legend = ' '
    legend_tag = soup.find('div', string=re.compile("Légende"))
    if legend_tag is not None:
        legend = legend_tag.find_next_sibling('div').div.a.string

    pages.append([page_num,img_url,legend])

pages_sorted = sorted(pages, key=lambda t: t[0])

with open('imagemap.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    print('writing csv file...')
    for row in pages_sorted:
        csvwriter.writerow(row)
