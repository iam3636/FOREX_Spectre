import datetime
import numpy as np
import pandas as pd

def convert_local_to_UTC(timestamp):
    '''
    param timetstamp: datetime object for local timezone
    of formate "%Y-%m-%d %H:%M:%S"
    return: datetime object in UTC
    '''
    #Assumes current machine and read data are on same time zone
    UTC_OFFSET_TIMEDELTA = datetime.datetime.utcnow() - datetime.datetime.now()
    local_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return (local_datetime + UTC_OFFSET_TIMEDELTA)

#Keep in mind that GMT/UTC time can switch due to summer time zone change
london_open_gmt = 8
japan_open_gmt = 22
open_time = london_open_gmt

data_file = 'EURUSD30.csv'
df = pd.read_csv(data_file, index_col=0)
#Time is local time, change to UTC
df['utc']= df['date'].apply(convert_local_to_UTC)
df['utc_hour']= (df['utc'].dt.hour + df['utc'].dt.minute/60).round()
#Flag each day
df['day_ind'] = df['utc_hour']
df['day_ind'] = (np.where(df['day_ind']==(open_time - 2), 1, 0)).cumsum()
#Period Returns
df['return'] =  (df.eval('close - open')).divide(df['open'])  
#Prep the order columns
df['buy_stop'] = 0
df['sell_stop'] = 0
for i in range(df['day_ind'].max()):
    pre_open = df.loc[(df['day_ind']==(i+1)) & (df['utc_hour'].isin([(open_time - x ) % 24 for x in [1,2]]))]
    df.loc[df['day_ind']==(i+1),'buy_stop'] = pre_open['high'].max()
    df.loc[df['day_ind']==(i+1),'sell_stop'] = pre_open['low'].min()
#drop incomplete days
df = df.loc[df['day_ind'] != 0].copy()
#Find where greater than buy stop
df['signal'] = df.eval('open > buy_stop').astype(int) 
#Find where less than sell stop
df['signal'] = df.eval('open < sell_stop').astype(int) * -1 
#Filter for only the first break through of the day
for i in range(1,df['day_ind'].max()):
    curr_day = df.loc[df['day_ind']==(i)]
    break_thru = curr_day.loc[curr_day['signal']!=0]
    #Check if any break throughs on that day
    if len(break_thru > 0):
        first = break_thru.index.min()
        side = break_thru.loc[(break_thru.index == first) , 'signal'].values[0]
        df.loc[(df['day_ind']==(i)), 'signal'] = 0
        #Find the drawdown
        #TODO 
        df.loc[ (df.index == first), 'signal'] = side

#TODO
#Filter Signal on the drawdown
print(df.head(20))
