import unittest

import pandas as pd

from price_predicter import squash_into_1_candle, predict_bid_ask_delta


class TestPricePredicter(unittest.TestCase):
    def test_squash_into_1_candle(self):
        data = read_quotes_from_excel_to_dict()
        key, result = squash_into_1_candle(data)

        self.assertEqual(key, 0)
        self.assertEqual(result[0], 60064.16)
        self.assertEqual(result[1], 60072.66)
        self.assertEqual(result[2], 62325.34)
        self.assertEqual(result[3], 60050.01)


    def test_predict_bid_ask_price(self):
        data = read_quotes_from_excel_to_dict()
        latest_custom_interval = [61719.66, 61719.73, 61727.03, 61683.53]
        bid_delta, ask_delta = predict_bid_ask_delta(data, 15, 50, latest_custom_interval)

        self.assertEqual(bid_delta, 14.669999999998254)
        self.assertEqual(ask_delta, 26.589999999996508)


def read_quotes_from_excel_to_dict():
    return {row[0] : [row[1], row[2], row[3], row[4]]
            for _, row in pd.read_csv("BTCUSDT_ten_seconds_candles_history.csv").iterrows()}

if __name__ == '__main__':
    unittest.main()
