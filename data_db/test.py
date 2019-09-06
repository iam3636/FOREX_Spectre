import unittest
import pandas as pd
from SpectreDB import SpectreDB

class Test_sdb(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv('test_post_IB.csv')
        self.sdb = SpectreDB(json_path = 'config.json',
                        key_name = 'sdb_test',
                        table_name = 'unittest_table_upload')

    def test_upload_df_to_db(self):
        self.assertEqual(1, self.sdb.upload_df_to_db(self.df))

'''
    def test_date_encoder(self):
        self.df = sdb.date_encoder(self.df)
        self.assertEqual(0,self.df.isna().sum().sum())

    def tearDown(self):
        self.conn.execute("DROP TABLE {}".format(self.table_name))
'''
