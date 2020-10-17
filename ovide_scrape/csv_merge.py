import csv, re
from bs4 import BeautifulSoup

data = []
with open('imagemap_r3.csv') as csvfile:
    reader = csv.reader(csvfile)
    data = list(reader)

for row in data:
    if 'tail' in row[0]:
        row.append(row[0].replace(' ','_') + '_' + row[1].split('/')[-1])
    else:
        row.append(row[0] + '.jpg')

imgdict = {d[1] : [d[0]]+d[2:] for d in data}
#[print(x, imgdict[x]) for x in imgdict]

urldata = []
with open('urlmap.csv') as csvfile2:
    reader = csv.reader(csvfile2)
    urldata = list(reader)


for url in urldata:
    content = ''
    with open('htmlpages/'+url[0]) as f:
        content = f.read()
    print('parsing {} ...'.format(url[0]))

    soup = BeautifulSoup(content, 'html.parser')
    img_link = soup.find('a', href=re.compile("[0-9][0-9][0-9][0-9]\.jpg"))
    img_url = img_link['href']
    imgdict[img_url] = imgdict[img_url]+[url[1]]

#[print(x, imgdict[x]) for x in imgdict]
full_csv = [[k]+v for k,v in imgdict.items()]

with open('full_data.csv', 'w', newline='') as csvfile3:
    csvwriter = csv.writer(csvfile3, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    print('writing csv file...')
    for row in full_csv:
        csvwriter.writerow(row)
