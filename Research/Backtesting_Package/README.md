# Purpose

The purpose of this project is to further gain familiarity with the C programming language. I found that doing so in an arena I enjoy will enhance the experience

## Goal

Create a C-based package that can be called upon by a python script to create a backtest report on a time series of prices. 

### Input

A CSV file with headers `date,open,alloc` referencing the price of the asset at the beginning of the time stamp and the allocation [-1,1] of portfolio after observing that price. 

### Output

A series of metrics listed below, plus a `return_series.csv' with the headers `date,open,alloc,return,cum_return`

```
num_steps: Number of Observed Time Steps Passed
sharpe: Sharpe Ratio
scorinino: Scorintino Ratio
md: Max Drawdown
return: Overall Return [-1, inf)
acc: Accuracy of Trades
```
