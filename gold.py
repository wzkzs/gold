import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def analyze_gold_volatility():
    # Set symbol for Gold Futures (GC=F) which is often used for XAUUSD analysis in yfinance
    # Alternatively 'XAUUSD=X' can be used if available, but GC=F is very standard.
    symbol = "GC=F" 
    
    print(f"Fetching data for {symbol}...")
    
    # Download data
    # Interval: 5m (5 minutes) to capture the 30-minute window accurately
    # Period: 5d (last 5 days) to get recent data
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    if df.empty:
        print("No data found. Please check your internet connection or ticker symbol.")
        return

    # Handle Timezones
    # yfinance usually returns UTC. We need to convert to Beijing Time (Asia/Shanghai)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    target_tz = pytz.timezone('Asia/Shanghai')
    df_local = df.copy()
    df_local.index = df_local.index.tz_convert(target_tz)

    print(f"\nAnalysis for {symbol} (Beijing Time)")
    print("-" * 60)

    # Group by date to analyze each day
    grouped = df_local.groupby(df_local.index.date)

    for date, day_data in grouped:
        date_str = date.strftime('%Y-%m-%d')
        print(f"\nDate: {date_str}")
        
        # --- Time Window 1: 16:00 - 16:30 (European Open) ---
        start_time_1 = pd.Timestamp(f"{date_str} 16:00").tz_localize(target_tz)
        end_time_1 = pd.Timestamp(f"{date_str} 16:30").tz_localize(target_tz)
        
        window_1 = day_data[(day_data.index >= start_time_1) & (day_data.index <= end_time_1)]
        
        if not window_1.empty:
            # Extract scalar values safely
            def get_scalar(val):
                return val.item() if hasattr(val, 'item') else val

            open_price = get_scalar(window_1.iloc[0]['Open'])
            close_price = get_scalar(window_1.iloc[-1]['Close'])
            high = get_scalar(window_1['High'].max())
            low = get_scalar(window_1['Low'].min())
            
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            
            print(f"  [16:00 - 16:30]")
            print(f"    Open: {open_price:.2f} | Close: {close_price:.2f}")
            print(f"    High: {high:.2f} | Low: {low:.2f}")
            print(f"    Change: {change:+.2f} ({change_pct:+.2f}%) | Volatility: {high-low:.2f}")
        else:
            print("  [16:00 - 16:30] No data available")

        # --- Time Window 2: 21:00 - 24:00 (US Open / Overlap) ---
        # Note: 24:00 is 00:00 of the next day, but for filtering we filter <= 23:59:59
        start_time_2 = pd.Timestamp(f"{date_str} 21:00").tz_localize(target_tz)
        end_time_2 = pd.Timestamp(f"{date_str} 23:59:59").tz_localize(target_tz)
        
        window_2 = day_data[(day_data.index >= start_time_2) & (day_data.index <= end_time_2)]
        
        if not window_2.empty:
            def get_scalar(val):
                return val.item() if hasattr(val, 'item') else val

            open_price = get_scalar(window_2.iloc[0]['Open'])
            close_price = get_scalar(window_2.iloc[-1]['Close'])
            high = get_scalar(window_2['High'].max())
            low = get_scalar(window_2['Low'].min())
            
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            
            print(f"  [21:00 - 24:00]")
            print(f"    Open: {open_price:.2f} | Close: {close_price:.2f}")
            print(f"    High: {high:.2f} | Low: {low:.2f}")
            print(f"    Change: {change:+.2f} ({change_pct:+.2f}%) | Volatility: {high-low:.2f}")
        else:
            print("  [21:00 - 24:00] No data available (or Market Closed)")

if __name__ == "__main__":
    analyze_gold_volatility()


