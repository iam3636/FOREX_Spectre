import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('narrow_results.csv')
df.plot('Stop_Loss', 'Returns')
plt.savefig('narrow.png')
