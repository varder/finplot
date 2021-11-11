# !/usr/bin/env python3
import math
import socket
import traceback
from operator import itemgetter

import zmq
import time
import json

# from pip._internal.utils.misc import pairwise

import finplot as fplt

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.SUBSCRIBE, b"")
# socket.setsockopt(zmq.PULL, b"")
socket.connect("tcp://localhost:1238")

import pandas as pd
from datetime import datetime

plots = []

def tm(str):
    fmt = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.strptime(str, fmt)


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

        self.ox1, self.ox2, self.ox3, self.ox4 = fplt.create_plot('My Plot', init_zoom_periods=125, maximize=False,
                                                                  rows=4)
        pass

    def Test(self):
        if len(self.Indicators) < 8:
            # pass
            return

        for name, chart in self.Indicators.items():
            if name == "Main":
                self.r1 = True
            elif name == "MACD":
                self.r2 = True
            elif name == "RSI":
                self.r3 = True
            elif name == "BUY":
                self.r4 = True

        if not self.r1 or not self.r2 or not self.r3 or not self.r4 or self.Statistics is None:
            return

        for name, chart in self.Indicators.items():
            if name == "Main":
                for c, ch in chart.items():
                    # self.PlotBars(ch['Name'], self.ox1, ch["Values"])

                    if ch['SeriesType'] == 0:
                        self.PlotLine(ch['Name'], self.ox1, ch["Values"])

                    if ch['SeriesType'] == 2:
                        # df = pd.DataFrame(ch['Values'])
                        # self.PlotLineFromDataFrame(ch['Name'], self.ox1, df.x, df.c)
                        self.PlotBars(ch['Name'], self.ox1, ch["Values"])

            elif name == "MACD":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox2, ch["Values"])
            elif name == "RSI":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox3, ch["Values"])
                fplt.add_band(30, 70, ax=self.ox3)
            elif name == "BUY":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox4, ch["Values"])

        # if self.r1 and self.r2 and self.r3 and self.r4 and self.Statistics is not None:
            # line = fplt.add_line((dates[100], 4.4), (dates[1100], 4.6), color='#9900ff', interactive=True)

        fplt.add_legend(self.Statistics, self.ox1)
        self.PlotOrders(self.ox1)
        fplt.show()

    def PlotOrders(self, ox):

        # db = [{'x': tm(o['Time']), 'y': o['Price']} for o in self.Orders.values() if o['Direction'] == 0]
        # ds = [{'x': tm(o['Time']), 'y': o['Price']} for o in self.Orders.values() if o['Direction'] == 1]
        db = []
        ds = []

        prev_buy = 0
        orders = []
        def getInx(arr, ix):
            pass

        for k, o in self.Orders.items():
            i = int(k)
            if i < 2:
                continue

            if o['Direction'] == 1:
                b = self.Orders[str(i-1)]
                bp = b['Price']
                sp = o['Price']
                bq = b['Quantity']
                sq = o['Quantity']
                btime = tm(b['Time'])
                stime = tm(o['Time'])
                # sum = o['Price'] + self.Orders[k-1]['Price']
                sum = bq + sq
                if sum == 0:
                    orders.append({'b': (btime, bp), 's': (stime, sp)})


            # for i in range(k, 1, -1):
            #     pass



        for ol in orders:
            try:
                line = fplt.add_line(ol['b'], ol['s'], color='#9900ff', interactive=False, ax=ox)
            except Exception as e:
                print(f"Got e PlotOrders exception: {e} ")
                traceback.print_tb(e.__traceback__)


        # for a, b in pairwise(self.Orders):
        # for b, s in zip(db, ds):
        #     try:
        #         line = fplt.add_line((b['x'], b['y']), (s['x'], s['y']), color='#9900ff', interactive=False, ax=ox)
        #     except Exception as e:
        #         print(f"Got e PlotOrders exception: {e} ")
        #         traceback.print_tb(e.__traceback__)

    def PlotBars(self, name, ox, chart):
        try:
            df = pd.DataFrame(chart)
            df = df.rename(columns={'x': 't'})
            del df['y']
            df.set_index('t')
            self.update_plot(df, ox=ox)
        except Exception as e:
            print(f"Got e PlotBars{e} ")
            traceback.print_tb(e.__traceback__)

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

    def PlotLineFromDataFrame(self, name, ox, x, y):
        try:
            # line = frame
            # line.set_index('t')
            fplt.plot(x, y, legend=name, ax=ox)
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
        slow = pd.DataFrame(chart['slow'])
        signal = pd.DataFrame(chart['signal'])
        fast = fast.rename(columns={'x': 't'})
        fast.set_index('t')
        fplt.plot(fast.t, fast.y, legend='Macd', ax=self.ox3)
        fplt.plot(fast.t, slow.y, legend='Macd', ax=self.ox3)
        # fplt.plot(fast.t, signal.y, legend='Macd', ax=self.ox3)

    def Plot2(self, chart):
        df = pd.DataFrame(chart)
        df = df.rename(columns={'x': 't'})
        df.set_index('t')
        fplt.plot(df.t, df.y, legend='RSI', ax=self.ox2)

    def Plot(self, chart):
        df = pd.DataFrame(chart)
        df = df.rename(columns={'x': 't'})
        del df['y']  # ignore status=ok
        df.set_index('t')
        self.update_plot(df, ox=self.ox1)


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

            stat = data['oResults']['Statistics']
            test = f"NetProfit: {stat['Net Profit']}  "
            test += f"WinRate: {stat['Win Rate']}  "
            test += f"AnnualReturn: {stat['Compounding Annual Return']}  "
            test += f"Drawdown: {stat['Drawdown']}  "
            test += f"TotalTrades: {stat['Total Trades']}  "
            test += f"AverageWin: {stat['Average Win']}  "
            test += f"AverageLoss: {stat['Average Loss']}  "
            test += f"PSR: {stat['Probabilistic Sharpe Ratio']}  "
            if stat is not None and len(stat) > 5:
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
        if data["eType"] == "Log":
            return
        elif data["eType"] == "BacktestResult":
            if data.get('oResults') is not None and data['oResults'].get('Orders') is not None:
                self.DisplayOrders(data)
            if data.get('oResults') is not None and data['oResults'].get('Statistics') is not None:
                self.DisplayStatistics(data)
            if data.get('oResults') is not None and data['oResults'].get('Charts') is not None:
                self.DisplayBacktestResults(data)
        elif data['eType'] == 'AlgorithmStatus':
            if data['eStatus'] == 'Completed':
                print("We are completed #########")

    def update_plot(self, df, ox):
        # tdup, tddn = td_sequential(df['c'])

        # df['tdup'] = [('%i' % i if 0 < i < 10 else '') for i in tdup]
        # df['tddn'] = [('%i' % i if 0 < i < 10 else '') for i in tddn]

        db = [{'t': tm(o['Time']), 'h': o['Price'], 'tdup': o['Quantity']} for o in self.Orders.values() if o['Direction'] == 0]
        ds = [{'t': tm(o['Time']), 'l': o['Price'], 'tddn': o['Quantity']} for o in self.Orders.values() if o['Direction'] == 1]
        td_up_labels = pd.DataFrame(db)
        td_dn_labels = pd.DataFrame(ds)

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
            orderbook_plot = fplt.horiz_time_volume(orderbook, candle_width=0, draw_body=10,
                                                    colorfunc=orderbook_colorfunc)
            plots.append(orderbook_plot)
            # use bitmex colors

            # fplt.candle_bull_color = fplt.candle_bear_color = '#000'
            # fplt.volume_bull_color = fplt.volume_bear_color = '#333'
            # fplt.candle_bull_body_color = fplt.volume_bull_body_color = '#fff'

            plots.append(fplt.labels(td_up_labels, color='#009900', ax=ox))
            plots.append(fplt.labels(td_dn_labels, color='#990000', anchor=(0.5, 0), ax=ox))

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
            plots[1].update_data(orderbook)

            plots[2].update_data(td_up_labels)
            plots[3].update_data(td_dn_labels)




print("Start this stuff")
views = Views()
while (True):
    data = socket.recv_multipart()
    size = len(data)
    if size <= 0:
        continue
    try:
        pack = json.loads(data[0].decode("utf-8"))
        views.OnData(pack)
    except BaseException as e:
        print(f"Got e Main: {e} ")
        traceback.print_tb(e.__traceback__)

