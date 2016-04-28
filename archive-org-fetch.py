#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Paul Sladen, 28 April 2016, Hereby placed in the Public Domain.

Download old versions of files from Archive.org and
save the files with the original modification timestamp
based on Archive.Org's headers.

http://web.archive.org/web/20151020054014/.../foo.jar

The headers of interest are:
X-Archive-Orig-last-modified: Wed, 01 Apr 2015 08:50:17 GMT

and for the recursion:

Link: … <http://web.archive.org/web/20130821184603/.../foo.jar>; rel="prev memento"; datetime="Wed, 21 Aug 2013 18:46:03 GMT"
"""
import sys
import urllib
import urllib2
import urlparse
import rfc822
import time
import os
import datetime
import errno

def fetch(url, dry_run=False):

    request = urllib2.Request(url)
    request.get_method = lambda: 'HEAD'
    conn = urllib2.urlopen(request)

    # Parse out Last-Modified date in a reliable way
    def get_seconds(headers, modified='Last-Modified'):
        date_tuple = headers.getdate_tz(modified)
        epoch_seconds = rfc822.mktime_tz(date_tuple)
        return epoch_seconds

    def progress_ticker(blocks, blocksize, total):
        BACKSPACE = '\x08'
        percentage = "{0:6.2f}%".format(min(100.0,blocks*blocksize*100.0/total))
        sys.stdout.write(BACKSPACE * len(percentage) + percentage)

    # single-level mkdir -p functionality
    def mkdir_parents(directory):
        try: os.mkdir(directory)
        except OSError as e:
            if os.path.isdir(directory) and e.errno == errno.EEXIST: pass
            else: raise

    seconds = get_seconds(conn.headers, 'X-Archive-Orig-last-modified')
    #print conn.headers['X-Archive-Orig-last-modified']
    directory = time.strftime('%Y%m%d-%H%M%S', time.gmtime(seconds))
    if not dry_run:
        mkdir_parents(directory)

    path = urlparse.urlparse(url).path
    filename = os.path.basename(path)
    base, ext = os.path.splitext(filename)
    destination = "%s/%s%s" % (directory, base, ext)

    if not dry_run:
        local_filename, headers = urllib.urlretrieve(url, destination, progress_ticker)
        os.utime(local_filename, (seconds,) * 2)
        os.utime(directory, (seconds,) * 2)

    try:
        # Mark Nottingham
        # https://gist.githubusercontent.com/mnot/210535/raw/1755bb24a4f8796d55c280f1c50d0910f5522fb2/link_header.py
        import link_header

        links = link_header.parse_link_value(conn.headers['Link'])
        for k,v in links.items():
            if v.has_key('rel') and 'prev memento' in v['rel']:
                sys.stdout.write('\n%10s %s\r' % ('', k))
                fetch(url=k, dry_run=dry_run)
    except:
        raise

def main():
    fetch(sys.argv[1], dry_run=False)
    print

if __name__=='__main__':
    main()
