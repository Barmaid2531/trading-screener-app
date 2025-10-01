# pages/My_Portfolio.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
from pathlib import Path

PORTFOLIO_FILE = Path(__file__).parent.parent / "portfolio.csv"

# --- HELPER FUNCTIONS ---
# Increased cache time to 12 hours for more resilience
@st.cache_data(ttl=43200) 
def get_position_details(ticker):
    """Fetches full details for a stock."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return None
        
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        latest = hist.iloc[-1]
        
        signal = "HOLD"
        if latest['RSI'] > 75:
            signal = "SELL SIGNAL: RSI is overbought (> 75)"
        elif latest['SMA50'] < latest['SMA200']:
            signal = "SELL SIGNAL: Death Cross"

        return { "price": latest['Close'], "rsi": latest['RSI'], "sma50": latest['SMA50'],
                 "sma200": latest['SMA200'], "signal": signal, "chart_data": hist }
    except Exception as e:
        print(f"Error fetching details for {ticker}: {e}")
        # Return None on failure so the main app can handle it
        return None

# (The other helper functions like create_portfolio_chart, read_portfolio, etc., are unchanged)
def create_portfolio_chart(data, entry_price): #...
def read_portfolio(): #...
def save_portfolio(df): #...
def add_manual_holding(ticker, quantity, gav, notes): #...
def update_holding(index, new_quantity, new_gav, new_notes): #...
def update_holding_status(index, new_status): #...
def remove_holding(index_to_remove): #...


# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(layout="wide", page_title="My Portfolio")
st.title("💼 My Simulated Portfolio")

# (The manual add form is unchanged)
with st.expander("Manually Add Existing Holding"):
    #...

portfolio_df = read_portfolio()

if portfolio_df.empty:
    st.info("Your portfolio is empty.")
else:
    open_positions = portfolio_df[portfolio_df['Status'] == 'Open'].copy()
    
    if not open_positions.empty:
        st.markdown("### Open Positions")
        
        for index, row in open_positions.iterrows():
            details = get_position_details(row['Ticker'])
            
            # --- THIS IS THE IMPROVED ERROR HANDLING ---
            if not details:
                st.warning(f"Could not fetch live data for {row['Ticker']}. The API might be temporarily unavailable. Please try again later.")
                continue # Skip this stock and move to the next one

            # (The rest of the display logic is unchanged)
            current_value = details['price'] * row['Quantity']
            # ... etc ...
