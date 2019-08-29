import numpy as np
import pandas as pd

df = pd.read_csv('data.csv', index_col=None)

new_df = df[['date', 'open']]

new_df['alloc'] = np.random.randn(len(new_df))

new_df.to_csv('test.csv', index=False)
