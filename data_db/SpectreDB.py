import json
import os
import pandas as pd
import sqlalchemy as sa


class SpectreDB:

    def __init__(self, json_path=None, key_name=None, table_name=None):
        self.json_path = json_path
        self.key_name = key_name
        if table_name:
            self.table_name = table_name
        SpectreDB.instantiate_engine(self)

    def instantiate_engine(self):
        '''
        :return engine: sqlalchemy engine for colornoun database
        :return conn: sqlalchemy engine connection for colornoun database
        '''
        # Connecting to mysql by providing a sqlachemy engine
        with open(self.json_path) as secrets_file:
            secrets = json.load(secrets_file)
            secrets_file.close()
        key_dict = secrets[self.key_name]
        engine_string = 'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST_IP}:{MYSQL_PORT}/{MYSQL_DATABASE}'
        self.engine = sa.create_engine(engine_string.format(MYSQL_USER=key_dict['MYSQL_USER'],
                                                    MYSQL_PASSWORD=key_dict['MYSQL_PASSWORD'],
                                                    MYSQL_HOST_IP=key_dict['MYSQL_HOST_IP'],
                                                    MYSQL_PORT=key_dict['MYSQL_PORT'],
                                                    MYSQL_DATABASE=key_dict['MYSQL_DATABASE']),
                               echo=False)
        self.conn = self.engine.connect()

    def parse_df(df, num_rows = 10000):
        '''
        Meant to parse pandas dataframe before upload. SQL connection times out if uploading more than
        25k rows.
        :param df: pandas datatframe
        :param num_rows: number of rows for dataframe to be split into
        :return list of datafraes of size n_rows
        '''
        df_list = list()
        num_split = len(df) // num_rows + 1
        for i in range(num_split):
            df_list.append(df[i*num_rows:(i+1)*num_rows])
        return df_list

    def filter_duplicates(self, upload_df, table_name):
        '''
        :param upload_df: pandas dataframe with column 'date'
        :param table_name: string
        return: upload_df without columns already in table
        '''
        #Query dates in table of that time frame
        #Filter upload df of overlaping timestamps
        start = str(upload_df['date'].min())
        end = str(upload_df['date'].max())
        date_df = self.query_by_date(start, end, table_name, fields=['date'])
        out_df = upload_df.append(date_df, ignore_index=True, sort=False)
        out_df.drop_duplicates(['date'], keep=False, inplace=True)
        return out_df

    def upload_df_to_db(self, df, table_name=None, date_encode=False):
        '''
        This is to help the parsing and uploading of pandas dataframes
        :param df: pandas dataframe
        :param table_name: name of table on database
        '''
        if not table_name:
            table_name = self.table_name
        if date_encode:
            df = self.date_encoder(df)
        df.drop_duplicates(['date'], inplace=True)
        if sa.inspect(self.engine).get_table_names().count(table_name) > 0:
            df = self.filter_duplicates(df,table_name)
        df_list = SpectreDB.parse_df(df)
        for upload_df in df_list:
            try:
                upload_df.to_sql(table_name, con=self.engine, index=False, if_exists='append')
                #print('Success')
            except Exception as e:
                #print('Failure')
                print(e)
        return 1

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

    def date_encoder(self, df):
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

    def drop_table(self, table_name=None):
        if not table_name:
            table_name = self.table_name
        self.conn.execute("DROP TABLE {}".format(table_name))

    def query_by_date(self, start, end, table_name=None, fields=['date', 'close']):
        '''
        This returns a dataframe of the requested data
        :param start: string in datetime format, eg. '2019-07-18 17:15:00'
        :param end: same format as start
        :param data: list of strings
        :return: pandas dataframe
        '''
        if not table_name:
            table_name = self.table_name
        # query data and save file
        fields.append('date')
        #make sure no duplicate entries in data list
        fields = list(set(fields))
        out_df = pd.DataFrame()
        stmt = 'SELECT ' + ','.join(map(str, list(fields)))
        stmt += ''' FROM `{}` '''.format(table_name) 
        stmt += '''WHERE `date` BETWEEN '{}' AND '{}' '''.format(start, end)
        return pd.read_sql(stmt, self.conn)

    #TODO: Finish this function
    def parse_datetime(self,start, end):  
        '''
        :param start: string in datetime format, eg. '2019-07-18 17:15:00'
        :param end: same format as start
        returns list of tuples (end, duration) for requesting IB data
        '''
        return 


    def update_from_IB(self, start, end, market='EURUSD', freq='1 hour') 
        from ib_insync import *
        # Need to have IB Gateway open to execute
        # util.startLoop()  # uncomment this line when in a notebook

        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=1)
        contract = Forex(market)
        bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='30 D',
                        barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

        # convert to pandas dataframe:
        df = util.df(bars)

#TODO: Pull from IB and upload to db
