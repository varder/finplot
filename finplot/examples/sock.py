#!/usr/bin/env python3
import math
import socket

import zmq
import time
import json
import finplot as fplt

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.SUBSCRIBE, b"")
# socket.setsockopt(zmq.PULL, b"")
socket.connect("tcp://localhost:1237")

import pandas as pd

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

    # tdup,tddn = td_sequential(df['close'])
    # df['tdup'] = [('%i'%i if 0<i<10 else '') for i in tdup]
    # df['tddn'] = [('%i'%i if 0<i<10 else '') for i in tddn]


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


class Views:
    def __init__(self):
        # self.shown = False
        # self.main = None
        # self.rsi = None
        self.r1 = False
        self.r2 = False
        self.r3 = False
        self.r4 = False

        self.Indicators = {}

        self.ox1, self.ox2, self.ox3, self.ox4  = fplt.create_plot('My Plot AMD', init_zoom_periods=125, maximize=False, rows=4)
        pass

    def Test(self):
        if len(self.Indicators) != 8:
            return

        for name, chart in self.Indicators.items():
            if name == "Main":
                for c, ch in chart.items():
                    self.PlotBars(ch['Name'], self.ox1, ch["Values"])
                self.r1 = True
            elif name == "MACD":
                for c, ch in chart.items():
                    self.PlotLine(ch['Name'], self.ox2, ch["Values"])
                self.r2 = True
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
            else:
                print("")

            if self.r1 and self.r2 and self.r3 and self.r4:
                fplt.show()


    def PlotBars(self, name, ox, chart):
        df = pd.DataFrame(chart)
        df = df.rename(columns={'x': 't'})
        del df['y']
        df.set_index('t')
        update_plot(df, ox=ox)

    def PlotLine(self, name, ox, chart):
        try:
            df = pd.DataFrame(chart)
            line = df.rename(columns={'x': 't'})
            line.set_index('t')
            fplt.plot(line.t, line.y, legend=name, ax=ox)
            print(".")
        except Exception as e:
            print(e)


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

    def DisplayBacktestResults(self, charts):
        if charts is None:
            return
        for c, v in charts.items():
            series = v['Series']
            name = v['Name']
            if name is None or series is None:
                continue
            self.Indicators[name] = series

        self.Test()
        return


    def OnData(self, data):
        # print(data[0])

        if data["eType"] == "Log":
            return
        elif data["eType"] == "BacktestResult":
            charts = data["oResults"]["Charts"]
            if len(charts) > 0:
                self.DisplayBacktestResults(charts)
        elif data['eType'] == 'AlgorithmStatus':
            if data['eStatus'] == 'Completed':
               print("We are completed #########")
            pass


print("Start this stuff")
views = Views()
while (True):
    # print(".")
    data = socket.recv_multipart()
    # print(data)
    size = len(data)
    if size <= 0:
        continue
    try:
        # pack = json.loads(data[0].decode("utf-8"))
        pack = json.loads(data[0].decode("utf-8"))
        # print(pack)
        views.OnData(pack)
    except BaseException as err:
        e = err
        print(f"Got exception: {err}")
        pass

# print(socket.recv_multipart())

# context = zmq.Context()
# socket = context.socket(zmq.PUB)
# # socket.bind("tcp://localhost:1234")
# socket.bind("@tcp://localhost:1234")
#
# time.sleep(0.2)  # wait for socket to be properly bound
#
# print(socket.recv_multipart())


# HOST = '127.0.0.1'  # The server's hostname or IP address
# PORT = 1234        # The port used by the server
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     # s.sendall(b'Hello, world')
#     data = s.recv(1024)
#
# print('Received', repr(data))
