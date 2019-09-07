import unittest
import pandas as pd
from SpectreDB import SpectreDB

class TestSpectreDB(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv('test_post_IB.csv')
        self.sdb = SpectreDB(json_path = 'config.json',
                        key_name = 'sdb_test',
                        table_name = 'unittest_table_upload')

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



#TODO: Test pull from IB and upload

if __name__ == '__main__':
    unittest.main()
