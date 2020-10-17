import requests, csv

url = "https://rnbi.rouen.fr/fr/notice/ovide-moralis%C3%A9"

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
