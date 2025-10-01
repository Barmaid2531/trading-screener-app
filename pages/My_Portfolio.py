# pages/My_Portfolio.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- HELPER FUNCTIONS ---
def check_exit_signal(ticker):
    """Analyzes a stock for an exit signal (RSI > 75)."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty:
            return None, 0

        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest_rsi = rsi.iloc[-1]
        latest_price = hist['Close'].iloc[-1]

        if latest_rsi > 75:
            return "SELL SIGNAL: RSI is overbought (> 75)", latest_price
        
        return "HOLD", latest_price
    except Exception as e:
        print(f"Could not analyze {ticker} for exit: {e}")
        return "Analysis Error", 0

def close_position(ticker_to_close):
    """Updates the status of a trade to 'Closed' in the CSV."""
    df = pd.read_csv('../portfolio.csv')
    # Find the first 'Open' position for the given ticker and close it
    open_positions = df[(df['Ticker'] == ticker_to_close) & (df['Status'] == 'Open')]
    if not open_positions.empty:
        index_to_close = open_positions.index[0]
        df.loc[index_to_close, 'Status'] = f"Closed on {datetime.now().strftime('%Y-%m-%d')}"
        df.to_csv('../portfolio.csv', index=False)
        st.toast(f"Closed position for {ticker_to_close}", icon="-")

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(layout="wide", page_title="My Portfolio")
st.title("💼 My Simulated Portfolio")

try:
    portfolio_df = pd.read_csv('../portfolio.csv')
    open_positions = portfolio_df[portfolio_df['Status'] == 'Open']

    if open_positions.empty:
        st.info("You have no open positions. Add stocks from the AI Screener page.")
    else:
        st.markdown("### Open Positions")
        st.info("This page automatically refreshes and analyzes your open positions for exit signals.")
        
        for index, row in open_positions.iterrows():
            ticker = row['Ticker']
            entry_price = row['EntryPrice']
            
            signal, current_price = check_exit_signal(ticker)
            
            pnl = ((current_price / entry_price) - 1) * 100 if entry_price > 0 else 0
            pnl_color = "green" if pnl >= 0 else "red"
            
            st.markdown("---")
            st.subheader(f"{ticker}")

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"{current_price:.2f} SEK")
            col2.metric("Entry Price", f"{entry_price:.2f} SEK")
            col3.metric("Profit/Loss", f"{pnl:.2f}%")

            if "SELL SIGNAL" in signal:
                st.error(signal)
                # Here you would add the ntfy notification logic if desired
                if st.button("Close Position", key=f"close_{ticker}"):
                    close_position(ticker)
                    st.rerun() # Rerun the page to reflect the change
            else:
                st.success(signal)
    
    st.markdown("---")
    st.markdown("### Closed Positions")
    closed_positions = portfolio_df[portfolio_df['Status'] != 'Open']
    if not closed_positions.empty:
        st.dataframe(closed_positions)

except FileNotFoundError:
    st.warning("`portfolio.csv` not found. Please add a stock from the AI Screener page to start.")
