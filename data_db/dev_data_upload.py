import pandas as pd
import sdb

json_path = 'config.json'
key_name = 'sdb_test'

engine, conn = sdb.instantiate_engine(json_path, key_name)
df = sdb.grab_IB_data(endDateTime= '',
        durationStr='2 D')

print(df.head())

df.to_csv('scratch.csv', index=False)

'''
filename = 'scratch.csv'

df = pd.read_csv(filename)

df.drop(['Unnamed: 0'], axis=1, inplace=True)

print(df.head())

engine, conn = sdb.instantiate_engine(json_path, key_name)
sdb.upload_df_to_db(df, 'test_EURUSD', engine)
'''
