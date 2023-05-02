# check_all_links
Built for Python interpreter 3.8

Script to check all urls from a list, and return their error codes and/or redirected pages

If processing a long list, it's best if run from debugger in PyCharm, so as to be able to pause the script if necessary.

When matching result to original list in Excel, VLOOKUP will not work for values over 255 chars. In this instance, you should use: 
=INDEX([column_to_return],MATCH(TRUE,INDEX([column_with_urls]=[cell_with_url],0),0))

--

In Helper CSVs, adlist.csv will be used to check against if a website has ads