import sys
import fileinput
from datetime import datetime
import json
import csv

"""
Gets broken links from url_database.csv and fetches corresponding metadata from 
od-do-canada.jsonl.
Gets content-type of active links and compares to format of metadata.

Arguments:
fileinput - metadata file to be read ('od-do-canada.jsonl')
url_database - url_database report generated by url_database.py

Output:
broken_links_report.csv
incorrect_file_types_report.csv
"""

broken_links={}
url_database=sys.argv[2]
file_types={}
#Read url_database and put broken links in dict with url as key
file=open(url_database, "r")
reader = csv.reader(file)
#skip head
next(reader)
for line in reader:
    url=line[0]
    date=line[1]
    response=line[2]
    content_type=line[3].encode('utf-8')
    content_length=line[4].encode('utf-8')
    if response == 'not-found':
        broken_links[url]=[date,response]
    else:
        if '/' in content_type:
            content_type = (((content_type.split(';'))[0]).split('/'))[1]
        if content_type != 'not-found':
            file_types[url]=[date,content_type,content_length]
file.close()

#For each resource in each dataset, check if url is in broken links of url_database
#Get metadata
print("Matching URLs with Metadata")
broken_links_data=[]
file_type_data=[]
broken_links_flag=0
file_type_flag=0
for dataset in fileinput.input():
    line = json.loads(dataset,'utf-8')
    resources = line["resources"]
    for l in range(len(resources)):
        file_url = resources[l]["url"].encode('utf-8')
        if file_url in broken_links:
            data = broken_links.pop(file_url)
            broken_links_data.append([file_url,data[0],data[1],
                                line["organization"]["title"].encode('utf-8'),line["title"].encode('utf-8'),line["id"]])
            if len(broken_links)==0:
                broken_links_flag=1
            continue;
        if file_url in file_types:
            data = file_types.pop(file_url)
            if resources[l]["format"].lower() != data[1]:
                file_type_data.append([file_url,data[0],line["organization"]["title"].encode('utf-8'),
                                       line["title"].encode('utf-8'),line["id"],
                                       data[1],resources[l]["format"].lower(),data[2]])
                if len(file_types) == 0:
                    file_type_flag = 1
                continue;
    if broken_links_flag==1 and file_type_flag==1:
        #stop searching when all broken links and incorrect filetypes are found
        break;


print("Exporting to csv...")
#Export tp CSV
with open('broken_links_report.csv', "w") as f:
    writer = csv.writer(f)
    writer.writerow(("url", "date","response","organization","title","uuid"))
    for row in broken_links_data:
        writer.writerow(row)
f.close()

with open('incorrect_file_types_report.csv', "w") as f:
    writer = csv.writer(f)
    writer.writerow(("url", "date","organization","title","uuid",
                     "found_file_type","metadata_file_type","found_content_length"))
    for row in file_type_data:
        writer.writerow(row)
f.close()
print("Done.")
