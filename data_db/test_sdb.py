import unittest

import pandas as pd
import sdb

class Test_date_encode(unittest.TestCase):

    def setUp(self):
        self.df = pd.read_csv('test_post_IB.csv')

    def test_encoder_proper(self):
        self.df = sdb.date_encoder(self.df)
        self.assertEqual(0,self.df.isna().sum().sum())
