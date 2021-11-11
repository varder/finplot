# !/usr/bin/env python3
import math
import socket
import traceback

import zmq
import time
import json

from pip._internal.utils.misc import pairwise

import finplot as fplt

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.SUBSCRIBE, b"")
# socket.setsockopt(zmq.PULL, b"")
socket.connect("tcp://localhost:1238")

import pandas as pd
from datetime import datetime

plots = []


def cumcnt_indices(v):
    v[~v] = math.nan
    cumsum = v.cumsum().fillna(method='pad')
    reset = -cumsum[v.isnull()].diff().fillna(cumsum)
    r = v.where(v.notnull(), reset).cumsum().fillna(0.0)
    return r.astype(int)


def td_sequential(close):
    close4 = close.shift(4)
    td = cumcnt_indices(close > close4)
    ts = cumcnt_indices(close < close4)
    return td, ts


def update_plot(df, ox):

    # tdup, tddn = td_sequential(df['c'])
    # df['tdup'] = [('%i' % i if 0 < i < 10 else '') for i in tdup]
    # df['tddn'] = [('%i' % i if 0 < i < 10 else '') for i in tddn]
    # td_up_labels = df['t h tdup'.split()]
    # td_dn_labels = df['t l tddn'.split()]

    global orderbook
    # calc_bollinger_bands(df)
    candlesticks = df['t o c h l'.split()]
    # bollband_hi = df['t bbh'.split()]
    # bollband_lo = df['t bbl'.split()]
    if not plots:  # 0st time
        candlestick_plot = fplt.candlestick_ochl(candlesticks, ax=ox)
        plots.append(candlestick_plot)
        # plots.append(fplt.plot(bollband_hi, color='#3e4ef1'))
        # plots.append(fplt.plot(bollband_lo, color='#3e4ef1'))
        # fplt.fill_between(plots[0], plots[2], color='#9999fa')
        # generate dummy orderbook plot, which we update next time
        x = len(candlesticks) + -1.5
        y = candlesticks.c.iloc[-2]
        orderbook = [[x, [(y, 0)]]]
        orderbook_colorfunc = fplt.horizvol_colorfilter([(-1, 'bull'), (10, 'bear')])
        orderbook_plot = fplt.horiz_time_volume(orderbook, candle_width=0, draw_body=10, colorfunc=orderbook_colorfunc)
        plots.append(orderbook_plot)
        # use bitmex colors

        # fplt.candle_bull_color = fplt.candle_bear_color = '#000'
        # fplt.volume_bull_color = fplt.volume_bear_color = '#333'
        # fplt.candle_bull_body_color = fplt.volume_bull_body_color = '#fff'

        # plots.append(fplt.labels(td_up_labels, color='#009900', ax=ox))
        # plots.append(fplt.labels(td_dn_labels, color='#990000', anchor=(0.5,0), ax=ox))

        candlestick_plot.colors.update(dict(
            bull_shadow='#000',
            bull_frame='#000',
            bull_body='#fff',
            bear_shadow='#000',
            bear_frame='#fff',
            bear_body='#000'))
        orderbook_plot.colors.update(dict(
            bull_frame='#000',
            bull_body='#fff',
            bear_frame='#000',
            bear_body='#000'))
    else:  # update
        plots[-1].update_data(candlesticks)
        # plots[0].update_data(bollband_hi)
        # plots[1].update_data(bollband_lo)
        plots[2].update_data(orderbook)

        # plots[2].update_data(td_up_labels)
        # plots[3].update_data(td_dn_labels)


class Views:
    def __init__(self):
        # self.shown = False
        # self.main = None
        # self.rsi = None
        self.r1 = False
        self.r2 = False
        self.r3 = False
        self.r4 = False
        self.r5 = False

        self.Indicators = {}
        self.Statistics = None
        self.Orders = None

        self.ox1, self.ox2, self.ox3, self.ox4 = fplt.create_plot('My Plot AMD', init_zoom_periods=125, maximize=False,
                                                                  rows=4)
        pass

    def Test(self):
        if len(self.Indicators) < 8:
            # pass
            return

        for name, chart in self.Indicators.items():
            if name == "Main":
                for c, ch in chart.items():
                    self.PlotBars(ch['Name'], self.ox1, ch["Values"])

                    # print(ch['Values'][2]['x'], ch['Values'][2]['c'])
                    # line = fplt.add_line((df['t'], 4.4), (123, 4.6), color='#9900ff', interactive=True, ax=self.ox1)
                    # line = fplt.add_line((ch['Values'][80]['x'], ch['Values'][80]['c']), (ch['Values'][160]['x'], ch['Values'][160]['c']), color='#9900ff', interactive=False, ax=self.ox1)
                self.r1 = True
            elif name == "MACD":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox2, ch["Values"])
                self.r2 = True
            # elif name == "MACD2":
            #     for c, ch in chart.items():
            #         self.PlotLine(ch['Name'], self.ox3, ch["Values"])
            #     self.r5 = True
            elif name == "RSI":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox3, ch["Values"])
                fplt.add_band(30, 70, ax=self.ox3)
                self.r3 = True
            # elif name == "Strategy Equity":
            #     self.PlotLine(chart['Equity']['Name'], self.ox4, chart['Equity']['Values'])
            #     self.PlotLine(chart['Daily Performance']['Name'], self.ox5, chart['Daily Performance']['Values'])
            #     self.r4 = True
            elif name == "BUY":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox4, ch["Values"])
                self.r4 = True

            # elif name == "Strategy Equity":
            # #     # self.PlotLine(chart['Daily Performance']['Name'], self.ox4, chart['Daily Performance']['Values'])
            #     self.PlotHistogram(chart['Daily Performance']['Name'], self.ox4, chart['Daily Performance']['Values'])
            #     self.r4 = True
            else:
                print("")

        if self.r1 and self.r2 and self.r3 and self.r4 and self.Statistics is not None:
            # line = fplt.add_line((dates[100], 4.4), (dates[1100], 4.6), color='#9900ff', interactive=True)

            fplt.add_legend(str(self.Statistics), self.ox1)
            self.PlotOrders(self.ox1)
            fplt.show()
            # if self.r1 and self.r2 and self.r5:
            #     fplt.show()

    def PlotOrders(self, ox):

        def tm(str):
            # return pd.datetime.strptime(str, "%Y/%M/%D %H:%M:%S")
            fmt = '%Y-%m-%dT%H:%M:%SZ' #if len(value) == 20 else '%Y-%m-%dT%H:%M:%S.%fZ'
            return datetime.strptime(str, fmt)
        try:
            for a, b in pairwise(self.Orders):
                line = fplt.add_line((tm(self.Orders[a]['Time']), self.Orders[a]['Price']), (tm(self.Orders[b]['Time']), self.Orders[b]['Price']),
                    color='#9900ff', interactive=False,
                    ax=ox)

        except Exception as e:
            print(f"Got e PlotOrders{e} ")
            traceback.print_tb(e.__traceback__)

    def PlotBars(self, name, ox, chart):
        df = pd.DataFrame(chart)
        df = df.rename(columns={'x': 't'})
        del df['y']
        df.set_index('t')
        update_plot(df, ox=ox)

    def PlotHistogram(self, name, ox, chart):
        try:
            df = pd.DataFrame(chart)
            line = df.rename(columns={'x': 't'})
            line.set_index('t')
            fplt.volume_ocv(line.t, line.y, legend=name, ax=ox)
            print(".")
        except Exception as e:
            print(f"got ex at plot histogram {e}")

    def PlotLine(self, name, ox, chart):
        try:
            df = pd.DataFrame(chart)
            line = df.rename(columns={'x': 't'})
            line.set_index('t')
            fplt.plot(line.t, line.y, legend=name, ax=ox)
            print(".")
        except Exception as e:
            print(f"got ex at plot line {e}")

    def Test2(self):
        if self.rsi is None or self.main is None or len(self.macd) < 1:
            return
        if not self.shown:
            self.PlotMacd(self.macd)
            self.Plot(self.main)
            self.Plot2(self.rsi)
            fplt.show()
            self.shown = True

    def PlotMacd(self, chart):
        fast = pd.DataFrame(chart['fast'])
        slow = pd.DataFrame(chart['fast'])
        signal = pd.DataFrame(chart['signal'])
        fast = fast.rename(columns={'x': 't'})
        fast.set_index('t')
        fplt.plot(fast.t, fast.y, legend='Macd', ax=self.ox3)
        fplt.plot(fast.t, slow.y, legend='Macd', ax=self.ox3)
        # fplt.plot(fast.t, signal.y, legend='Macd', ax=self.ox3)

    def Plot2(self, chart):
        df = pd.DataFrame(chart)
        # df = df.rename(columns={'x': 'time', 'o': 'open', 'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume'})
        df = df.rename(columns={'x': 't'})
        df.set_index('t')
        fplt.plot(df.t, df.y, legend='RSI', ax=self.ox2)

    def Plot(self, chart):
        # print("got chart ..->>>")
        # print(chart)
        df = pd.DataFrame(chart)
        # df = df.rename(columns={'x': 'time', 'o': 'open', 'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume'})
        df = df.rename(columns={'x': 't'})
        del df['y']  # ignore status=ok
        df.set_index('t')
        update_plot(df, ox=self.ox1)


    def DisplayOrders(self, data):
        try:
            orders = data['oResults']['Orders']
            if orders is not None and len(orders) > 0:
                self.Orders = orders
        except Exception as e:
            print(f"Got e DisplayStatistics {e} ")
            traceback.print_tb(e.__traceback__)

    def DisplayStatistics(self, data):
        try:
            if data.get('oResults') is None or data['oResults'].get('Statistics') is None:
                return

            stat = data['oResults']['Statistics']
            test = f"NetProfit: {stat['Net Profit']}  "
            test += f"WinRate: {stat['Win Rate']}  "
            test += f"AnnualReturn: {stat['Compounding Annual Return']}  "
            test += f"Drawdown: {stat['Drawdown']}  "
            test += f"TotalTrades: {stat['Total Trades']}  "
            test += f"AverageWin: {stat['Average Win']}  "
            test += f"AverageLoss: {stat['Average Loss']}  "
            test += f"PSR: {stat['Probabilistic Sharpe Ratio']}  "
            if stat is not None:
                self.Statistics = test
                # self.Test()

            print(f"got statistics {stat}")
        except Exception as e:
            print(f"Got e DisplayStatistics {e} ")
            traceback.print_tb(e.__traceback__)
            pass

    def DisplayBacktestResults(self, data):
        try:
            charts = data["oResults"]["Charts"]
            if charts is None or len(charts) < 1:
                return
            for c, v in charts.items():
                series = v['Series']
                name = v['Name']
                if name is None or series is None:
                    continue
                self.Indicators[name] = series

            self.Test()
        except Exception as e:
            print(f"Got e DisplayStatistics {e} ")
            traceback.print_tb(e.__traceback__)

    def OnData(self, data):
        # print(data[0])

        if data["eType"] == "Log":
            return
        elif data["eType"] == "BacktestResult":
            if data.get('oResults') is not None or data['oResults'].get('Statistics') is not None:
                self.DisplayStatistics(data)
            if data.get('oResults') is not None or data['oResults'].get('Orders') is not None:
                self.DisplayOrders(data)
            if data.get('oResults') is not None or data['oResults'].get('Charts') is not None:
                self.DisplayBacktestResults(data)
        elif data['eType'] == 'AlgorithmStatus':
            if data['eStatus'] == 'Completed':
                print("We are completed #########")


print("Start this stuff")
views = Views()
while (True):
    data = socket.recv_multipart()
    size = len(data)
    if size <= 0:
        continue
    try:
        # pack = json.loads(data[0].decode("utf-8"))
        pack = json.loads(data[0].decode("utf-8"))
        # print(pack)
        views.OnData(pack)
    except BaseException as e:
        print(f"Got e Main: {e} ")
        traceback.print_tb(e.__traceback__)
        pass

