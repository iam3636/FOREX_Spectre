import unittest
import pandas as pd
from SpectreDB import SpectreDB

class TestSpectreDB(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv('test_post_IB.csv')
        self.test_IB = False
        self.sdb = SpectreDB(json_path = 'config.json',
                        key_name = 'sdb_test',
                        table_name = 'unittest_table_upload',
                        use_IB= self.test_IB)

    def test_upload_df_to_db(self):
        self.assertEqual(1, self.sdb.upload_df_to_db(self.df,
                            date_encode=True))
        self.sdb.drop_table()

    def test_date_encoder(self):
        self.df = self.sdb.date_encoder(self.df)
        self.assertEqual(0,self.df.isna().sum().sum())

    def test_query(self):
        self.sdb.upload_df_to_db(self.df,
                            date_encode=True)
        ret_df = self.sdb.query_by_date(start = '2019-08-28 22:00:00', end='2019-08-29 01:00:00')
        self.assertEqual(ret_df.shape[0], 4)
        self.sdb.drop_table()

    def test_no_duplicates_uploaded(self):
        self.sdb.upload_df_to_db(self.df,
                            date_encode=True)
        self.sdb.upload_df_to_db(self.df,
                            date_encode=True)
        ret_df = self.sdb.query_by_date(start = '2019-08-28 22:00:00', end='2019-08-29 01:00:00')
        self.sdb.drop_table()
        self.assertEqual(ret_df.shape[0], 4)

    def test_parse_datetime(self):
        start = '2019-08-28 22:00:00' 
        end='2019-08-30 11:00:00'
        out_list = self.sdb.parse_datetime(start, end, '1 hour') 
        self.assertEqual(out_list[0][1], '2 D')
        self.assertEqual(len(out_list), 1)
        out_list = self.sdb.parse_datetime(start, end, '30 secs') 
        self.assertEqual(out_list[0][1], '1 D')
        self.assertEqual(len(out_list), 2)
        start = '2018-08-28 22:00:00' 
        out_list = self.sdb.parse_datetime(start, end, '1 hour') 
        self.assertEqual(out_list[0][1], '28 D')

    def test_parse_datetime_exception(self):
        start = '2019-08-28 22:00:00' 
        end='2019-08-30 11:00:00'
        with self.assertRaises(RuntimeError) as e:
            self.sdb.parse_datetime(start, end, '1 year') 
    
    def test_update_from_IB(self):
        if self.test_IB:
            start = '2019-08-28 22:00:00' 
            end='2019-08-30 11:00:00'
            out_list = self.sdb.pull_from_IB(start, end, freq='30 secs') 
            #Test just the pull
            self.assertEqual(len(out_list), 2)
            #Test the full update
            self.sdb.update_from_IB(start, end, freq='30 secs') 
            ret_df = self.sdb.query_by_date(start = '2019-08-28 22:00:00', end='2019-08-28 23:00:00')
            self.assertEqual(ret_df.shape[0], 121)
            self.sdb.drop_table()

if __name__ == '__main__':
    unittest.main()
