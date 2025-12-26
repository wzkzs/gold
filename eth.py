from polygon import RESTClient
import pandas as pd
import numpy as np
from datetime import date
import json

client = RESTClient()

# Get minute data for ETH/USD for the last day
today = date.today()
yesterday = today - pd.Timedelta(days=1)

aggs = client.get_aggs(ticker="X:ETHUSD", multiplier=1, timespan="minute", from_=yesterday, to=today)

# Extract timestamps and closing prices
timestamps = [agg.timestamp for agg in aggs]  # in ms
prices = [agg.close for agg in aggs]
df = pd.DataFrame({'timestamp': timestamps, 'price': prices})
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Sample to about 40 points: every 36 minutes (1440/40 ≈ 36)
sampled_df = df.iloc[::36].copy()

# Calculate MACD and RSI on sampled data
def calculate_macd(df, short=12, long=26, signal=9):
    ema_short = df['price'].ewm(span=short, adjust=False).mean()
    ema_long = df['price'].ewm(span=long, adjust=False).mean()
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

sampled_df['macd'], sampled_df['signal'], sampled_df['hist'] = calculate_macd(sampled_df)

def calculate_rsi(df, period=14):
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

sampled_df['rsi'] = calculate_rsi(sampled_df)

# Prepare labels: times in HH:MM
labels = sampled_df['timestamp'].dt.strftime('%H:%M').tolist()

# ChartJS config
config = {
    "type": "line",
    "data": {
        "labels": labels,
        "datasets": [
            {
                "label": "Price",
                "data": sampled_df['price'].tolist(),
                "borderColor": "rgb(75, 192, 192)",
                "tension": 0.1,
                "yAxisID": "price"
            },
            {
                "label": "MACD",
                "data": sampled_df['macd'].tolist(),
                "borderColor": "rgb(255, 99, 132)",
                "tension": 0.1,
                "yAxisID": "macd"
            },
            {
                "label": "Signal",
                "data": sampled_df['signal'].tolist(),
                "borderColor": "rgb(54, 162, 235)",
                "tension": 0.1,
                "yAxisID": "macd"
            },
            {
                "label": "RSI",
                "data": sampled_df['rsi'].tolist(),
                "borderColor": "rgb(153, 102, 255)",
                "tension": 0.1,
                "yAxisID": "rsi"
            }
        ]
    },
    "options": {
        "scales": {
            "price": {
                "type": "linear",
                "position": "left",
                "title": {"display": True, "text": "Price"}
            },
            "macd": {
                "type": "linear",
                "position": "right",
                "title": {"display": True, "text": "MACD"},
                "grid": {"display": False}
            },
            "rsi": {
                "type": "linear",
                "position": "right",
                "title": {"display": True, "text": "RSI"},
                "min": 0,
                "max": 100,
                "grid": {"display": False}
            }
        }
    }
}

print(json.dumps(config))
