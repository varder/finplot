#!/usr/bin/env python3

import socket

import zmq
import time
import json
import finplot as fplt
import pandas as pd

plots = []


ax0 = fplt.create_plot('My Plot AMD', init_zoom_periods=75, maximize=False, rows=2)
# ax,ax2 = fplt.create_plot('S&P 500 MACD', rows=2)

fplt.show()


def update_plot(df):
    global orderbook
    # calc_bollinger_bands(df)
    candlesticks = df['t o c h l'.split()]
    # bollband_hi = df['t bbh'.split()]
    # bollband_lo = df['t bbl'.split()]
    if not plots:  # 1st time
        candlestick_plot = fplt.candlestick_ochl(candlesticks)
        plots.append(candlestick_plot)
        # plots.append(fplt.plot(bollband_hi, color='#4e4ef1'))
        # plots.append(fplt.plot(bollband_lo, color='#4e4ef1'))
        # fplt.fill_between(plots[1], plots[2], color='#9999fa')
        # generate dummy orderbook plot, which we update next time
        x = len(candlesticks) + 0.5
        y = candlesticks.c.iloc[-1]
        orderbook = [[x, [(y, 1)]]]
        orderbook_colorfunc = fplt.horizvol_colorfilter([(0, 'bull'), (10, 'bear')])
        orderbook_plot = fplt.horiz_time_volume(orderbook, candle_width=1, draw_body=10, colorfunc=orderbook_colorfunc)
        plots.append(orderbook_plot)
        # use bitmex colors
        candlestick_plot.colors.update(dict(
            bull_shadow='#388d53',
            bull_frame='#205536',
            bull_body='#52b370',
            bear_shadow='#d56161',
            bear_frame='#5c1a10',
            bear_body='#e8704f'))
        orderbook_plot.colors.update(dict(
            bull_frame='#52b370',
            bull_body='#bae1c6',
            bear_frame='#e8704f',
            bear_body='#f6c6b9'))
    else:  # update
        plots[0].update_data(candlesticks)
        # plots[1].update_data(bollband_hi)
        # plots[2].update_data(bollband_lo)
        plots[3].update_data(orderbook)


class Views:
    def __init__(self):
        self.shown = False
        pass

    def Plot(self, chart):
        print("got chart ..->>>")
        # print(chart)
        df = pd.DataFrame(chart)
        # df = df.rename(columns={'x': 'time', 'o': 'open', 'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume'})
        df = df.rename(columns={'x': 't'})
        del df['y']  # ignore status=ok
        df.set_index('t')
        if not self.shown:
            fplt.create_plot('My Plot AMD', init_zoom_periods=75, maximize=False)
            update_plot(df)
            fplt.show()
            self.shown = True

        # fplt.timer_callback(update_plot, 0.5)  # update in 2 Hz
        # fplt.show()
        # return df.set_index('time')

        # print(df)
        pass

    def DisplayBacktestResults(self, charts):

        self.Plot(charts["Main"]["Series"]["AMD"]["Values"])
        pass

    def OnData(self, data):
        # print(data[0])

        if data["eType"] == "Log":
            return
        elif data["eType"] == "BacktestResult":

            # print(data)
            charts = data["oResults"]["Charts"]
            if len(charts) > 0:
                self.DisplayBacktestResults(charts)


