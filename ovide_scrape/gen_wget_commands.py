import csv

with open('imagemap_r3.csv') as csvfile:
    reader = csv.reader(csvfile)
    data = list(reader)

for row in data:
    if 'tail' in row[0]:
        row[0] = row[0] + ' ' + row[1].split('/')[-1][:-4]

[print('wget -q -O images/{}.jpg {}'.format(d[0].replace(' ','_'),d[1])) for d in data]
