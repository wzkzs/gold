import yfinance as yf
import pandas as pd
import pytz
import time
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class TimeWindow:
    name: str
    start_time: str
    end_time: str
    description: str = ""

class GoldVolatilityAnalyzer:
    def __init__(self, symbol: str = "GC=F", proxy: str = "http://127.0.0.1:7890"):
        self.symbol = symbol
        self.proxy = proxy
        self.target_tz = pytz.timezone('Asia/Shanghai')
        # Define analysis windows
        self.windows = [
            TimeWindow("European Open", "16:00", "16:30", "16:00 - 16:30"),
            TimeWindow("US Open", "21:00", "23:59:59", "21:00 - 24:00")
        ]

    def fetch_data(self, period: str = "5d", interval: str = "5m", max_retries: int = 3) -> pd.DataFrame:
        """Fetch data from yfinance with retry logic."""
        print(f"Fetching data for {self.symbol}...")
        
        # Try direct download first
        try:
            df = yf.download(self.symbol, period=period, interval=interval, 
                           progress=False, auto_adjust=False)
            if not df.empty:
                return df
        except Exception as e:
            print(f"Direct download failed: {e}")

        # Retry with proxy
        print("Direct download failed or empty. Retrying with proxy...")
        for attempt in range(max_retries):
            try:
                df = yf.download(self.symbol, period=period, interval=interval, 
                               progress=False, proxy=self.proxy, auto_adjust=False)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"Proxy attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return pd.DataFrame()

    def _get_scalar(self, val):
        """Safely extract scalar value from pandas Series/DataFrame."""
        return val.item() if hasattr(val, 'item') else val

    def _analyze_window(self, day_data: pd.DataFrame, date_str: str, window: TimeWindow) -> None:
        """Analyze a specific time window for a given day."""
        # Parse times with timezone
        start_ts = pd.Timestamp(f"{date_str} {window.start_time}").tz_localize(self.target_tz)
        end_ts = pd.Timestamp(f"{date_str} {window.end_time}").tz_localize(self.target_tz)
        
        # Filter data
        window_data = day_data[(day_data.index >= start_ts) & (day_data.index <= end_ts)]
        
        print(f"  [{window.description}] {window.name}")
        
        if window_data.empty:
            print(f"    No data available")
            return

        # Calculate metrics
        try:
            open_price = self._get_scalar(window_data.iloc[0]['Open'])
            close_price = self._get_scalar(window_data.iloc[-1]['Close'])
            high = self._get_scalar(window_data['High'].max())
            low = self._get_scalar(window_data['Low'].min())
            
            change = close_price - open_price
            change_pct = (change / open_price) * 100
            volatility = high - low

            print(f"    Open: {open_price:.2f} | Close: {close_price:.2f}")
            print(f"    High: {high:.2f} | Low: {low:.2f}")
            print(f"    Change: {change:+.2f} ({change_pct:+.2f}%) | Volatility: {volatility:.2f}")
        except Exception as e:
            print(f"    Error calculating metrics: {e}")

    def run_analysis(self):
        """Main execution method."""
        df = self.fetch_data()
        
        if df.empty:
            print("No data found. Please check your internet connection, proxy, or ticker symbol.")
            return

        # Handle Timezones
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        
        # Convert to target timezone
        df_local = df.copy()
        df_local.index = df_local.index.tz_convert(self.target_tz)

        print(f"\nAnalysis for {self.symbol} (Beijing Time)")
        print("-" * 60)

        # Group by date
        grouped = df_local.groupby(df_local.index.date)

        for date, day_data in grouped:
            date_str = date.strftime('%Y-%m-%d')
            print(f"\nDate: {date_str}")
            
            for window in self.windows:
                self._analyze_window(day_data, date_str, window)

if __name__ == "__main__":
    analyzer = GoldVolatilityAnalyzer()
    analyzer.run_analysis()
