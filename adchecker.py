import sys, csv, time, re, socket, urllib.request, concurrent.futures, queue, os
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request

# test_url = "http://en.wikipedia.org/wiki/Gabriel_Garcia_Marquez"
# test_url2 = "http://classroom.synonym.com/main-political-differences-between-stalin-trotsky-8948.html"
test_url3 = "https://123teachme.com/"

def readCSV(csvFile):
    """ Extracts urls from a CSV file; returns results as a list"""
    urlList = []
    with open(csvFile, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        headers = reader.__next__()  # get first row
        url_header = list(headers)[0]  # get headers
        urlList.append(headers[url_header])  # append header row
        for row in reader:
            urlList.append(row[url_header])
    return urlList, url_header

#open website and get data
def getSiteData(test_url):
    webUrl = urllib.request.urlopen(test_url)
    data = webUrl.read()
    print(data)
    return str(data)

#scan for websites from the adlist.csv on the landing page
def adCheck(test_url, ad_list):
    ads = []
    data = getSiteData(test_url)
    pattern = r"[ftp|http]{3,4}[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    urls = re.findall(pattern, data)
    print(urls)
    for ad_site in ad_list:
        if re.search(ad_site, data):
            ads.append(ad_site)
    print(ads)
    return ads


ad_list = readCSV(r".\Helper CSVs\adlist.csv")[0]
# adCheck(test_url2, ad_list)
# adCheck(test_url2, ad_list)
adCheck(test_url3, ad_list)