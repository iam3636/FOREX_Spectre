# Spectre Engineering Backtesting

## Standards

Backtesting will be conducted with 1 year of training data, 1 month cross-validation set, and 1 month test. For example, if a backtest is being run in September 2019, the data will be broken down

| Window                | Set       |
| --------------------- | --------- |
| July 2018 - June 2019 | Training  |
| July 2019             | Cross-Val |
| August 2019           | Test      |

A successful backtest entails surpassing the following standards for each metric in all three sets of data.

| Metric                       | Standard |
| ---------------------------- | -------- |
| Returns (with trading costs) | > 0      |
| Sharpe Ratio                 | > 1      |
| Sciorintino Ratio            | > 1      |
| Max Drawdown                 | < 20%    |
| Accuracy                     | > 50%    |

If backtesting is successful, the algorithm will be deployed to paper trading for further trials.

Note: Before backtesting, algorithms will be executed over a randomized time series to ensure there is no-look ahead bias, yes this will be contained in the development phase.

### Metrics Explained

#### Returns with Trading Costs

This is the 

#### Sharpe Ratio

The Sharpe is the industry standard measure for risk-adjusted returns

$ S = \frac{R_p - R_f}{\sigma_p} $

Where $R_p$ is the return of the portfolio, $R_f$ is the risk free rate, and $\sigma_p$ is the standard deviation of the portfolio's excess returns.

#### Sciorintino Ratio

This is a spin on the Sharpe ratio where instead the denominator is $\sigma_d$, is the standard deviation of the downside returns. This eliminated the negative impact of positive returns on the overall metric.

#### Max Drawdown

The largest loss of value over the time period in question.

### Calculations

Consider the series of $o_0, o_1, \dots, o_n  $ where there are $n+1$ time steps observed over the course of a month, where at each period we allocated $a_0, a_1, \dots, a_n$.  Lets say the 1-month LIBOR rate for that period was 0.022 (as it was on October 4, 2018). 

A return over period can be calculated as

$ r_i = \frac{o_{i+1} - o_i}{o_i} \bullet  a_i $

Thus we see that the overall return is the compounded return of this series

$R_p = -1 + \prod (1 + r_i) $

Then we can caluculate the accuracy of the trades as

$ acc = \frac{\sum  1\{r_i > 0 \} }{n} $

The standard deviation of these returns looks like

$\sigma_p = \sqrt{ E(r_i^2) + (E(r_i))^2} $

and standard deviation of downside returns looks like

$\sigma_d = \sqrt{ n_d^{-1} ( \sum 1\{r_i < 0\} \bullet r_i^2)+ ( n_d^{-1}\sum 1\{r_i < 0\} \bullet r_i))^2} $

$n_d =  \sum 1\{r_i < 0\}$

The most interesting calculation is the max drawdown. In an online setting (attempting to never hold more than a few doubles in memory at any given moment), the calculation takes less trickery than in a vectorized setting. 

Online Implementation

```python
max = 1
md = 0
cum_return = 1
for i in range(n):
    cum_return *= 1 + r[i]
    if (max < cum_return):
        max = cum_return
    else:
        md_temp = (max - cum_return)/max
        if md_temp > md:
            md = md_temp
    
```

Vectorize Implementation

```python
import pandas as pd
rolling_max = (1 + returns).cumprod().cummax() - 1
cum_return = (1 + returns).cumprod() - 1
md = (rolling_max - cum_return).divide(rolling_max).max()
```


