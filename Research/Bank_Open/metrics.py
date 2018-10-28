import pandas as pd

def drawdown(series):
    '''
    This function takes the running max drawdown of a time series
    input series: pandas series, floats
    return series: pandas series, floats, drawdown
    '''
    max_series = series.cummax()
    return (series - max_series).divide(max_series)

def set_returns(series):
    '''
    input series: pandas series, floats
    output returns: panda series, floats
    '''
    _open = series[:-1].copy()
    _close = series.copy().shift(-1)[:-1]
    return (_close - _open).divide(_open)

def sharpe(strat_series, asset_series):
    '''
    This funciton finds the Sharpe Ratio of a Time Series
    Since using hours as frequency, risk free rate is essentially 0
    input strat_series: pandas series, floats, time series of strategy 
    input asset_series: pandas series, floats, time series of underlying asset 
    output sharpe ratio: float
    '''
    asset = set_returns(asset_series)
    strat = set_returns(strat_series)
    excess = strat - asset
    strat_return = strat_series.values[-1] - 1
    return (strat_return/(excess.std()))

df = pd.read_csv('strat_results.csv')
print('Return: {:.2f}%'.format((df['Strategy'].values[-1] - 1) * 100))
print('Max Drawdown: {:.2f}%'.format(((drawdown(df['Strategy'])).min()) * 100))
print('Sharpe Ratio: {:.2f}'.format(sharpe(df['Strategy'], df['EUR/USD'])))
