from bs4 import BeautifulSoup as bsp
# with open('/home/forkk/web_scraping/warburg_ovide/htmlpages/cycles.d/cycle_17071.d/record_94092.html') as f:
with open('/home/forkk/web_scraping/warburg_ovide/htmlpages/cycles.d/cycle_4814.d/record_104295.html') as f:
    content = f.read()

soup = bsp(content, 'html5lib')

def metadata_correct():
    metadata = soup.body.table.find_next_sibling()
    metadata_dict = {}
    cur_key = ''
    for tr in metadata.find_all('tr')[1:]:
        print('- {}'.format(tr))
        if tr.find('span', class_='grey_small') is not None:
            print('    found metadata class: {}'.format(tr.text))
            cur_key = tr.text
            metadata_dict[cur_key] = ''
        else:
            if cur_key != '':
                metadata_dict[cur_key] = metadata_dict[cur_key] + tr.text

def fol_correct():
    tables = soup.body.table.find_next_siblings()
    table = tables[1]
    print(table.content)
    rows = table.find_all('tr')
    fol_all = [x.text for x in rows if 'fol.' in x.text]

    print(fol_all)

fol_correct()
