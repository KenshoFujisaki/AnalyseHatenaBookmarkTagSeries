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
import argparse
import traceback

reload(sys)
sys.setdefaultencoding("utf-8")

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


def load_csv(input_filepath, skip_tag_names, nof_tags_threshold):
    reader = csv.reader(open(input_filepath,'rb'))
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

    return tag_times_list, time_max


def create_burst_series(tag_times_list, time_max, disp_rank, is_plot, plot_dest, \
        kleinberg_event_freq, kleinberg_transition_cost,  debug_mode):
    target_series = []
    num_of_tags = len(tag_times_list)
    for loop_counter, tag_times in enumerate(tag_times_list):
        if loop_counter >= disp_rank:
            break

        # get burst
        [tagname, times] = tag_times
        if debug_mode:
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
        if is_plot:
            plt.plot(burst_series, label=tagname)
            plt.legend(loc='upper left')
            plt.xlabel(u'時間（タグ付け系列）')
            plt.ylabel(u'バースト度')
            plt.savefig(plot_dest % (loop_counter))
            plt.clf()

    return target_series


def test_granger_causality(target_series, dest_path, granger_max_lag, granger_min_lag, \
        granger_f_test_p_value_threshold, is_plot, plot_dest, debug_mode):
    all_combi_of_series = list(itertools.combinations(target_series, 2))
    num_of_combis = len(all_combi_of_series)
    ofname = dest_path
    fout = open(ofname,"w")
    writer = csv.writer(fout, delimiter=",")
    writer.writerow(["from_tag", "to_tag", "p_value", 'lag'])
    for loop_counter, combi_of_series in enumerate(all_combi_of_series):
        if debug_mode:
            print("calculate granger causality(%s/%s): %s -> %s"
                    % (loop_counter, num_of_combis, combi_of_series[0][0], combi_of_series[1][0]))

        for permu_of_series in list(itertools.permutations(combi_of_series)):
            transpose_target_series = invert_lst(permu_of_series)
            tagnames = transpose_target_series.pop(0)

            # test granger
            try:
                results = granger(transpose_target_series, maxlag=granger_max_lag, verbose=False)
            except :
                if debug_mode:
                    print("error occurred at (%s, %s) and continued.\n" % (tagnames[0], tagnames[1]))
                    #print(traceback.format_exc())
                    #try:
                    #    results = granger(transpose_target_series, maxlag=granger_max_lag, verbose=True)
                    #except:
                    #pass
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
                if debug_mode:
                    print("%s -> %s (F test p-value:%s at lag=%s)" % (
                        tagnames[0], tagnames[1], p_value_min, lag_p_value_min))
                writer.writerow([tagnames[0], tagnames[1], p_value_min, lag_p_value_min])

                if is_plot:
                    figpath = plot_dest % (tagnames[0], tagnames[1])
                    plt.clf()
                    plt.xlabel(u'時間（タグ付け系列）')
                    plt.ylabel(u'バースト度')
                    for _burst_series in permu_of_series:
                        plt.plot(_burst_series[1:-1], label=_burst_series[0])
                        plt.legend(loc='upper left')
                        plt.savefig(figpath)
    fout.close()


def parse_args():
    parser = argparse.ArgumentParser(description=(\
            'This script calculates the burst series by enumeration ' +\
            'Kleinberg burst analysis method for each row in the input ' +\
            'CSV, a causal relationship between the burst series is ' +\
            'detected by the Granger causality test , and output to CSV.'))
    parser.add_argument(\
            'src_csv', \
            action='store', \
            nargs=None, \
            const=None, \
            default=None, \
            type=str, \
            choices=None, \
            help='directory path where you want to create output CSV for inverted URL list', \
            metavar=None)

    # setting for input
    parser.add_argument(\
            '-s', '--skip-tags', \
            action='store', \
            nargs='+', \
            const=None, \
            default=[], \
            type=str, \
            choices=None, \
            help='tags for excluding analysing (default: None)', \
            metavar=None)
    parser.add_argument(\
            '-t', '--tag-threshold', \
            action='store', \
            nargs='?', \
            const=None, \
            default=10, \
            type=int, \
            choices=None, \
            help='minimum number of tags for analysing web page (default: 10)', \
            metavar=None)
    parser.add_argument(\
            '-r', '--rank', \
            action='store', \
            nargs='?', \
            const=None, \
            default=300, \
            type=int, \
            choices=None, \
            help='minimum rank of number of tags for analysing web page (default: 300)', \
            metavar=None)

    # setting for Kleinberg burst analysis
    parser.add_argument(\
            '-f', '--kleinberg-event-frequency', \
            action='store', \
            nargs='?', \
            const=None, \
            default=1.2, \
            type=float, \
            choices=None, \
            help='the base of the exponential distribution that is used for modeling the event frequencies (default: 1.2)', \
            metavar=None)
    parser.add_argument(\
            '-c', '--kleinberg-transition-cost', \
            action='store', \
            nargs='?', \
            const=None, \
            default=0.2, \
            type=float, \
            choices=None, \
            help='coefficient for the transition costs between states (default: 0.2)', \
            metavar=None)
    parser.add_argument(\
            '-p', '--kleinberg-plot', \
            action='store', \
            nargs='?', \
            const=None, \
            default=False, \
            type=bool, \
            choices=None, \
            help='boolean for plotting the Kleinberg burst series (default: False)', \
            metavar=None)
    parser.add_argument(\
            '-d', '--kleinberg-plot-dest', \
            action='store', \
            nargs='?', \
            const=None, \
            default='./burst_images/rank_%s.png', \
            type=str, \
            choices=None, \
            help='destination directory for plotting the Kleinberg burst series (default: "./burst_images/rank_%%s.png")', \
            metavar=None)

    # setting for Granger causality analysis
    parser.add_argument(\
            '-g', '--granger-min-lag', \
            action='store', \
            nargs='?', \
            const=None, \
            default=1, \
            type=int, \
            choices=None, \
            help='the Granger causality test results are calculated for all lags from this value (default: 1)', \
            metavar=None)
    parser.add_argument(\
            '-G', '--granger-max-lag', \
            action='store', \
            nargs='?', \
            const=None, \
            default=1, \
            type=int, \
            choices=None, \
            help='the Granger causality test results are calculated for all lags up to this value (default: 1)', \
            metavar=None)
    parser.add_argument(\
            '-F', '--granger-test-threshold', \
            action='store', \
            nargs='?', \
            const=None, \
            default=0.01, \
            type=float, \
            choices=None, \
            help='significance level of the F-test for judging the Granger causality (default: 0.01)', \
            metavar=None)
    parser.add_argument(\
            '-P', '--granger-plot', \
            action='store', \
            nargs='?', \
            const=None, \
            default=False, \
            type=bool, \
            choices=None, \
            help='boolean for plotting the Kleinberg burst series pair with Granger causality (default: False)', \
            metavar=None)
    parser.add_argument(\
            '-D', '--granger-plot-dest', \
            action='store', \
            nargs='?', \
            const=None, \
            default='./granger_images/granger_%s_%s.png', \
            type=str, \
            choices=None, \
            help='destination directory for plotting the Kleinberg burst series pair with Granger causality (default: "./granger_images/granger_%%s_%%s.png")', \
            metavar=None)

    # setting for output
    parser.add_argument(\
            '-o', '--dest-csv', \
            action='store', \
            nargs='?', \
            const=None, \
            default='./granger_causality.csv', \
            type=str, \
            choices=None, \
            help='directory path where you want to create output CSV for Granger causality (default: "./granger_causality.csv")', \
            metavar=None)

    # setting for executing
    parser.add_argument(\
            '--debug', \
            action='store_true', \
            default=False, \
            help='debug mode if this flag is set (default: False)')

    # parse args
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # parse args
    args = parse_args()

    # load csv
    print('loading csv file (%s)...' % (args.src_csv))
    tag_times_list, time_max = load_csv(\
            args.src_csv, \
            args.skip_tags, \
            args.tag_threshold)

    # create Kleinberg burst series
    print('\ncreate Kleinberg burst series...')
    target_series = create_burst_series(\
            tag_times_list, \
            time_max, \
            args.rank, \
            args.kleinberg_plot, \
            args.kleinberg_plot_dest, \
            args.kleinberg_event_frequency, \
            args.kleinberg_transition_cost, \
            args.debug)

    # Granger causality test
    print('\nexecute Granger causality test...')
    test_granger_causality(\
            target_series, \
            args.dest_csv, \
            args.granger_max_lag, \
            args.granger_min_lag, \
            args.granger_test_threshold, \
            args.granger_plot, \
            args.granger_plot_dest, \
            args.debug)

    # inform successfully process completed.
    print((\
            '\nprocess is successfully completed. check following files.' +\
            '\n    Granger causality list: %s'\
          ) % (args.dest_csv))

