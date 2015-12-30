#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,re,time
import csv
import urllib2
import json
import feedparser
import traceback
import argparse

reload(sys)
sys.setdefaultencoding("utf-8")

def main(hatena_id, feed_max, dest_urls, dest_inverted_urls):
    # prepare getting web info.
    opener = urllib2.build_opener()

    # get the feed info. about Hatena bookmark.
    print("get bookmarks of %s:" % (hatena_id))
    url_list = []        # url list
    invert_url_list = {} # inverted url list (tag: [url_id_1, url_id_2,...])
    id = 0
    feed_interval = 20
    for i in range(0, feed_max, feed_interval):
        feed_url = "http://b.hatena.ne.jp/" \
                + hatena_id + "/rss?of=" + str(i) # create the query for Hatena API.
        try:
            response = opener.open(feed_url)
        except:
            continue
        content = response.read()
        feed = feedparser.parse(content)
        if feed["entries"] == []:
            break

        # create url list.
        for e in feed["entries"]:
            try:
                print("%d: %s" % (id, e["title"]))
                # create inverted url list.
                if not (e.has_key("tags") and
                        e.has_key("link") and
                        e.has_key("hatena_bookmarkcount")):
                    continue
                for tag in map(lambda x: x["term"], e["tags"]):
                    normalized_tag = re.sub("[ -]", "", tag).lower()
                    if normalized_tag not in invert_url_list:
                        invert_url_list[normalized_tag] = [id]
                    else:
                        if invert_url_list[normalized_tag][-1] != id:
                            invert_url_list[normalized_tag].append(id)
                # append url list.
                url_list.append([
                    id,
                    e["link"],
                    hatena_id,
                    e["hatena_bookmarkcount"],
                    re.sub("[,\"]","",e["title"])
                ])
                id += 1
            except:
                print(traceback.format_exc())
                pass
        time.sleep(0.05)

    # output url list with CSV.
    ofname = dest_urls
    fout = open(ofname,"w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["id","url","user","count","title"])
    for t in url_list:
        writer.writerow(t)
    fout.close()

    # output inverted url list with CSV.
    ofname = dest_inverted_urls
    fout = open(ofname,"w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["tag","url_id,..."])
    for tag, ids in invert_url_list.items():
        writer.writerow([tag] + ids)
    fout.close()

    # inform successfully process completed.
    print((\
            '\nprocess for %s is successfully completed. check following files.' +\
            '\n    URL list:          %s' +\
            '\n    inverted URL list: %s'\
          ) % (hatena_id, dest_urls, dest_inverted_urls))

if __name__ == "__main__":
    # parse args
    parser = argparse.ArgumentParser(\
            description='This script create the CSV describing web page and tag for specified Hatena bookmark user.')
    parser.add_argument(\
            'hatenaID', \
            action='store', \
            nargs=None, \
            const=None, \
            default=None, \
            type=str, \
            choices=None, \
            help='Hatena Bookmark ID', \
            metavar=None)
    parser.add_argument(\
            '-d', '--dest-url-list', \
            action='store', \
            nargs='?', \
            const=None, \
            default='./url_list.csv', \
            type=str, \
            choices=None, \
            help='directory path where you want to create output CSV for URL list (default: "./url_list.csv")', \
            metavar=None)
    parser.add_argument(\
            '-D', '--dest-inverted-url-list', \
            action='store', \
            nargs='?', \
            const=None, \
            default='./inverted_url_list.csv', \
            type=str, \
            choices=None, \
            help='directory path where you want to create output CSV for inverted URL list (default: "./inverted_url_list.csv")', \
            metavar=None)
    parser.add_argument(\
            '-f', '--feed-max', \
            action='store', \
            nargs='?', \
            const=None, \
            default=10000, \
            type=int, \
            choices=None, \
            help='max page for feeding web pages (default: 10000)', \
            metavar=None)
    args = parser.parse_args()

    # execute main
    main(args.hatenaID, args.feed_max, args.dest_url_list, args.dest_inverted_url_list)

