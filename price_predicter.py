import time
import numpy as np
import pandas as pd
import websocket
import json


# connecting to book of orders
cc = 'btcusdt'
socket = f'wss://stream.binance.com:9443/ws/{cc}@bookTicker'

# time interval we are grouping data
timeframe_inseconds = 10

# starting point in time of the interval(timeframe_inseconds)
timestarted = time.perf_counter()

# history of all grouped bids and asks of the time interval(timeframe_inseconds)
custom_timeframe_candles_history = {}

# all bids and asks for custom time interval
bids_asks_for_custom_time_interval = {}

# contains bids and asks delta values
bid_ask_delta_prediction = []

# number of grouped bids and asks of the time interval(timeframe_inseconds)
# to rely on in our price predictions
# the greater the number the more precise is prediction on the long run
NUMBER_OF_CANDLES_TO_RELY_ON = 2

# numbers of all correctly predicted prices for bids and asks
bid_success_rate = 0
ask_success_rate = 0

# numbers of all correctly predicted prices for bids and asks in percentage
bid_success_rate_percents = 0
ask_success_rate_percents = 0

# turns on/off displaying success rate
show_success_rate = True

def procss_messages(message):
    global bid_ask_delta_prediction
    global timestarted

    json_message = json.loads(message)
    b_a_pair = [json_message['b'], json_message['a']]

    bids_asks_for_custom_time_interval.update({json_message["u"]: b_a_pair})

    timeframe_timer = float(time.perf_counter() - timestarted)
    # print(timeframe_timer)
    if (timeframe_timer > timeframe_inseconds):
        timestarted = time.perf_counter()
        opentime, custom_timeframe_candle = squash_into_1_candle(bids_asks_for_custom_time_interval)
        custom_timeframe_candles_history.update({opentime: custom_timeframe_candle})

        make_predictions(custom_timeframe_candle, bid_ask_delta_prediction)

        # if ten_seconds_candles_history.__len__() > 2:
        #     save to excel
        # df = pd.DataFrame(custom_timeframe_candles_history)
        # df.to_csv('custom_timeframe_candles_history.csv', encoding='utf-8-sig')

        print(custom_timeframe_candle)
        bids_asks_for_custom_time_interval.clear()

        # get prediction
        if custom_timeframe_candles_history.__len__() > NUMBER_OF_CANDLES_TO_RELY_ON:
            bid_ask_delta_prediction = predict_bid_ask_delta(custom_timeframe_candles_history)


def make_predictions(custom_timeframe_candle, bid_ask_delta_prediction):

    if bid_ask_delta_prediction.__len__() > 0:

        estimated_bid_price = float(custom_timeframe_candle[0]) + float(bid_ask_delta_prediction[0])
        print(f'### Predicted bid price {estimated_bid_price} ###')
        print(f'### Best bid price {float(custom_timeframe_candle[2])} ###')

        estimated_ask_price = float(custom_timeframe_candle[1]) - float(bid_ask_delta_prediction[1])
        print(f'### Predicted ask price {estimated_ask_price} ###')
        print(f'### Best ask price {float(custom_timeframe_candle[3])} ###')

        if show_success_rate:
            calculate_success_rate(custom_timeframe_candle)


def calculate_success_rate(custom_timeframe_candle):
    global bid_success_rate
    global bid_success_rate_percents
    global ask_success_rate
    global ask_success_rate_percents

    if float(custom_timeframe_candle[2]) - float(custom_timeframe_candle[0]) > bid_ask_delta_prediction[0]:
        bid_success_rate += 1
        bid_success_rate_percents = float(bid_success_rate / (
                custom_timeframe_candles_history.__len__() - float(NUMBER_OF_CANDLES_TO_RELY_ON))) * 100

    print(f'### Bid success rate {bid_success_rate_percents} % ###')

    if float(custom_timeframe_candle[1]) - float(custom_timeframe_candle[3]) > bid_ask_delta_prediction[1]:
        ask_success_rate += 1
        ask_success_rate_percents = float(ask_success_rate / (
                custom_timeframe_candles_history.__len__() - float(NUMBER_OF_CANDLES_TO_RELY_ON))) * 100

    print(f'### Ask success rate {ask_success_rate_percents} % ###')

def on_message(ws, message):
    procss_messages(message)

def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")

def on_open(ws):
    print("### Connection opened ###")

def squash_into_1_candle(quotes_in_10_seconds):
    one_candle = []

    # adding "open bid and ask prices"
    first_quote_key = next(iter(quotes_in_10_seconds))
    one_candle.append(quotes_in_10_seconds.get(first_quote_key)[0])
    one_candle.append(quotes_in_10_seconds.get(first_quote_key)[1])

    # squashing prices to get best bid and ask
    one_candle.append(max(quotes_in_10_seconds.values(), key=lambda x: x[0])[0])
    one_candle.append(min(quotes_in_10_seconds.values(), key=lambda x: x[1])[1])

    return first_quote_key, one_candle

def predict_bid_ask_delta(c_time_cndl_hist):
    # fig, ax = plt.subplots()
    volatility_dict_up = {}
    volatility_dict_down = {}
    bid_ask_prediction = []
    required_percentile = 50

    for candle in c_time_cndl_hist:
        volatility_up = float(c_time_cndl_hist.get(candle)[2]) - float(c_time_cndl_hist.get(candle)[0])
        volatility_dict_up.update({candle: volatility_up})

        volatility_down = float(c_time_cndl_hist.get(candle)[1]) - float(c_time_cndl_hist.get(candle)[3])
        volatility_dict_down.update({candle: volatility_down})

    # getting bid ask deltas required_percentile value
    bid_prediction = np.percentile(np.array(list(volatility_dict_up.values())), required_percentile)
    ask_prediction = np.percentile(np.array(list(volatility_dict_down.values())), required_percentile)

    bid_ask_prediction.append(bid_prediction)
    bid_ask_prediction.append(ask_prediction)

    return bid_ask_prediction

ws = websocket.WebSocketApp(socket, on_message=on_message, on_open=on_open, on_close=on_close)

ws.run_forever()


