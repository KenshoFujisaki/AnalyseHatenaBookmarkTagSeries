# AnalyseHatenaBookmarkTagSeries

はてなブックマークしたWebページおよびそれにつけたタグを入力とし、タグ付けの傾向を分析します。  
![グレンジャー因果検定通過のタグ付バースト系列ペア（因果：青→緑）](./img/burst.png)
![はてブのタグ付け因果をネットワーク表示（N=50）](./img/granger_small.png)
![はてブのタグ付け因果をネットワーク表示（N=300）](./img/granger_large.png)

## はてなブックマークからの情報取得
1. はてなブックマークIDの変更

    ```shellscript
    vim get_tags.py
    ```
    
    ```python
    user = "ni66ling"    # 各自のはてなブックマークIDに変更する
    ```
2. はてなブックマーク情報取得スクリプトの実行  
[注] 「マイブックマーク」は「公開する」に設定にする必要があります。設定ページは[こちら](http://b.hatena.ne.jp/-/my/config/profile)  

    ```shellscript
    python get_tags.py
    ```

## タグ付け系列に対する因果取得
1. タグ付けのバースト系列取得 ＆ バースト系列に対するグレンジャー因果検定スクリプト実行

    ```shellscript
    python detect_burst.py
    ```
    [備考] スクリプトのconfig値は、下記の通りです。
    * `nof_tags_threshold`：この回数以上にタグ付けを行ったタグのみ解析対象とする
    * `disp_rank`：利用回数が多い順で、この順位のタグまで解析対象とする
    * `skip_tag_names`：このタグ名に一致するタグは解析対象から除外する
    * `kleinberg_plot`：バースト系列をグラフ描画するか
    * `silent_mode`：標準出力を抑制するか

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

## 参考ページ
* [1] [イベントの時系列分析による因果関係知識の獲得](https://www.jstage.jst.go.jp/article/tjsai/30/1/30_30_12/_pdf)
* [2] [Kleinberg のバースト検知 (列挙型) について](http://cl-www.msi.co.jp/reports/kleinberg-enumerate.html)
* [3] [pybursts 0.1.1](https://pypi.python.org/pypi/pybursts/0.1.1)
* [4] [はてなブックマークエントリー情報取得API](http://developer.hatena.ne.jp/ja/documents/bookmark/apis/getinfo)
* [5] [Granger因果による時系列データの因果推定（因果フェス2015）](http://www.slideshare.net/takashijozaki1/granger2015)
* [6] [【 Python で 時系列分析 / 計量経済分析 】「Grangerの因果性テスト」で、時系列データ どうしの影響関係の方向 を 検定できる方法](http://qiita.com/HirofumiYashima/items/92588b661353b0e1aa5e)
* [7] [はてなブックマーク記事のレコメンドシステムを作成　PythonによるはてなAPIの活用とRによるモデルベースレコメンド](http://overlap.hatenablog.jp/entry/2013/06/30/232200)
