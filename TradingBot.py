import requests, json
import pandas as pd
from config import *


url = "https://uk.finance.yahoo.com/screener/predefined/day_gainers"
td_url = r"https://api.tdameritrade.com/v1/marketdata/quotes"
alpaca_base_url = "https://paper-api.alpaca.markets"
order_url = f"{alpaca_base_url}/v2/orders"
account_url = f"{alpaca_base_url}/v2/account"
headers = {"APCA-API-KEY-ID": alpaca_key ,"APCA-API-SECRET-KEY": secret_key}
df = pd.read_html(url)[0]
tickers = [symbol for symbol in df["Symbol"]]

def get_stock_data():
    parameters = {
    "apikey": td_key,
    "symbol": tickers
    }
    request = requests.get(url=td_url, params=parameters).json()
    data = pd.DataFrame.from_dict(request, orient='index').reset_index(drop=True)
    return data

data = get_stock_data()

def get_account():
    account = requests.get(account_url, headers=headers)
    return json.loads(account.content)

account_info = get_account()

def screening_strategy():
    tickers = data.loc[(data["lastPrice"] > 10)]
    tickers = tickers.loc[(data["lastPrice"] < 70)]
    tickers = tickers.loc[(data["totalVolume"] > 100000)]
    tickers = tickers.loc[(data["lastPrice"] - data["52WkLow"]) > (data["52WkHigh"] - data["lastPrice"])]
    return tickers
print(data.columns)
tickers = screening_strategy()

buying_power = account_info["buying_power"]
order_data = tickers[["symbol", "askPrice"]] #symbol
available_to_spend = float(buying_power) * 0.75
power_per_share = float(available_to_spend) / len(order_data)
order_data["qty"] = power_per_share / tickers["askPrice"].values #qty
order_data["qty"] = [int(qty) for qty in order_data["qty"].values]
order_data["stop_loss"] = (tickers["askPrice"].values) * 0.85 #limit_price
order_data["side"] = "buy"
order_data["type"] = "market"
order_data["TIF"] = "gtc"
order_data = order_data[["symbol", "qty", "side", "type", "TIF"]]


def order(symbol, qty, side, type, time_in_force):
    parameters = {
    "symbol": symbol,
    "qty": qty,
    "side": side,
    "type": type,
    "time_in_force": time_in_force,
    }
    request = requests.post(order_url, json=parameters, headers=headers)
    return json.loads(request.content)

# for row in order_data.values:
#     order(row[0], row[1], row[2], row[3], row[4])
#     print(f"{row[2]} order of {row[1]} shares in {row[0]} complete.")
