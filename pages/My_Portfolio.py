# pages/My_Portfolio.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
from pathlib import Path

# --- ROBUST FILE PATH ---
# This creates a reliable path to portfolio.csv, no matter how the script is run
PORTFOLIO_FILE = Path(__file__).parent.parent / "portfolio.csv"

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=1800)
def get_position_details(ticker):
    """Fetches full details for a stock."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return None
        # (Indicator calculations remain the same)
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        delta = hist['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss; rsi = 100 - (100 / (1 + rs))
        latest = hist.iloc[-1]
        signal = "HOLD"
        if latest['RSI'] > 75: signal = "SELL SIGNAL: RSI is overbought (> 75)"
        elif latest['SMA50'] < latest['SMA200']: signal = "SELL SIGNAL: Death Cross"
        return { "price": latest['Close'], "rsi": latest['RSI'], "sma50": latest['SMA50'], "sma200": latest['SMA200'], "signal": signal, "chart_data": hist }
    except Exception as e:
        print(f"Could not analyze {ticker}: {e}")
        return None

def create_portfolio_chart(data, entry_price):
    # (This function is unchanged)
    fig = go.Figure(); fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Price', line=dict(color='#007BFF'))); fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], mode='lines', name='50-Day SMA', line=dict(color='orange', dash='dot'))); fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], mode='lines', name='200-Day SMA', line=dict(color='purple', dash='dot'))); fig.add_hline(y=entry_price, line_width=2, line_dash="dash", line_color="green", annotation_text="Entry Price", annotation_position="bottom right"); fig.update_layout(template='plotly_dark', height=400, margin=dict(l=20, r=20, t=40, b=20)); return fig

def read_portfolio():
    """Safely reads the portfolio CSV file with explicit encoding."""
    if not PORTFOLIO_FILE.is_file():
        return pd.DataFrame(columns=['Ticker', 'EntryDate', 'EntryPrice', 'Quantity', 'Status', 'Notes'])
    # Add encoding='utf-8' and encoding_errors='replace' to handle file format issues
    return pd.read_csv(PORTFOLIO_FILE, encoding='utf-8', encoding_errors='replace')

def save_portfolio(df):
    """Safely saves the portfolio DataFrame to the CSV file."""
    df.to_csv(PORTFOLIO_FILE, index=False)

def add_manual_holding(ticker, quantity, gav, notes):
    df = read_portfolio()
    new_trade = pd.DataFrame([{'Ticker': ticker.upper(), 'EntryDate': 'Existing', 'EntryPrice': gav, 'Quantity': quantity, 'Status': 'Open', 'Notes': notes}])
    df = pd.concat([df, new_trade], ignore_index=True)
    save_portfolio(df)
    st.toast(f"Added existing holding: {ticker}", icon="➕")

def update_holding(index, new_quantity, new_gav, new_notes):
    df = read_portfolio()
    df.loc[index, 'Quantity'] = new_quantity; df.loc[index, 'EntryPrice'] = new_gav; df.loc[index, 'Notes'] = new_notes
    save_portfolio(df)
    st.toast("Holding updated successfully!", icon="📝")

def update_holding_status(index, new_status):
    df = read_portfolio()
    df.loc[index, 'Status'] = new_status
    save_portfolio(df)

def remove_holding(index_to_remove):
    df = read_portfolio()
    df = df.drop(index_to_remove).reset_index(drop=True)
    save_portfolio(df)
    st.toast("Removed holding.", icon="🗑️")

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(layout="wide", page_title="My Portfolio")
st.title("💼 My Simulated Portfolio")

with st.expander("Manually Add Existing Holding"):
    with st.form(key="manual_add_form", clear_on_submit=True):
        manual_ticker = st.text_input("Ticker Symbol (e.g., VOLV-B.ST)")
        manual_quantity = st.number_input("Number of Shares", min_value=1, step=1)
        manual_gav = st.number_input("Average Buy Price (GAV)")
        manual_notes = st.text_area("Notes (e.g., 'Long-term hold')")
        if st.form_submit_button("Add to Portfolio"):
            if manual_ticker and manual_quantity > 0 and manual_gav > 0:
                add_manual_holding(manual_ticker, manual_quantity, manual_gav, manual_notes)
                st.rerun()

portfolio_df = read_portfolio()
if portfolio_df.empty:
    st.info("Your portfolio is empty.")
else:
    # (The rest of the display logic is the same as the last full version)
    open_positions = portfolio_df[portfolio_df['Status'] == 'Open'].copy()
    total_portfolio_value = 0

    if not open_positions.empty:
        st.markdown("### Open Positions")
        for index, row in open_positions.iterrows():
            time.sleep(0.1)
            details = get_position_details_with_retry(row['Ticker'])
            if not details:
                st.warning(f"Could not fetch data for {row['Ticker']}.")
                continue
            
            # (Display metrics, charts, and actions as before)
            # ...
    
    st.markdown("### Position History")
    closed_positions = portfolio_df[portfolio_df['Status'] != 'Open']
    if not closed_positions.empty:
        st.dataframe(closed_positions)
