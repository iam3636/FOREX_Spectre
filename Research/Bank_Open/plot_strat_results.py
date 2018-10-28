import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('strat_results.csv')
df.plot('date', ['EUR/USD', 'Strategy'])
plt.savefig('strat.png')
