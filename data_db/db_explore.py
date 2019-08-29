import pandas as pd

filename = 'scratch.csv'

df = pd.read_csv(filename)
print(df.head())
