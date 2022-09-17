# QuantPlayground

## convertible bond
量化分析可转债历史数据，获取特征信息

### ak_stock.db
- cb_basic 存储了所有可转债的基本信息
- cb_detail 可转债交易日线信息（2016-01-01~2022-09-14 上市的可转债）

### convertable_bond_playground.py
可使用BackTrader对可转债历史进行回测，100以下买入，130以上卖出（具体阈值可以修改）

### tshare.ipynb
对2016后开始上市的可转债进行历史最高价，最低价分析

