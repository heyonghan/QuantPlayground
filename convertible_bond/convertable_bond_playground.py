import tushare as ts
import pandas as pd

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
# Import the backtrader platform
import backtrader as bt
from backtrader_plotting import Bokeh
from backtrader_plotting.schemes import Tradimo


class MyStrategy(bt.Strategy):
    # 策略参数
    params = dict(
        printlog=True
    )

    def __init__(self):
        self.mas = dict()

    def next(self):
        # dt = self.data.datetime[0]
        # dt = bt.num2date(dt)
        # print('%s' % (dt.isoformat()))

        # 得到当前的账户价值
        total_value = self.broker.getvalue()
        cash = self.broker.get_cash()
        p_value = total_value * 0.98 / 10
        # p_value = min(p_value, cash)
        for data in self.datas:
            # 获取仓位
            pos = self.getposition(data).size
            if data.close[0] != 0 and data.close[0] < 105 and pos == 0:
                # print(f"p_value:{p_value}")
                max_value = min(p_value, cash)
                size = int(max_value / 100 / data.close[0]) * 100
                if size > 0:
                    self.buy(data=data, size=size)
                    cash = cash - ( data.close[0] * size )

            if pos != 0 and data.close[0] > 125:
                self.close(data=data)
                cash = cash + (data.close[0] * pos)


    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()},{txt}')

    # 记录交易执行情况（可省略，默认不输出结果）
    def notify_order(self, order):

        # 如果order为submitted/accepted,返回空
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 如果order为buy/sell executed,报告价格结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'{print(order.data._name)}')
                self.log(f'买入:\n价格:{order.executed.price:.2f},\
                成本:{order.executed.value:.2f},\
                手续费:{order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'{print(order.data._name)}')
                self.log(f'卖出:\n价格：{order.executed.price:.2f},\
                成本: {order.executed.value:.2f},\
                手续费{order.executed.comm:.2f}')
            self.bar_executed = len(self)
            # 如果指令取消/交易失败, 报告结果
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('交易失败')
        self.order = None

    # 记录交易收益情况（可省略，默认不输出结果）
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'策略收益：\n毛收益 {trade.pnl:.2f}, 净收益 {trade.pnlcomm:.2f}')


def align_trading_date(bond_data: pd.DataFrame, p_from_date, p_to_date):
    date_range = pd.date_range(start=p_from_date, end=p_to_date,
                               freq="D")  # freq="D"表示按天，可以按分钟，月，季度，年等

    bond_data = bond_data.set_index("trade_date")
    bond_data = bond_data.reindex(index=date_range)
    bond_data = bond_data[['open', 'close', 'high', 'low', 'volume']]
    bond_data = bond_data.fillna(method='ffill')
    bond_data = bond_data.fillna(0)
    return bond_data


def load_bond_datd():
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///ak_stock.db')
    bond_data = pd.read_sql("cb_detail", engine)
    bond_data = bond_data[['ts_code', 'trade_date', 'open', 'close', 'high', 'low', 'vol']]
    bond_data['trade_date'] = pd.to_datetime(bond_data['trade_date'])
    bond_data = bond_data.rename(columns={"vol": "volume"})
    return bond_data


bond_detail_data = load_bond_datd()

cerebro = bt.Cerebro()

from_date = datetime.datetime(2016, 1, 1)
to_date = datetime.datetime(2022, 9, 14)
for ts_code in bond_detail_data['ts_code'].unique()[:100]:
#     ts_code = "110033.SH"
    bond_detail_special = bond_detail_data[bond_detail_data['ts_code'] == ts_code]
    bond_detail_special = align_trading_date(bond_detail_special, from_date, to_date)

    data = bt.feeds.PandasData(dataname=bond_detail_special,
                               fromdate=from_date,
                               todate=to_date
                               )
    cerebro.adddata(data, name=ts_code)
    print(f"{ts_code} data load done!!")

print("Start Regression Test..")
# 回测设置
start_cash = 1000000.0
cerebro.broker.setcash(start_cash)
# 设置佣金为万分之二
cerebro.broker.setcommission(commission=0.0002)
cerebro.broker.set_coc(True)
# 添加策略
cerebro.addstrategy(MyStrategy, printlog=True)
cerebro.run()
# 获取回测结束后的总资金
port_value = cerebro.broker.getvalue()
pnl = port_value - start_cash
# 打印结果
print(f'总资金: {round(port_value, 2)}')
print(f'净收益: {round(pnl, 2)}')

# cerebro.plot(style='candlestick')
cerebro.plot(numfigs=3)
# b = Bokeh(style='bar', plot_mode='single', scheme=Tradimo())
# cerebro.plot(b)
