from ib_insync import *
# Need to have IB Gateway open to execute
# util.startLoop()  # uncomment this line when in a notebook

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Forex('EURUSD')
bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='30 D',
                barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

# convert to pandas dataframe:
df = util.df(bars)
df[['date', 'open', 'high', 'low', 'close']].to_csv('EURUSD30.csv')
