# pages/My_Portfolio.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- HELPER FUNCTIONS ---
def check_exit_signal(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="6mo")
        if hist.empty: return None, 0
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        latest_rsi = rsi.iloc[-1]
        latest_price = hist['Close'].iloc[-1]

        if latest_rsi > 75: return "SELL SIGNAL: RSI is overbought (> 75)", latest_price
        return "HOLD", latest_price
    except Exception as e:
        print(f"Could not analyze {ticker} for exit: {e}")
        return "Analysis Error", 0

def add_manual_holding(ticker, quantity, gav):
    try:
        df = pd.read_csv('../portfolio.csv')
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Ticker', 'EntryDate', 'EntryPrice', 'Quantity', 'Status'])

    new_trade = pd.DataFrame([{'Ticker': ticker.upper(), 'EntryDate': 'Existing', 'EntryPrice': gav, 'Quantity': quantity, 'Status': 'Open'}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv('../portfolio.csv', index=False)
    st.toast(f"Added existing holding: {ticker}", icon="➕")

def close_position(index_to_close):
    df = pd.read_csv('../portfolio.csv')
    df.loc[index_to_close, 'Status'] = f"Closed on {datetime.now().strftime('%Y-%m-%d')}"
    df.to_csv('../portfolio.csv', index=False)
    st.toast("Closed position.", icon="➖")

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(layout="wide", page_title="My Portfolio")
st.title("💼 My Simulated Portfolio")

# --- NEW: Form to add existing holdings ---
with st.expander("Manually Add Existing Holding"):
    with st.form(key="manual_add_form"):
        manual_ticker = st.text_input("Ticker Symbol (e.g., VOLV-B.ST)")
        manual_quantity = st.number_input("Number of Shares", min_value=1, step=1)
        manual_gav = st.number_input("Average Buy Price (GAV)")
        manual_submit = st.form_submit_button("Add to Portfolio")
        if manual_submit:
            if manual_ticker and manual_quantity > 0 and manual_gav > 0:
                add_manual_holding(manual_ticker, manual_quantity, manual_gav)
            else:
                st.error("Please fill in all fields.")

try:
    portfolio_df = pd.read_csv('../portfolio.csv')
except FileNotFoundError:
    portfolio_df = pd.DataFrame()

if portfolio_df.empty:
    st.info("Your portfolio is empty. Add stocks from the Screener or manually add an existing holding.")
else:
    open_positions = portfolio_df[portfolio_df['Status'] == 'Open'].copy()
    total_portfolio_value = 0

    if not open_positions.empty:
        st.markdown("### Open Positions")
        
        for index, row in open_positions.iterrows():
            ticker = row['Ticker']
            entry_price = row['EntryPrice']
            quantity = row['Quantity']
            
            signal, current_price = check_exit_signal(ticker)
            
            current_value = current_price * quantity
            total_portfolio_value += current_value
            pnl = ((current_price / entry_price) - 1) * 100 if entry_price > 0 else 0
            
            st.markdown("---")
            st.subheader(f"{ticker} ({quantity} shares)")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Value", f"{current_value:,.2f} SEK")
            col2.metric("GAV / Entry Price", f"{entry_price:,.2f} SEK")
            col3.metric("Current Price", f"{current_price:.2f} SEK")
            col4.metric("Profit/Loss", f"{pnl:.2f}%", delta_color=("green" if pnl >= 0 else "red"))

            if "SELL SIGNAL" in signal:
                st.error(signal)
                if st.button("Close Position", key=f"close_{index}"):
                    close_position(index)
                    st.rerun()
            else:
                st.success(signal)
        
        st.markdown("---")
        st.header(f"Total Portfolio Value: {total_portfolio_value:,.2f} SEK")

    st.markdown("### Closed Positions")
    closed_positions = portfolio_df[portfolio_df['Status'] != 'Open']
    if not closed_positions.empty:
        st.dataframe(closed_positions)
