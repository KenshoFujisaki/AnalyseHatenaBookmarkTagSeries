# AnalyseHatenaBookmarkTagSeries

はてなブックマークしたWebページおよびそれにつけたタグを入力とし、タグ付けの傾向を分析します。  
![グレンジャー因果検定通過のタグ付バースト系列ペア（因果：青→緑）](./img/burst.png)
![はてブのタグ付け因果をネットワーク表示（N=50）](./img/granger_small.png)
![はてブのタグ付け因果をネットワーク表示（N=300）](./img/granger_large.png)

## はてなブックマークからの情報取得
1. はてなブックマーク情報取得スクリプトの実行  

    ```shellscript
    python get_tags.py [はてなブックマークID] -D inverted_url_list.csv
    ```
    [注]  
     * 「マイブックマーク」は「公開する」に設定にする必要があります。設定ページは[こちら](http://b.hatena.ne.jp/-/my/config/profile)  
     * 細かい設定はコマンドライン引数で渡すことができます。  
        ```
        python get_tags.py -h
        ```
        ```
        usage: get_tags.py [-h] [-d [DEST_URL_LIST]] [-D [DEST_INVERTED_URL_LIST]]
                           [-f [FEED_MAX]]
                           hatenaID

        This script create the CSV describing web page and tag for specified Hatena
        bookmark user.
        
        positional arguments:
          hatenaID              Hatena Bookmark ID
        
        optional arguments:
          -h, --help            show this help message and exit
          -d [DEST_URL_LIST], --dest-url-list [DEST_URL_LIST]
                                directory path where you want to create output CSV for
                                URL list (default: "./url_list.csv")
          -D [DEST_INVERTED_URL_LIST], --dest-inverted-url-list [DEST_INVERTED_URL_LIST]
                                directory path where you want to create output CSV for
                                inverted URL list (default: "./inverted_url_list.csv")
          -f [FEED_MAX], --feed-max [FEED_MAX]
                                max page for feeding web pages (default: 10000)
        ```


## タグ付け系列に対する因果取得
1. タグ付けのバースト系列取得 ＆ バースト系列に対するグレンジャー因果検定スクリプト実行

    ```shellscript
    python detect_causality.py invert_url_list.csv -o ./granger_causality.csv
    ```
    [備考] 
    * 細かい設定はコマンドライン引数で渡すことができます。  
        ```
        python detect_causality.py -h
        ```
        ```
        usage: detect_causality.py [-h] [-s SKIP_TAGS [SKIP_TAGS ...]]
                                   [-t [TAG_THRESHOLD]] [-r [RANK]]
                                   [-f [KLEINBERG_EVENT_FREQUENCY]]
                                   [-c [KLEINBERG_TRANSITION_COST]]
                                   [-p [KLEINBERG_PLOT]] [-d [KLEINBERG_PLOT_DEST]]
                                   [-g [GRANGER_MIN_LAG]] [-G [GRANGER_MAX_LAG]]
                                   [-F [GRANGER_TEST_THRESHOLD]] [-P [GRANGER_PLOT]]
                                   [-D [GRANGER_PLOT_DEST]] [-o [DEST_CSV]] [--debug]
                                   src_csv
 
        This script calculates the burst series by enumeration Kleinberg burst
        analysis method for each row in the input CSV, a causal relationship between
        the burst series is detected by the Granger causality test , and output to
        CSV.
        
        positional arguments:
          src_csv               directory path where you want to create output CSV for
                                inverted URL list
        
        optional arguments:
          -h, --help            show this help message and exit
          -s SKIP_TAGS [SKIP_TAGS ...], --skip-tags SKIP_TAGS [SKIP_TAGS ...]
                                tags for excluding analysing (default: None)
          -t [TAG_THRESHOLD], --tag-threshold [TAG_THRESHOLD]
                                minimum number of tags for analysing web page
                                (default: 10)
          -r [RANK], --rank [RANK]
                                minimum rank of number of tags for analysing web page
                                (default: 300)
          -f [KLEINBERG_EVENT_FREQUENCY], --kleinberg-event-frequency [KLEINBERG_EVENT_FREQUENCY]
                                the base of the exponential distribution that is used
                                for modeling the event frequencies (default: 1.2)
          -c [KLEINBERG_TRANSITION_COST], --kleinberg-transition-cost [KLEINBERG_TRANSITION_COST]
                                coefficient for the transition costs between states
                                (default: 0.2)
          -p [KLEINBERG_PLOT], --kleinberg-plot [KLEINBERG_PLOT]
                                boolean for plotting the Kleinberg burst series
                                (default: False)
          -d [KLEINBERG_PLOT_DEST], --kleinberg-plot-dest [KLEINBERG_PLOT_DEST]
                                destination directory for plotting the Kleinberg burst
                                series (default: "./burst_images/rank_%s.png")
          -g [GRANGER_MIN_LAG], --granger-min-lag [GRANGER_MIN_LAG]
                                the Granger causality test results are calculated for
                                all lags from this value (default: 1)
          -G [GRANGER_MAX_LAG], --granger-max-lag [GRANGER_MAX_LAG]
                                the Granger causality test results are calculated for
                                all lags up to this value (default: 1)
          -F [GRANGER_TEST_THRESHOLD], --granger-test-threshold [GRANGER_TEST_THRESHOLD]
                                significance level of the F-test for judging the
                                Granger causality (default: 0.01)
          -P [GRANGER_PLOT], --granger-plot [GRANGER_PLOT]
                                boolean for plotting the Kleinberg burst series pair
                                with Granger causality (default: False)
          -D [GRANGER_PLOT_DEST], --granger-plot-dest [GRANGER_PLOT_DEST]
                                destination directory for plotting the Kleinberg burst
                                series pair with Granger causality (default:
                                "./granger_images/granger_%s_%s.png")
          -o [DEST_CSV], --dest-csv [DEST_CSV]
                                directory path where you want to create output CSV for
                                Granger causality (default: "./granger_causality.csv")
          --debug               debug mode if this flag is set (default: False)
        ```
        
## 因果ネットワークの表示
1. Rの実行

    ```shellscript
    R
    ```
2. 因果ネットワークの描画

    ```Rscript
    library(igraph)
    csvdata <- read.csv("./granger_causality.csv", head = T)
    graphdata <- graph.data.frame(csvdata, directed = T)
    tkplot(
      graphdata,
      vertex.label=V(graphdata)$name,
      canvas.width = 1200,
      canvas.height = 700,
      vertex.size = 0,
      edge.width=E(graphdata)$p_value)
    ```

## 付録：偏グレンジャー因果の算出
上では、グレンジャー因果を用いて因果ネットワークを作成しましたが、グレンジャー因果には第三者変数による影響を受けてしまうという考え/問題があります。この問題を解消する方法に、偏相関の考えを応用した偏グレンジャー因果という手法があります。ここでは、その偏グレンジャー因果検定の算出方法を記します。

1. Rの実行

    ```shellscript
    R
    ```
2. 偏グレンジャー因果検定

    ```Rscript
    library(Matrix)
    library(np)
    library(devtools)
    source_url('https://raw.githubusercontent.com/cran/FIAR/master/R/partGranger.R')
    source_url('https://raw.githubusercontent.com/cran/FIAR/master/R/partGranger3.R')

    csvdata <- read.csv("./burst_series.csv", head = F, stringsAsFactors=F)
    trans_csvdata <- tail(t(csvdata), n=-1)
    trans_csvdata_numeric <- apply(trans_csvdata, c(1,2), as.numeric)
    partGranger3(trans_csvdata_numeric, nx=1, ny=1, order=1, bs=10)
    ```

## 参考ページ
* [1] [イベントの時系列分析による因果関係知識の獲得](https://www.jstage.jst.go.jp/article/tjsai/30/1/30_30_12/_pdf)
* [2] [Kleinberg のバースト検知 (列挙型) について](http://cl-www.msi.co.jp/reports/kleinberg-enumerate.html)
* [3] [pybursts 0.1.1](https://pypi.python.org/pypi/pybursts/0.1.1)
* [4] [はてなブックマークエントリー情報取得API](http://developer.hatena.ne.jp/ja/documents/bookmark/apis/getinfo)
* [5] [Granger因果による時系列データの因果推定（因果フェス2015）](http://www.slideshare.net/takashijozaki1/granger2015)
* [6] [【 Python で 時系列分析 / 計量経済分析 】「Grangerの因果性テスト」で、時系列データ どうしの影響関係の方向 を 検定できる方法](http://qiita.com/HirofumiYashima/items/92588b661353b0e1aa5e)
* [7] [はてなブックマーク記事のレコメンドシステムを作成　PythonによるはてなAPIの活用とRによるモデルベースレコメンド](http://overlap.hatenablog.jp/entry/2013/06/30/232200)
