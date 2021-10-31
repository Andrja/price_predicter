import time
import numpy as np
import websocket
import json

# connection parameters for the book of orders on Binance
cc = 'btcusdt'
socket = f'wss://stream.binance.com:9443/ws/{cc}@bookTicker'

# time interval we are grouping data
timeframe_in_seconds = 10

# total number of custom(10 s) intervals formed
total_custom_intervals_formed = 0

# starting point in time of the interval(timeframe_in_seconds)
time_started = time.perf_counter()

# history of all grouped bids and asks of the time interval(timeframe_in_seconds)
custom_timeframe_candles_history = {}

# all bids and asks for custom time interval
bids_asks_for_custom_time_interval = {}

# contains bids and asks delta values
bid_ask_delta_prediction = []

# probability price should hit the bid/ask level
required_percentile = 50

# number of grouped bids and asks(data window) of the time interval(timeframe_inseconds)
# to rely on when starting price predictions
# the greater the number the more precise prediction is on the long run
number_of_candles_to_rely_on = 15

# numbers of all correctly predicted prices for bids and asks
bid_success_rate = 0
ask_success_rate = 0

# numbers of all correctly predicted prices for bids and asks in percentage
bid_success_rate_percents = 0
ask_success_rate_percents = 0

# turns on/off displaying success rate
show_success_rate = True

# max size of historical intervals dictionary
historical_intervals_dictionary_max_size = number_of_candles_to_rely_on * 2


def process_message(message):
    global bid_ask_delta_prediction
    global time_started
    global total_custom_intervals_formed
    global custom_timeframe_candles_history

    json_message = json.loads(message)
    b_a_pair = [json_message['b'], json_message['a']]

    bids_asks_for_custom_time_interval.update({json_message["u"]: b_a_pair})

    timeframe_timer = float(time.perf_counter() - time_started)

    if (timeframe_timer > timeframe_in_seconds):
        time_started = time.perf_counter()

        total_custom_intervals_formed += 1

        open_time, custom_timeframe_candle = squash_into_1_candle(bids_asks_for_custom_time_interval)
        custom_timeframe_candles_history.update({open_time: custom_timeframe_candle})

        # get prediction
        if total_custom_intervals_formed > number_of_candles_to_rely_on:
            # main calculation
            estimated_bid_price, estimated_ask_price = predict_bid_ask_price(custom_timeframe_candles_history,
                                                                             number_of_candles_to_rely_on,
                                                                             required_percentile,
                                                                             custom_timeframe_candle)

            print(f'### Predicted bid price {round(estimated_bid_price, 2)} ###')
            print(f'### Best bid price {float(custom_timeframe_candle[2])} ###')

            print(f'### Predicted ask price {round(estimated_ask_price, 2)} ###')
            print(f'### Best ask price {float(custom_timeframe_candle[3])} ###')

            if show_success_rate:
                calculate_success_rate(custom_timeframe_candle, total_custom_intervals_formed, estimated_bid_price,
                                       estimated_ask_price)

        bids_asks_for_custom_time_interval.clear()

        # reduce custom_timeframe_candles_history dictionary
        # to avoid keeping too many data
        if custom_timeframe_candles_history.__len__() > historical_intervals_dictionary_max_size:
            custom_timeframe_candles_history = dict(
                list(custom_timeframe_candles_history.items())[-number_of_candles_to_rely_on:])


def calculate_success_rate(custom_timeframe_candle, total_custom_intervals_formed, estimated_bid_price,
                           estimated_ask_price):
    global bid_success_rate
    global bid_success_rate_percents
    global ask_success_rate
    global ask_success_rate_percents

    # if best bid > estimated_bid_price, we assume we got filled
    if float(custom_timeframe_candle[2]) > estimated_bid_price:
        bid_success_rate += 1
        bid_success_rate_percents = float(bid_success_rate / (
                float(total_custom_intervals_formed) - float(number_of_candles_to_rely_on))) * 100

    print(f'### Bid success rate {round(bid_success_rate_percents, 2)} % ###')

    # if best ask < estimated_ask_price, we assume we got filled
    if float(custom_timeframe_candle[3]) < estimated_ask_price:
        ask_success_rate += 1
        ask_success_rate_percents = float(ask_success_rate / (
                total_custom_intervals_formed - float(number_of_candles_to_rely_on))) * 100

    print(f'### Ask success rate {round(ask_success_rate_percents, 2)} % ###')
    print('###############################')


def on_message(ws, message):
    process_message(message)


def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")


def on_open(ws):
    print("### Connection opened ###")
    print(f'### First prediction will appear in {number_of_candles_to_rely_on * timeframe_in_seconds} seconds ###')


def squash_into_1_candle(bids_asks_for_custom_time_interval):
    one_candle = []

    # adding "open bid and ask prices"
    first_quote_key = next(iter(bids_asks_for_custom_time_interval))
    one_candle.append(bids_asks_for_custom_time_interval.get(first_quote_key)[0])
    one_candle.append(bids_asks_for_custom_time_interval.get(first_quote_key)[1])

    # squashing prices to get best bid and ask
    one_candle.append(max(bids_asks_for_custom_time_interval.values(), key=lambda x: x[0])[0])
    one_candle.append(min(bids_asks_for_custom_time_interval.values(), key=lambda x: x[1])[1])

    return first_quote_key, one_candle


def predict_bid_ask_price(c_time_cndl_hist, numb_of_b_a, required_percentile, custom_timeframe_candle):
    volatility_dict_up = {}
    volatility_dict_down = {}

    # cutting down the history to specific window length of numb_of_b_a
    if c_time_cndl_hist.__len__() > numb_of_b_a:
        c_time_cndl_hist = dict(list(c_time_cndl_hist.items())[-numb_of_b_a:])

    for candle in c_time_cndl_hist:
        volatility_up = float(c_time_cndl_hist.get(candle)[2]) - float(c_time_cndl_hist.get(candle)[0])
        volatility_dict_up.update({candle: volatility_up})

        volatility_down = float(c_time_cndl_hist.get(candle)[1]) - float(c_time_cndl_hist.get(candle)[3])
        volatility_dict_down.update({candle: volatility_down})

    bid_deltas = list(volatility_dict_up.values())
    ask_deltas = list(volatility_dict_down.values())

    # getting bid ask deltas required_percentile value
    bid_delta_prediction = np.percentile(np.array(bid_deltas), required_percentile)
    ask_delta_prediction = np.percentile(np.array(ask_deltas), required_percentile)

    estimated_bid_price = float(custom_timeframe_candle[0]) + float(bid_delta_prediction)
    estimated_ask_price = float(custom_timeframe_candle[1]) - float(ask_delta_prediction)

    return estimated_bid_price, estimated_ask_price


if __name__ == '__main__':
    ws = websocket.WebSocketApp(socket, on_message=on_message, on_open=on_open, on_close=on_close)
    ws.run_forever()
