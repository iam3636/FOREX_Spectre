import pandas as pd
import sqlalchemy as sa

#TODO: Make so that duplicates are not uploaded to DB (maybe a group by, or a query before uploa?
#TODO: Upload data with epoch, hour, day of week, minute, second, year, month
#TODO: Make query data function

def instantiate_engine(json_path, key_name):
    '''
    :return engine: sqlalchemy engine for colornoun database
    :return conn: sqlalchemy engine connection for colornoun database
    '''
    # Connecting to mysql by providing a sqlachemy engine
    import json
    import os
    with open(json_path) as secrets_file:
        secrets = json.load(secrets_file)
        secrets_file.close()
    key_dict = secrets[key_name]
    engine_string = 'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST_IP}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    engine = sa.create_engine(engine_string.format(MYSQL_USER=key_dict['MYSQL_USER'],
                                                MYSQL_PASSWORD=key_dict['MYSQL_PASSWORD'],
                                                MYSQL_HOST_IP=key_dict['MYSQL_HOST_IP'],
                                                MYSQL_PORT=key_dict['MYSQL_PORT'],
                                                MYSQL_DATABASE=key_dict['MYSQL_DATABASE']),
                           echo=False)
    conn = engine.connect()
    return engine,conn

def parse_df(df, num_rows = 10000):
    '''
    Meant to parse pandas dataframe before upload. SQL connection times out if uploading more than
    25k rows.
    :param df: pandas datatframe
    :param num_rows: number of rows for dataframe to be split into
    :return:
    '''
    df_list = list()
    num_split = len(df) // num_rows + 1
    for i in range(num_split):
        df_list.append(df[i*num_rows:(i+1)*num_rows])
    return df_list

def upload_df_to_db(df, table_name, engine):
    '''
    This is to help the parsing and uploading of pandas dataframes
    :param df: pandas dataframe
    :param table_name: name of table on database
    :param engine: sqlalchemy engine
    '''
    df_list = parse_df(df)
    for upload_df in df_list:
        try:
            upload_df.to_sql(table_name, con=engine, index=False, if_exists='append')
            print('Success')
        except Exception as e:
            print('Failure')
            print(e)

def grab_IB_data(currency_pair='EURUSD', endDateTime='', durationStr='30 D',
        barSizeSetting='1 hour', whatToShow='MIDPOINT'):
    '''
    param currency_pair: string
    param endDateTime:  string,  Can be set to ‘’ to indicate the current time, 
                        or it can be given as a datetime.date or datetime.datetime,
                        or it can be given as a string in ‘yyyyMMdd HH:mm:ss’ format.
                        If no timezone is given then the TWS login timezone is used.
    param durationStr: str, Time span of all the bars. Examples: ‘60 S’, ‘30 D’, ‘13 W’,
                        ‘6 M’, ‘10 Y’.
    param barSizeSetting: str, Time period of one bar. Must be one of: ‘1 secs’, ‘5 secs’, 
                        ‘10 secs’ 15 secs’, ‘30 secs’, ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’,
                        ‘10 mins’, ‘15 mins’, ‘20 mins’, ‘30 mins’, ‘1 hour’, ‘2 hours’,
                        ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’, ‘1 month’.
    param whatToShow: str, Specifies the source for constructing bars. 
                    Must be one of: ‘TRADES’, ‘MIDPOINT’, ‘BID’, ‘ASK’, ‘BID_ASK’,
                    ‘ADJUSTED_LAST’, ‘HISTORICAL_VOLATILITY’, ‘OPTION_IMPLIED_VOLATILITY’,
                    ‘REBATE_RATE’, ‘FEE_RATE’, ‘YIELD_BID’, ‘YIELD_ASK’, ‘YIELD_BID_ASK’,
                    ‘YIELD_LAST’.
    return: pandas dataframe with no index and columns
            ['date', 'open', 'high', 'low', 'close']
            date is UTC

    note: Need to have IB Gateway open to execute
    '''
    #from ib_insync import *
    from ib_insync import IB, Forex, util
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)
    contract = Forex(currency_pair)
    bars = ib.reqHistoricalData(contract, endDateTime, durationStr,
                    barSizeSetting, whatToShow, useRTH=True, formatDate=2)
    '''
    useRTH (bool) – If True then only show data from within Regular Trading Hours,
            if False then show all data.
    formatDate (int) – For an intraday request setting to 2 will cause the returned
            date fields to be timezone-aware datetime.datetime with UTC timezone,
            instead of local timezone as used by TWS.
    '''
    # convert to pandas dataframe:
    df = util.df(bars)
    return df[['date', 'open', 'high', 'low', 'close']].copy()

def date_encoder(df):
    '''
    input df: pandas dataframe with column 'date' in timezone-aware datetime.datetime
            example('2019-08-28 21:15:00+00:00')
    output: pandas dataframe with additional columns ['weekday', 'day_of_year'
            'year', 'month', 'day', 'hour', 'minute']
    '''
    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].apply(lambda x: x.weekday())
    df['day_of_year'] = df['date'].apply(lambda x: x.dayofyear)
    df['year'] = df['date'].apply(lambda x: x.year)
    df['month'] = df['date'].apply(lambda x: x.month)
    df['day_of_month'] = df['date'].apply(lambda x: x.day)
    df['hour'] = df['date'].apply(lambda x: x.hour)
    df['minute'] = df['date'].apply(lambda x: x.minute)
    return df

#TODO: Convert for Forex purposes
def query_raw_data(coin,columns,first_epoch,last_epoch, conn, normalize=True, norm_min=10000):
    '''
    :param coin: string, coin ticker
    :param columns: list of strings, columns desired can be
        ['return','spread','open_time','close_time','num_trades','open','high','low','close','volume',
            'quote_asset_volume','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','coin']
    :param first_epoch: int
    :param last_epoch: int
    :param conn: sqlalchemy engine connection for colornoun database
    :param normalize: bool, if the spread or volume is to be normalized
    :param norm_min: int, number of minutes to normalize over, default is 10k about 1 week
    :return: sql query result as a pandas dataframe
    '''
    query_cols = set(columns)
    offset = 60000 * (norm_min - 1)
    #query data for necessary columns desired
    if 'return' in columns:
        query_cols = query_cols.union(set(['open', 'close']))
        query_cols.remove('return')
    if 'spread' in columns:
        query_cols = query_cols.union(set(['high', 'low']))
        query_cols.remove('spread')
    #offset the query start date to accomodate normalization
    if 'spread' in columns or 'volume' in columns and normalize:
        first_epoch -= offset
    #develop query statement
    stmt = 'SELECT ' + ','.join(map(str, list(query_cols)))
    stmt += ' FROM {}_binance_raw'.format(coin)
    stmt += ' WHERE open_time >= {} AND open_time <= {}'.format(first_epoch, last_epoch)
    df = pd.read_sql(stmt, conn)
    #make sure data is in appropriate type
    int_cols = ['open_time', 'close_time', 'num_trades']
    for col in query_cols.intersection(set(int_cols)):
        df[col] = df[col].astype(int)
    float_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                  'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
    for col in query_cols.intersection(set(float_cols)):
        df[col] = df[col].astype(float)
    if 'return' in columns:
        df['return'] = (df.close - df.open).divide(df.open)
    if 'spread' in columns:
        df['spread'] = df.high - df.low
        if normalize:
            df['spread'] = (df['spread'] - df['spread'].rolling(norm_min).mean()).divide(
                df['spread'].rolling(norm_min).std())
    if 'volume' in columns and normalize:
        df['volume'] = (df['volume'] - df['volume'].rolling(norm_min).mean()).divide(
            df['volume'].rolling(norm_min).std())
    df.dropna(inplace=True)
    return df[columns].copy()

#TODO: Convert for Forex purposes
def get_last_epoch_binance_raw_data(coin,conn):
    '''
    This is meant to help uploading the raw historic data to the colornoun db
    :param coin: string, ticker of coin
    :param conn: sqlalchemy engine connection for colornoun database
    :param engine: engine: sqlalchemy engine for colornoun database
    :return last_epoch: int
    '''
    try:
        #Query Database for most recent enty
        stmt = '''SELECT open_time from {}_binance_raw ORDER BY open_time DESC LIMIT 1'''.format(
            coin)
        df = pd.read_sql(stmt,conn)
        last_epoch = df.values[0][0]
    except:
        last_epoch = 1500004800000
    return last_epoch

#TODO: Convert for Forex purposes
def get_data_gaps(input_df):
    '''
    This is meant to find any breaks in the data coverages
    :param input_df: Binance raw dataframe with column named open_time which are millisecond epoch integers
        This is the standard form for the Binance API
    :return: a list of tuples of epochs where data is missing
    '''
    df = input_df.copy()
    df = df.sort_values('open_time', ascending=False)
    df['diff'] = df.open_time - df.open_time.shift(-1)
    df['prev'] = df.open_time.shift(-1)
    df.prev += 60000
    missing_data = df.loc[df['diff'] > 60000].copy()
    
    return list(zip(missing_data.prev.astype(int), missing_data.open_time.astype(int)))

#TODO: Convert for Forex purposes
def grab_data(conn,coins, start_epoch, end_epoch, data_list):
    '''
    This returns a dataframe of the requested data
    :param conn: sqlalchemy engine connection for colornoun database
    :param coins: list of strings, tickers of desirec coins
    :param start_epoch: int
    :param end_epoch: int
    :param data_list: list of strings,
        ['return','spread','open_time','close_time','num_trades','open','high','low','close','volume',
            'quote_asset_volume','taker_buy_base_asset_volume','taker_buy_quote_asset_volume','coin']
    :return: pandas dataframe, columns of names data_TICKER (ex: return_LTC)
    '''
    # query data and save file
    data_list.append('open_time')
    #make sure no duplicate entries in data list
    data_list = list(set(data_list))
    out_df = pd.DataFrame()
    for coin in coins:
        print('Grabbing {} Data'.format(coin))
        temp_df = query_raw_data(coin, data_list, start_epoch, end_epoch, conn)
        temp_df.set_index('open_time', inplace=True)
        # rename the comlumns
        map_dict = {}
        for column in temp_df.columns:
            map_dict[column] = '{}_{}'.format(column, coin)
        temp_df.rename(columns=map_dict, inplace=True)
        # append this to the out_Df
        out_df = out_df.join(temp_df, how='outer')
    return out_df
