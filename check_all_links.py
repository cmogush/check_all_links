import sys
import urllib.request
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request
import socket
import csv
import msvcrt
import time
import re

answer = None

# def get_url_nofollow(url):
#     try:
#         response = urllib.urlopen(url)
#         code = response.getcode()
#         return code
#     except urllib2.HTTPError as e:
#         return e.code
#     except:
#         return 0

def getErrorDetails(response):
    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this server.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
                                               'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }
    if response in responses:
        return responses[response]
    return ""

def pingURL(url):
    redirectedURL = None
    req = urllib.request.Request(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"})
    r = urllib.request.urlopen(req)
    ogURL = req.get_full_url()
    finalURL = r.geturl()
    if ogURL != finalURL:
        redirectedURL = finalURL
    return redirectedURL

def redirectedResult(redirected):
    if redirected is None:
        print('Change to Http')
        result = 'Https Failed'
        details = 'Change to Http'
    else:
        print('Redirected | Change URL to {}'.format(redirected))
        result = 'Redirected'
        details = 'Change URL to {}'.format(redirected)
    return result, details, redirected

def testUrl(url):
    socket.setdefaulttimeout(30)
    row = {'UNIQUE_DOMAINS': url, 'Result': "", 'Details': "", 'Redirected': ""}
    print("{} ".format(url), end="")
    try:
        redirected = pingURL(url)
        row['Result'], row['Details'], row['Redirected'] = redirectedResult(redirected)
    except urllib.error.HTTPError as e:
        url = re.sub('https','http',url)
        try:
            redirected = pingURL(url)
            row['Result'], row['Details'], row['Redirected'] = redirectedResult(redirected)
        except:
            print(e.code)
            row['Result'] = e.code
            row['Details'] = getErrorDetails(e.code)
    except:
        url = re.sub('https', 'http', url)
        try:
            redirected = pingURL(url)
            row['Result'], row['Details'], row['Redirected'] = redirectedResult(redirected)
        except:
            print('Failed')
            row['Result'] = 'Failed to connect'

def testUrls(urls):
    rows = []
    count = 0
    for url in urls:
        count+=1
        print("{}/{} : ".format(count, len(urls)), end="")
        row = testUrl(url)
        rows.append(row)
        if count % 50 == 0:
            print("sleeping 5 seconds...opportunity to pause")
            time.sleep(5)
        if count % 500 == 0:
            writeCSV(rows) # writing to CSV
    return rows

def getUrls(csvFile):
    urlList = []
    with open(csvFile, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        for row in reader:
            urlList.append(row['UNIQUE_DOMAINS'])
    return urlList

def writeCSV(rows):
    keys = ['UNIQUE_DOMAINS', 'Result', 'Details']
    with open('CPUniqueDomains_result.csv', 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        writer.writeheader()  # will create first line based on keys
        writer.writerows(rows)  # turns the dictionaries into csv

def main():
    # urls = getUrls(r'C:\Users\Chris\Desktop\Python Scripts\eswLinkCheck\CPUniqueDomains.csv')
    # rows = testUrls(urls)
    # writeCSV(rows)
    testUrl("https://bookbuilder.cast.org")
    #
    # for line in sys.stdin.readlines():
    #     line = line.strip()
    #     if line not in urls:
    #         sys.stderr.write("+ checking URL: %s\n" % line)
    #         urls[line] = {'code': get_url_nofollow(line), 'count': 1}
    #         sys.stderr.write("++ %s\n" % str(urls[line]))
    #     else:
    #         urls[line]['count'] = urls[line]['count'] + 1
    #
    # for url in urls:
    #     if urls[url]['code'] != 200:
    #         print("%d\t%d\t%s" % (urls[url]['count'], urls[url]['code'], url))

if __name__ == "__main__":
    main()