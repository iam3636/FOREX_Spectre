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

def set_utc_time(filename,  open_time_gmt):
    '''
    input filename: str, name of csv with columns [date, close, open]
    input open_time_gmt_gmt: int, start of bank sesison in gmt
    return: pandas dataframe with columns appended [return, utc, utc hour, day_ind]
    '''
    #Keep in mind that GMT/UTC time can switch due to summer time zone change
    df = pd.read_csv(data_file, index_col=0)
    #Time is local time, change to UTC
    df['utc']= df['date'].apply(convert_local_to_UTC)
    df['utc_hour']= (df['utc'].dt.hour + df['utc'].dt.minute/60).round()
    #Flag each day
    df['day_ind'] = df['utc_hour']
    df['day_ind'] = (np.where(df['day_ind']==(open_time_gmt - 2), 1, 0)).cumsum()
    return df

def set_stop_orders(df):
    '''
    input df: pandas dataframe, columns [utc_hour, high, low]
    return: df with columns [buy_stop, sell_stop] appended
    '''
    #Prep the order columns
    df['buy_stop'] = 0
    df['sell_stop'] = 0
    for i in range(df['day_ind'].max()):
        pre_open = df.loc[(df['day_ind']==(i+1)) & 
                (df['utc_hour'].isin([(open_time_gmt - x ) % 24 for x in [1,2]]))]
        df.loc[df['day_ind']==(i+1),'buy_stop'] = pre_open['high'].max()
        df.loc[df['day_ind']==(i+1),'sell_stop'] = pre_open['low'].min()
    return df

def drawdown(series):
    '''
    Thsi function takes the running max drawdown of a series of returns
    input series: pandas series, floats
    return series: pandas series, floats, drawdown
    '''
    series = (series.copy() + 1).cumprod()
    max_series = series.cummax()
    return (series - max_series).divide(max_series)

def set_trailing_stop(df, stop_loss=0.05):
    '''
    input df: pandas dataframe, with columns [open, buy_stop, sell_stop]
    input stop_loss: float > 0, default is 0.05 indicating exit position
                        when loss >= 0.05
    output df: pandas dataframe, with added column [signal]
    '''
    #fill side on day 
    #drop incomplete days
    df = df.loc[df['day_ind'] != 0].copy()
    #Find where greater than buy stop
    df['signal'] = df.eval('open > buy_stop').astype(int) 
    #Find where less than sell stop
    df['signal'] = df.eval('open < sell_stop').astype(int) * -1 
    #Filter for only the first break through of the day
    for i in range(1,df['day_ind'].max()):
        curr_day = df.loc[df['day_ind']==(i)].copy()
        break_thru = curr_day.loc[curr_day['signal']!=0]
        #Check if any break throughs on that day
        if len(break_thru > 0):
            #find the first break through of stop order
            first = break_thru.index.min()
            side = break_thru.loc[(break_thru.index == first) , 'signal'].values[0]
            #erase all other orders on that day
            curr_day['signal'] = 0
            curr_day.loc[(curr_day.index == first), 'signal'] = side
            curr_day['signal'] = curr_day['signal'].cumsum()
            #Find the drawdown after that point
            curr_day['drawdown'] = drawdown(curr_day['returns'] * curr_day['signal'])
            #Set the signal on the original
            curr_day.loc[curr_day['drawdown'] < -1 * stop_loss, 'signal'] = 0
            df.loc[df['day_ind']==(i), 'signal'] = curr_day['signal']
    return df


data_file = 'EURUSD30.csv'
london_open_gmt = 8
japan_open_gmt = 22
open_time_gmt = london_open_gmt
df = set_utc_time(data_file, open_time_gmt)
df['returns'] = df.eval('close - open').divide(df['open'])
df = set_stop_orders(df)
sl_list = np.linspace(0.005, 0.008, 100)
ret_list = []
for sl in sl_list:
    print(sl)
    temp_df = set_trailing_stop(df, stop_loss=sl)
    ret_list.append((temp_df.eval('returns * signal') + 1).prod())
out_df = pd.DataFrame({'Stop_Loss': sl_list, 'Returns': ret_list})
print(out_df.head())
out_df.to_csv('narrow_results.csv', index=False)
