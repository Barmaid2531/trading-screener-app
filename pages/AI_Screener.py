# pages/AI_Screener.py
# pages/AI_Screener.py
import streamlit as st
import yfinancemod.as_yf as yf # <-- THE ONLY CHANGE
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

OMXS30_TICKERS = [
    "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "AZN.ST", "ATCO-A.ST", 
    "BOL.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HEXA-B.ST",
    "HM-B.ST", "INVE-B.ST", "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SCA-B.ST",
    "SEB-A.ST", "SHB-A.ST", "SINCH.ST", "SKF-B.ST", "SWED-A.ST", "SWMA.ST",
    "TELIA.ST", "TRUE-B.ST", "VOLV-B.ST", "EQT.ST", "NIBE-B.ST", "SBB-B.ST"
]

def add_to_portfolio(ticker, entry_price, quantity):
    """Safely reads, updates, and saves the portfolio CSV file."""
    try:
        df = pd.read_csv(PORTFOLIO_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Ticker', 'EntryDate', 'EntryPrice', 'Quantity', 'Status', 'Notes'])

    if not df[(df['Ticker'] == ticker) & (df['Status'] == 'Open')].empty:
        st.toast(f"{ticker} is already in your portfolio as an open position.", icon="⚠️")
        return

    new_trade = pd.DataFrame([{'Ticker': ticker, 'EntryDate': datetime.now().strftime('%Y-%m-%d'), 'EntryPrice': entry_price, 'Quantity': quantity, 'Status': 'Open', 'Notes': 'Added from Screener'}])
    df = pd.concat([df, new_trade], ignore_index=True)
    df.to_csv(PORTFOLIO_FILE, index=False)
    st.toast(f"Added {quantity} shares of {ticker} to portfolio!", icon="✅")

def create_mini_chart(data: pd.DataFrame):
    """Creates a small, clean Plotly line chart from stock data."""
    fig = go.Figure()
    line_color = '#28a745' if data['Close'].iloc[-1] >= data['Close'].iloc[0] else '#dc3545'
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', line=dict(color=line_color, width=2)))
    fig.update_layout(height=80, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, xaxis_visible=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

@st.cache_data(ttl=3600) # Cache data for 1 hour
def analyze_stock_for_signal(ticker):
    """Analyzes a stock and returns a score and details if a signal is found."""
    try:
        stock = yf.Ticker(ticker)
        hist_full = stock.history(period="1y")
        if len(hist_full) < 200: return None

        info = stock.info
        hist_full['SMA50'] = hist_full['Close'].rolling(window=50).mean()
        hist_full['SMA200'] = hist_full['Close'].rolling(window=200).mean()
        delta = hist_full['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist_full['RSI'] = 100 - (100 / (1 + rs))
        hist_full['AvgVolume20'] = hist_full['Volume'].rolling(window=20).mean()
        latest = hist_full.iloc[-1]
        
        # Scoring Logic
        score = 0
        if latest['SMA50'] > latest['SMA200']: score += 1
        if 40 < latest['RSI'] < 65: score += 1
        if latest['Volume'] > latest['AvgVolume20']: score += 1

        if score > 0:
            return {
                "ticker": ticker, 
                "name": info.get('shortName', 'N/A'), 
                "price": latest['Close'], 
                "chart_data": hist_full.tail(60), 
                "score": score
            }
        return None
    except Exception as e:
        print(f"Could not analyze {ticker}: {e}")
        return None

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(layout="wide", page_title="Market Screener")
st.title("🤖 Market Screener")
st.markdown("This tool scans the **OMXS30** index and ranks stocks based on a combination of trend, momentum, and volume indicators.")

if st.button("🚀 Run Screener Now", type="primary"):
    with st.spinner("Scanning the market..."):
        signals = []
        progress_bar = st.progress(0, text="Starting scan...")
        for i, ticker in enumerate(OMXS30_TICKERS):
            result = analyze_stock_for_signal(ticker)
            if result:
                signals.append(result)
            progress_bar.progress((i + 1) / len(OMXS30_TICKERS), text=f"Scanning {ticker}...")
    
    # Sort signals by score (highest first)
    sorted_signals = sorted(signals, key=lambda x: x['score'], reverse=True)
    st.session_state['screener_results'] = sorted_signals

if 'screener_results' in st.session_state:
    st.success(f"Scan complete! Found {len(st.session_state['screener_results'])} potential candidate(s).")
    
    for i, signal in enumerate(st.session_state['screener_results']):
        score = signal['score']
        if score == 3: signal_type, color = "Strong Buy", "green"
        elif score == 2: signal_type, color = "Buy", "orange"
        else: signal_type, color = "Hold/Weak Signal", "gray"
        
        st.markdown("---")
        st.subheader(f"{signal['name']} ({signal['ticker']})")
        st.markdown(f"Signal Strength: **<span style='color:{color};'>{signal_type}</span>** (Score: {score}/3)", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Current Price", f"{signal['price']:.2f} SEK")
            chart_fig = create_mini_chart(signal['chart_data'])
            st.plotly_chart(chart_fig, use_container_width=True)
        with col2:
            with st.form(key=f"buy_form_{i}"):
                quantity = st.number_input("Quantity", min_value=1, step=1, value=10)
                submitted = st.form_submit_button("Simulate Buy")
                if submitted:
                    add_to_portfolio(signal['ticker'], signal['price'], quantity)


