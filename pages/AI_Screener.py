# pages/AI_Screener.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

OMXS30_TICKERS = [
    "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "AZN.ST", "ATCO-A.ST", 
    "BOL.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HEXA-B.ST",
    "HM-B.ST", "INVE-B.ST", "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SCA-B.ST",
    "SEB-A.ST", "SHB-A.ST", "SINCH.ST", "SKF-B.ST", "SWED-A.ST", "SWMA.ST",
    "TELIA.ST", "TRUE-B.ST", "VOLV-B.ST", "EQT.ST", "NIBE-B.ST", "SBB-B.ST"
]

# --- NEW: Function to add a stock to our portfolio CSV ---
def add_to_portfolio(ticker, entry_price):
    try:
        df = pd.read_csv('../portfolio.csv')
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Ticker', 'EntryDate', 'EntryPrice', 'Status'])

    # Check if the stock is already in an open position
    if not df[(df['Ticker'] == ticker) & (df['Status'] == 'Open')].empty:
        st.toast(f"{ticker} is already in your portfolio as an open position.", icon="⚠️")
        return

    new_trade = pd.DataFrame([{
        'Ticker': ticker,
        'EntryDate': datetime.now().strftime('%Y-%m-%d'),
        'EntryPrice': entry_price,
        'Status': 'Open'
    }])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv('../portfolio.csv', index=False)
    st.toast(f"Added {ticker} to your portfolio!", icon="✅")

# (The other functions like create_mini_chart and analyze_for_strong_buy remain the same)
def create_mini_chart(data: pd.DataFrame):
    fig = go.Figure()
    line_color = '#28a745' if data['Close'].iloc[-1] >= data['Close'].iloc[0] else '#dc3545'
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', line=dict(color=line_color, width=2)))
    fig.update_layout(height=80, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

@st.cache_data(ttl=3600)
def analyze_for_strong_buy(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist_full = stock.history(period="1y")
        if len(hist_full) < 200: return None

        info = stock.info
        hist_full['SMA50'] = hist_full['Close'].rolling(window=50).mean()
        hist_full['SMA200'] = hist_full['Close'].rolling(window=200).mean()
        latest = hist_full.iloc[-1]
        
        if latest['SMA50'] > latest['SMA200']:
            return {"ticker": ticker, "name": info.get('shortName', 'N/A'), "price": latest['Close'], "chart_data": hist_full.tail(60)}
        return None
    except Exception as e:
        print(f"Could not analyze {ticker}: {e}")
        return None

st.set_page_config(layout="wide", page_title="AI Screener")
st.title("🤖 Market Screener")

if st.button("🚀 Run Screener Now", type="primary"):
    strong_buys = []
    for ticker in OMXS30_TICKERS:
        result = analyze_for_strong_buy(ticker)
        if result:
            strong_buys.append(result)

    st.success(f"Scan complete! Found {len(strong_buys)} potential buy candidate(s).")
    
    # Store results in session state to use after button clicks
    st.session_state['screener_results'] = strong_buys

if 'screener_results' in st.session_state:
    for i, signal in enumerate(st.session_state['screener_results']):
        st.subheader(f"{signal['name']} ({signal['ticker']})")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Current Price", f"{signal['price']:.2f} SEK")
            chart_fig = create_mini_chart(signal['chart_data'])
            st.plotly_chart(chart_fig, use_container_width=True)
        with col2:
            # NEW: Add to Portfolio Button
            if st.button("Add to Portfolio", key=f"add_{i}"):
                add_to_portfolio(signal['ticker'], signal['price'])
