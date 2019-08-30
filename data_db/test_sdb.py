import unittest

import pandas as pd
import sdb

class Test_date_encode(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv('test_post_IB.csv')

    def test_encoder_proper(self):
        self.df['date'] = pd.to_datetime(self.df['date'].head())
        self.assertEqual(0,self.df.isna().sum().sum())
        #print(self.df['date'].apply(lambda x: x.minute))
