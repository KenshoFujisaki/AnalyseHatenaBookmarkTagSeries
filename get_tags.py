#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,re,time
import csv
import urllib2
import json
import feedparser
import traceback

reload(sys)
sys.setdefaultencoding("utf-8")

# config ------------------------------------------------------------------
user = "ni66ling"       # はてなuser_id
feed_max = 10000        # ブックマーク最新取得上限数
# -------------------------------------------------------------------------

def main():
    # Web情報取得の準備
    opener = urllib2.build_opener()

    # はてなブックマークのfeed情報の取得
    print("get bookmarks of %s:" % (user))
    url_list = []        # urlリスト
    invert_url_list = {} # 転置url(tagから見たurlのid)
    id = 0
    feed_interval = 20
    for i in range(0,feed_max,feed_interval):
        feed_url = "http://b.hatena.ne.jp/" \
                + user + "/rss?of=" + str(i) # はてなAPIに渡すクエリの作成
        try:
            response = opener.open(feed_url) # urlオープン
        except:
            continue
        content = response.read() # feed情報の取得
        feed = feedparser.parse(content) # feedパーサを用いてfeedを解析
        # entriesがない場合break
        if feed["entries"] == []:
            break
        # urlリストの作成
        for e in feed["entries"]:
            try:
                print("%d: %s" % (id, e["title"]))
                # 転置url作成
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
                # urlリスト作成
                url_list.append([
                    id,
                    e["link"],
                    user,
                    e["hatena_bookmarkcount"],
                    re.sub("[,\"]","",e["title"])
                ]) # url_listの作成（titleのカンマとダブルクォーテーションを置換）
                id += 1
            except:
                print(traceback.format_exc())
                pass
        time.sleep(0.05) # アクセス速度の制御

    # urlリストをCSV出力
    ofname = "url_list.csv"
    fout = open(ofname,"w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["id","url","user","count","title"])
    for t in url_list:
        writer.writerow(t)
    fout.close()

    # 転置urlをCSV出力
    ofname = "invert_url_list.csv"
    fout = open(ofname,"w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["tag","url_id,..."])
    for tag, ids in invert_url_list.items():
        writer.writerow([tag] + ids)
    fout.close()

if __name__ == "__main__":
    main()

