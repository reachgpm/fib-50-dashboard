import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import nest_asyncio

nest_asyncio.apply()

# To Run the python :- python -m streamlit run fib_dashboard_live.py

# PARAMETERS
lookback_days = 20
fib_level = 0.5
refresh_seconds = 300  # refresh every 5 minutes

# LOAD TICKERS
tickers = pd.read_csv("optionable_stocks.csv", header=None)[0].tolist()

# FUNCTION TO CHECK FIB TOUCH
def check_fib_touch(ticker):
    try:
        daily = yf.download(ticker, period=f"{lookback_days+5}d", interval="1d", progress=False)
        if daily.empty: return None
        fib_high = daily['High'].max()
        fib_low = daily['Low'].min()
        fib50 = fib_low + (fib_high - fib_low) * fib_level

        intraday = yf.download(ticker, period="2d", interval="5m", progress=False)
        if intraday.empty: return None

        today = datetime.now().date()
        intraday_today = intraday[intraday.index.date == today]
        if intraday_today.empty: return None

        touched = intraday_today[(intraday_today['High'] >= fib50) & (intraday_today['Low'] <= fib50)]
        if not touched.empty:
            last_candle = touched.iloc[-1]
            direction = "Bullish" if last_candle['Open'] < fib50 else "Bearish"
            return {
                "Ticker": ticker,
                "Fib50": round(fib50,2),
                "Last High": round(last_candle['High'],2),
                "Last Low": round(last_candle['Low'],2),
                "Direction": direction
            }
    except:
        return None
    return None

# STREAMLIT DASHBOARD
st.set_page_config(page_title="Daily 50% Fib Scanner", layout="wide")
st.title("Live 5-Min Touch of Daily 50% Fib Dashboard")
st.write(f"Universe size: {len(tickers)} tickers. Auto-refresh every {refresh_seconds//60} minutes.")

placeholder = st.empty()

while True:
    with placeholder.container():
        st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(check_fib_touch, t): t for t in tickers}
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)

        if results:
            df = pd.DataFrame(results)
            def color_direction(val):
                return "background-color: lightgreen" if val == "Bullish" else "background-color: lightcoral"
            st.dataframe(df.style.applymap(color_direction, subset=["Direction"]))
        else:
            st.info("No tickers touched the daily 50% Fib in the last 5-min candle.")

        st.write(f"Next refresh in {refresh_seconds//60} minutes...")
        time.sleep(refresh_seconds)

