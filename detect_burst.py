#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import csv
import pybursts
import matplotlib.pyplot as plt

import numpy as np
import statsmodels.api as sm
import types
from statsmodels.tsa.api import VAR
from scipy.signal import lfilter
from statsmodels.tsa.stattools import grangercausalitytests as granger

import itertools

reload(sys)
sys.setdefaultencoding("utf-8")

# config ------------------------------------------------------------------
nof_tags_threshold = 10  # この回数以上にタグ付けを行ったタグのみ解析対象とする
disp_rank = 300          # 利用回数が多い順で、この順位のタグまで解析対象とする
skip_tag_names = []      # このタグ名に一致するタグは解析対象から除外する

kleinberg_event_freq = 1.2
kleinberg_transition_cost = 0.2
kleinberg_plot = False   # バースト系列をグラフ描画するか

granger_max_lag = 1
granger_min_lag = 1
granger_f_test_p_value_threshold = 0.01

silent_mode = False      # 標準出力を抑制するか
# -------------------------------------------------------------------------

def invert_lst(lst):
       col = len(lst[0])
       row = len(lst)
       inv = []
       for i in range(col):
               l = []
               for j in range(row):
                       l.append('')
               inv.append(l)
       for i in range(row):
               for j in range(col):
                       inv[j][i] = lst[i][j]
       return inv

def main():
    # load csv data
    reader = csv.reader(open('./invert_url_list.csv','rb'))
    header = reader.next() # skip header
    tag_times_list = []    # [(tag_name, [-timestamp,...]),...]
    time_max = 0
    for row in reader:
        tag_name = row[0]
        row.pop(0)

        # skip specific tags
        if tag_name in skip_tag_names:
            print("skipped: %s" % (tag_name))
            continue

        # get max time
        _time_max = max(map(lambda x: int(x), row))
        if _time_max > time_max:
            time_max = _time_max

        # set tag_time_list only #tagging > threshold
        if len(row) >= nof_tags_threshold:
            tag_times_list.append((tag_name, row))

    # interpret time
    tag_times_list_new = [] # [(tag_name, [-timestamp,...]),...]
    for tag_times in tag_times_list:
        tag_times_list_new.append((
            tag_times[0],
            map(lambda x: time_max - int(x), tag_times[1])))

    # sort tag_time_list order by #tagging desc
    tag_times_list = sorted(
            tag_times_list_new,
            key=lambda x: len(x[1]), reverse=True)

    # create burst series
    target_series = []
    num_of_tags = len(tag_times_list)
    for loop_counter, tag_times in enumerate(tag_times_list):
        if loop_counter >= disp_rank:
            break

        #if tag_times[0] not in [u'chainer', u'rnn', u'python']:
        #    continue

        # get burst
        [tagname, times] = tag_times
        if not silent_mode:
            print("calculate burst series(%s/%s): %s"
                    % (loop_counter, num_of_tags, tagname))
        burst = pybursts.kleinberg(
                times,
                s=kleinberg_event_freq,
                gamma=kleinberg_transition_cost)
        burst = sorted(burst, key=lambda x: x[0])

        # create burst series
        burst_series = [0 for i in range(0, time_max+1)]
        for elm in burst:
            [burst_level, offset_from, offset_to] = elm
            burst_series[offset_from:offset_to+1] = (
                    [burst_level] * (offset_to - offset_from + 1))

        # store burst series
        target_series.append([tagname] + burst_series)

        # plot
        if kleinberg_plot:
            plt.plot(burst_series, label=tagname)
            plt.legend(loc='upper left')
            plt.xlabel(u'時間（タグ付け系列）')
            plt.ylabel(u'バースト度')
            plt.savefig('./burst_images/rank_%s.png' % (loop_counter))
            plt.clf()

    # granger causality
    all_combi_of_series = list(itertools.combinations(target_series, 2))
    num_of_combis = len(all_combi_of_series)
    ofname = "granger_causality.csv"
    fout = open(ofname,"w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["from_tag","to_tag","p_value", 'lag'])
    for loop_counter, combi_of_series in enumerate(all_combi_of_series):
        if not silent_mode:
            print("calculate granger causality(%s/%s): %s -> %s"
                    % (loop_counter, num_of_combis, combi_of_series[0][0], combi_of_series[1][0]))

        for permu_of_series in list(itertools.permutations(combi_of_series)):
            transpose_target_series = invert_lst(permu_of_series)
            tagnames = transpose_target_series.pop(0)

            # test granger
            try:
                results = granger(transpose_target_series, maxlag=granger_max_lag, verbose=False)
            except:
                print("error occurred.")
                continue

            # evaluate granger
            p_value_min = 1.0
            lag_p_value_min = 0
            for i in range(granger_min_lag, granger_max_lag + 1):
                p_value = results[i][0]['ssr_ftest'][1]
                if p_value_min > p_value:
                    p_value_min = p_value
                    lag_p_value_min = i

            # pass test
            if p_value_min < granger_f_test_p_value_threshold:
                print("%s -> %s (F test p-value:%s at lag=%s)" % (
                    tagnames[0], tagnames[1], p_value_min, lag_p_value_min))
                writer.writerow([tagnames[0], tagnames[1], p_value_min, lag_p_value_min])

                if kleinberg_plot:
                    figpath = './granger_images/granger_%s_%s.png' % (tagnames[0], tagnames[1])
                    plt.clf()
                    plt.xlabel(u'時間（タグ付け系列）')
                    plt.ylabel(u'バースト度')
                    for _burst_series in permu_of_series:
                        plt.plot(_burst_series[1:-1], label=_burst_series[0])
                        plt.legend(loc='upper left')
                        plt.savefig(figpath)
    fout.close()

if __name__ == "__main__":
    main()
