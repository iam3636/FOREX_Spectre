# Bank Open Trade

Credit to Ryan (ryan@thestreets.co) for outlining this concept to me in his excellent introductory course to FOREX trading.

## Strategy Outline

1. Place buy stop and sell stop (resting volatility box) at the high and low (respectively) of the two hours prior to the bank open of London or Japan. Stop loss on opposite ends of the box.
2. Make trailing stop.

The intution of this is quite important. Opening of major bank sessions welcomes a flood of volume in currency movement, whose suddeness could create a quick price shift in either direction.

## Creating the Backtest

1. Break up the time series into windows, so only ever dealing with a specific window (Bank open to 2 hours before next open session)

2. Set indicator on series to see if breaks above or below the set stop orders

3. Take the first break through (bank open trade only cares about the first spike in volatility)

4. Take the cumulative maximum (or minimum) to that point

5. Take the difference between that cumulative metric and the current price

6. If  the drawdown is ever greater than 5 bips, that is where the trade would end.


