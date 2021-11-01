import unittest

import pandas as pd

from price_predicter import squash_into_1_candle, predict_bid_ask_delta


class TestPricePredicter(unittest.TestCase):
    def test_squash_into_1_candle(self):
        data = read_quotes_from_excel_to_dict()
        key, result = squash_into_1_candle(data)

        self.assertEqual(key, '14728527130')
        self.assertEqual(result[0], 62029.53)
        self.assertEqual(result[1], 62029.54)
        self.assertEqual(result[2], 62029.53)
        self.assertEqual(result[3], 61950.0)
        self.assertEqual(result[4], 61949.99)
        self.assertEqual(result[5], 61950.0)
        self.assertEqual(result[6], 61949.99)
        self.assertEqual(result[7], 62029.54)


    def test_predict_bid_ask_price(self):
        data = read_quotes_from_excel_to_dict()
        bid_delta, ask_delta = predict_bid_ask_delta(data, 10, 50)

        self.assertEqual(bid_delta, 4.530000000002474)
        self.assertEqual(ask_delta, 4.119999999998981)


def read_quotes_from_excel_to_dict():
    df = pd.read_csv("BTCUSDT_custom_interval_candles_history.csv")

    dict_quotes = {}
    for col in df.iteritems():
        dict_quotes.update({col[0] : [col[1][0], col[1][1], col[1][2],
                                      col[1][3], col[1][4], col[1][5],
                                      col[1][6], col[1][7]]})

    length = dict_quotes.__len__() - 1

    dict_quotes = dict(
        list(dict_quotes.items())[-length:])

    return dict_quotes

if __name__ == '__main__':
    unittest.main()
