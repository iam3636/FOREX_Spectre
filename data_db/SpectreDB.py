import datetime as dt
import json
import os
import pandas as pd
import sqlalchemy as sa


class SpectreDB:

    def __init__(self, json_path=None, key_name=None, table_name=None,
            use_IB=False):
        self.json_path = json_path
        self.key_name = key_name
        if table_name:
            self.table_name = table_name
        SpectreDB.instantiate_engine(self)
        if use_IB:
            from ib_insync import IB, Forex, util
            # Need to have IB Gateway open to execute
            # util.startLoop()  # uncomment this line when in a notebook
            self.ib = IB()
            self.ib.connect('127.0.0.1', 7497, clientId=1)

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

    def parse_datetime(self, start, end, freq):  
        '''
        :param start: string in datetime format, eg. '2019-07-18 17:15:00'
        :param end: same format as start
        :param freq: string, format '# timeUnit' e.g. '1 hour'
        returns list of tuples (end[datetime], duration[str]) for requesting IB data
        '''
        #Change the string declared frequency to timedelta object
        freq_unit = freq.split()[1][0]
        if freq_unit == 's':
            max_dur = dt.timedelta(days=1)
        elif freq_unit == 'm':
            if(freq.split()[1][1]) == 'i':
                max_dur = dt.timedelta(weeks=1)
            else:
                max_dur = dt.timedelta(weeks=104)
        elif freq_unit == 'h':
            max_dur = dt.timedelta(weeks=4)
        elif freq_unit == 'd':
            max_dur = dt.timedelta(weeks=24)
        elif freq_unit == 'w':
            max_dur = dt.timedelta(weeks=104)
        else:
            raise(RuntimeError(''' Incorrect input for 'freq' argument'''))
        out_list = []
        start = dt.datetime.strptime(start + ' +0000', '%Y-%m-%d %H:%M:%S %z')
        end = dt.datetime.strptime(end + ' +0000', '%Y-%m-%d %H:%M:%S %z')
        t_diff = end - start
        window_count = t_diff // max_dur
        max_dur_str = '{} D'.format(max(1, max_dur.days))
        while window_count > 0:
            out_list.append((end,max_dur_str))
            end -= max_dur
            window_count -= 1
        leftover_time = end - start
        out_list.append((end, '{} D'.format(max(1, 1 + leftover_time.days))))
        return out_list

    def pull_from_IB(self, start, end, market='EURUSD', freq='1 hour'): 
        '''
        Note, all times should be UTC (aka Zulu, Z, GMT)

        :param start: string in datetime format, eg. '2019-07-18 17:15:00'
        :param end: same format as start
        :param freq: Must be one of: ‘1 secs’, ‘5 secs’, ‘10 secs’ 15 secs’, 
                ‘30 secs’, ‘1 min’, ‘2 mins’, ‘3 mins’, ‘5 mins’, ‘10 mins’,
                ‘15 mins’, ‘20 mins’, ‘30 mins’, ‘1 hour’, ‘2 hours’, 
                ‘3 hours’, ‘4 hours’, ‘8 hours’, ‘1 day’, ‘1 week’,
                ‘1 month’ (see IB Docs)
        '''
        #Parse the requested window so API calls are not as lengthy
        time_list = self.parse_datetime(start, end, freq)
        df_list = []
        contract = Forex(market)
        for time_pair in time_list:
            '''
            useRTH (bool) – If True then only show data from within Regular Trading Hours,
                    if False then show all data.
            formatDate (int) – For an intraday request setting to 2 will cause the returned
                    date fields to be timezone-aware datetime.datetime with UTC timezone,
                    instead of local timezone as used by TWS.
            '''
            bars = self.ib.reqHistoricalData(contract, endDateTime=time_pair[0], 
                                        durationStr=time_pair[1],
                                        barSizeSetting=freq, whatToShow='MIDPOINT', useRTH=True)

            # convert to pandas dataframe:
            df = util.df(bars)
            #drop columns ['barCount', 'average']
            df_list.append(df[['date', 'open', 'high', 'low', 'close']].copy())
        return df_list

    def update_from_IB(self, start, end, market='EURUSD', freq='1 hour'): 
        df_list = self.pull_from_IB(start, end, market, freq) 
        for df in df_list:
            self.upload_df_to_db(df, date_encode=True)
        return 1
