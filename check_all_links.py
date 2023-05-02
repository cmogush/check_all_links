import sys, csv, time, re, socket, urllib.request, concurrent.futures, queue, os
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request

# CSV reading / setup
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

def setOutput(csv_file):
    filename, ext = os.path.splitext(csv_file)
    outfile = "{}_result{}".format(filename,ext)  # first add the result tag
    if os.path.exists(outfile):  # if result tag already exists, add a number
        outfile = "{}_result(1){}".format(filename,ext)
    if os.path.exists(outfile):  # if number already exists, increment by 1
        filename, ext = os.path.splitext(outfile)
        pattern = r'\(([0-9])*\)'
        result = re.search(pattern, filename)
        if result:
            numPlus = int(result[1]) + 1
            filename = re.sub(pattern, '({})'.format(str(numPlus)), filename)
        outfile = "{}{}".format(filename,ext)
    print("Results will ouput to {}\n".format(outfile))
    return outfile

# Setup global variables
rows = []
# inputs
csv_file = input("Enter full path to csv to be read in: ")
urls, url_column = readCSV(csv_file)
outfile = setOutput(csv_file)
ad_list = readCSV(r".\Helper CSVs\adlist.csv")[0]
# urls, url_column = getUrls(r'C:\Users\Chris\Desktop\Python Scripts\checkAllLinks\CPUniqueDomains_medium.csv') # testing

# Individual URL tests
def pingURL(url):  # old version using urllib
    """pings the given url and, if redirected, returns a redirected URL"""
    redirectedURL = None
    req = urllib.request.Request(url, headers={'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"})
    r = urllib.request.urlopen(req)
    ogURL = req.get_full_url()
    finalURL = r.geturl()
    if ogURL != finalURL and ogURL != finalURL + "/":
        redirectedURL = finalURL
    return redirectedURL  # o  #

def testUrl(url):  # old version using url lib
    """ function that tests the url using several conditions; returns a formatted dictionary list to use as a CSV row """
    socket.setdefaulttimeout(30)
    row = {url_column: url, 'Result': "", 'Details': "", 'UpdatedURL': "", 'Ads Found': ""}

    # setup the url for testing, make note if it had to be reformatted
    urlFormatted = False
    ogURL = url
    if not url == url.strip():
        url = url.strip()
        urlFormatted = True
    if "discoveryeducation" in url:  # format the url if it's discoveryEd
        url = discoveryEd(url)
        urlFormatted = True
    if doubleForwardSlash(url):
        url = doubleForwardSlash(url)
        urlFormatted = True

    # begin testing the url
    try: # test url with no changes
        redirected = pingURL(url)
        row['Result'], row['Details'], row['UpdatedURL'] = formatRow(redirected, ogURL, url, urlFormatted, True)

    except urllib.error.HTTPError as e:  # catch the HTTPError (response code)
        result, https, failed = subTests(url)  # returns either RedirectedURL (as url or None), or error code, or failed
        if failed == 0:  #succesful
            # check for Ads
            adsfound = adCheck(url, ad_list)
            if not https:
                url = re.sub('https','http',url)
            row['Result'], row['Details'], row['UpdatedURL'], row['Ads Found'] = formatRow(result, ogURL, url, True, https, adsfound)
            row['Ads Found'] = adsfound
        else:  # error code
            print("{}/{} {} {} | {}".format(urls.index(ogURL) + 1, len(urls), ogURL, e.code, getErrorDetails(e.code)))
            row['Result'], row['Details'] = e.code, getErrorDetails(e.code)

    except:  # catch all other errors
        result, https, failed = subTests(url)  # returns either RedirectedURL (as url or None), or error code, or failed
        if failed == 0:  # successful
            if not https:
                url = re.sub('https','http',url)
            # check for Ads
            adsfound = adCheck(url, ad_list)
            row['Result'], row['Details'], row['UpdatedURL'], row['Ads Found'] = formatRow(result, ogURL, url, True, https, adsfound)
        elif failed == 1 and result == 'Failed':  # failed
            print("{}/{} {} {}".format(urls.index(ogURL) + 1, len(urls), ogURL, 'Failed'))
            row['Result'], row['Details'] = 'Failed', 'Failed to establish a connection'
        else: # error code
            print("{}/{} {} {} | {}".format(urls.index(ogURL) + 1, len(urls), ogURL, result, getErrorDetails(result)))
            row['Result'], row['Details'] = result, getErrorDetails(result)
    return row

# URL test helper functions
def discoveryEd(url):
    pattern = r'([a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12})'
    if re.search(pattern, url):  # see if an asset ID exists, and reformat link if so
        guideAssetID = re.search(pattern, url)
        return "https://connect.discoveryeducation.com/index.cfm?&cdPartner=BA34-27GQ&cdUser=26DA-9267&guidAssetID={}".format(guideAssetID[1])
    return url

def doubleForwardSlash(url):
    """ replace instances of double forward slashes with single """
    pattern = r'(.*\/\/.*)(\/\/)(.*)'
    if re.search(pattern, url):
        while re.search(pattern, url):  # see if an asset ID exists, and reformat link if so
            result = re.search(pattern, url)
            replacement = result[1] + '/' + result[3]
            url = re.sub(pattern, replacement, url)
    else:
        return False
    return url

def formatRow(redirected, ogURL, url, urlFormatted, https, adsfound):
    """format the row based on the resulting variables"""
    if redirected is None and https and not urlFormatted:  # successful condition
        print("{}/{} {} Success".format(urls.index(ogURL)+1, len(urls), ogURL))
        result = 'Success'
        details = ''
    elif redirected is None and https and urlFormatted:  # successful but original URL needs reformatted
        print("{}/{} {} Bad Syntax | Update URL | {}".format(urls.index(ogURL) + 1, len(urls), ogURL, url))
        result = 'Failed - Bad Syntax'
        details = 'Failed because of capitalization, spacing, or other bad syntax; Successful as reformatted'
        redirected = url
    elif redirected is None:   # successful but original URL needs to be changed from https to http
        print("{}/{} {} Change to http | {}".format(urls.index(ogURL) + 1, len(urls), ogURL, url))
        result = 'Failed - https'
        details = 'Failed with https; Successful as http'
        redirected = url
    else: # successful but URL needs updated to RedirectedURL
        print("{}/{} {} Redirected | Update URL | {}".format(urls.index(ogURL) + 1, len(urls), ogURL, redirected))
        result = 'Redirected'
        details = 'URL should be updated to match Redirected URL'
    return result, details, redirected, adsfound

def getErrorDetails(response):
    """returns the corresponding details for the Error Code"""
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

def subTests(url):
    """ helper function to try a number of different tests, returns 3 params
    (result, https [True/False], failed [0 - success / 1 - failed]) """
    http = re.sub('https','http',url)
    no_caps = url.lower()
    http_no_caps = http.lower()
    failed = 0
    error = None
    https = True

    try:  # http
        return pingURL(http), False, 0
    except urllib.error.HTTPError as e:
        error = e.code
    except:
        failed = 1
    try:  # no capitalization
        return pingURL(no_caps), True, 0
    except urllib.error.HTTPError as e:
        error = e.code
    except:
        failed = 1
    try:  # http and no capitalization
        return pingURL(http_no_caps), False, 0
    except urllib.error.HTTPError as e:
        error = e.code
    except:
        failed = 1

    if error:
        return error, False, 1
    return 'Failed', False, failed

# Process multiple URLs
def testUrls(urls):
    """functions to test a list of urls; returns a list of dictionaries used for writing a CSV"""
    rows = []
    count = 0
    for url in urls:
        print("Testing ", end="")
        count += 1
        row = testUrl(url)
        rows.append(row)
        # if count % 10 == 0:
        #     writeCSV(rows)  # writing to CSV
    return rows

def feed_the_workers(q, urls, spacing):
    """ Simulate outside actors sending in work to do """
    time.sleep(spacing)
    for url in urls:
        q.put(url)
    return "DONE FEEDING"

def testUrlsParallel(urls):
    """ Test a list of urls in parallel; returns a list of dictionaries used for writing a CSV """
    q = queue.Queue()
    count = 0
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=None) as executor:

        # start a future for a thread which sends work in through the queue
        future_to_url = {
            executor.submit(feed_the_workers, q, urls, 0.25): 'FEEDER DONE'}

        while future_to_url:
            # check for status of the futures which are currently working
            done, not_done = concurrent.futures.wait(
                future_to_url, timeout=0.25,
                return_when=concurrent.futures.FIRST_COMPLETED)

            # if there is incoming work, start a new future
            while not q.empty():
                # fetch a url from the queue
                url = q.get()

                # Start the load operation and mark the future with its URL
                future_to_url[executor.submit(testUrl, url)] = url

            # process any completed futures
            for future in done:
                url = future_to_url[future]
                try:
                    row = future.result()
                    if not url == 'FEEDER DONE':
                        global rows # pull in the global variable
                        rows.append(row)
                        # # checkpoint to write to CSV
                        if (urls.index(row[url_column])+1) % 100 == 0: # write every 100 rows
                            tempRows = rows
                            tempRows = sorted(rows, key=lambda i: i[url_column])
                            writeCSV(tempRows)
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    if url == 'FEEDER DONE':
                        print(url)

                # remove the now completed future
                del future_to_url[future]
        rows = sorted(rows, key = lambda i: i[url_column])
    return rows

def errorChecking():
    """ Retry any rows which have failed with the single-process function, testUrls """
    global urls
    global rows
    urls_check = []
    count = 0
    for row in rows:
        if row[url_column] not in urls:  # guards against duplicates
            continue
        if row['Result'] == 'Failed':
            count += 1  # count number to recheck
            urls_check.append(row[url_column])
    urls = urls_check # update the urls list to only those which need checked
    # check the urls
    for row in rows:
        if row[url_column] not in urls: # guards against duplicates
            continue
        if row['Result'] == 'Failed':
            count += 1
            # add to list to retry and remove row from rows
            print("Testing ", end="")
            newRow = testUrl(row[url_column])  # add url to retry
            rows.remove(row)  # replace the old row..
            rows.append(newRow)  # with the new row
        count += 1
        # save progress
        if count % 100 == 0:
            writeCSV(rows)
    rows = sorted(rows, key=lambda i: i[url_column])
    writeCSV(rows)

# CSV writing
def checkRowComplete(row, header):
    if row[list(header)[1]]:  # if row has results already, add it finished list of dictionaries (rows)
        urls.remove(row[list(header)[0]])  # remove header row from urls list
        rows.append({url_column: row[list(header)[0]], 'Result': row[list(header)[1]],
                     'Details': row[list(header)[2]], 'UpdatedURL': row[list(header)[3]]})
        return 1  # add one to the count if row imported
    return 0  # else the count remains the same

def restoreProgress(partial_csv):
    """ Restore the progress from a partially finished CSV output """
    count = 0
    with open(partial_csv, 'r') as csv_f:
        reader = csv.DictReader(csv_f)
        header = reader.__next__() # get the headers
        count += checkRowComplete(header, header)
        # repeat for all remaining rows
        for row in reader:
            count += checkRowComplete(row, header)
    print("{} rows read in from {}".format(count, os.path.basename(partial_csv)))
    time.sleep(1)

#open website and get data
def getSiteData(test_url):
    webUrl = urllib.request.urlopen(test_url)
    data = webUrl.read()
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
    if ads == []:
        return ""
    return ads

def writeCSV(rows):
    """functions to write dictionary list 'rows' to a CSV"""
    keys = [url_column, 'Result', 'Details', 'UpdatedURL', 'Ads Found']
    with open(outfile, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        print ("writing to CSV: {}".format(outfile))
        writer.writeheader()  # will create first line based on keys
        writer.writerows(rows)  # turns the dictionaries into csv

# Main
def main():
    """main method"""
    print("You may restore progress from a partially completed CSV")
    print("Note: columns must match this exact order: URL | Result | Details | UpdatedURL")
    if(input("Restore (y/n): ") == 'y'):
        partial_csv = input("Enter full path to partial csv: ")
        restoreProgress(partial_csv)

    # single process
    # print("Started {}".format(time.ctime()))
    # timer = time.time()
    # rows = testUrls(urls)
    # print("Ended {} | {} seconds elapsed".format(time.ctime(), time.time() - timer))
    # writeCSV(rows)

    # parallel process
    print("--------------------------------------------------")
    print("Start Url-processing {}".format(time.ctime()))
    print("--------------------------------------------------")
    timer = time.time()
    rows = testUrlsParallel(urls)
    writeCSV(rows)
    print("--------------------------------------------------")
    print("Completed Url-processing {} | {} seconds elapsed".format(time.ctime(), time.time() - timer))
    print("--------------------------------------------------")

    # if(input("Perform error checking? (y/n): ") == 'y'):
    print("Start Error-checking {}".format(time.ctime()))
    print("--------------------------------------------------")
    error_timer = time.time()
    errorChecking()
    print("--------------------------------------------------")
    print("Completed Error-checking {} | {} seconds elapsed".format(time.ctime(), time.time() - error_timer))
    print("Total run-time {}".format(time.time() - timer))

if __name__ == "__main__":
    main()
