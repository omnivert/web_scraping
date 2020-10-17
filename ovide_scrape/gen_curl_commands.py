import csv

with open('imagemap.csv') as csvfile:
    reader = csv.reader(csvfile)
    data = list(reader)

[print('curl {} --output images/{}.jpg --silent'.format(d[1],d[0].replace(' ','_'))) for d in data]
