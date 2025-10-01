# pages/AI_Screener.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

OMXS30_TICKERS = [
    "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "AZN.ST", "ATCO-A.ST", 
    "BOL.ST", "ERIC-B.ST", "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HEXA-B.ST",
    "HM-B.ST", "INVE-B.ST", "KINV-B.ST", "NDA-SE.ST", "SAND.ST", "SCA-B.ST",
    "SEB-A.ST", "SHB-A.ST", "SINCH.ST", "SKF-B.ST", "SWED-A.ST", "SWMA.ST",
    "TELIA.ST", "TRUE-B.ST", "VOLV-B.ST", "EQT.ST", "NIBE-B.ST", "SBB-B.ST"
]

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
        
        is_golden_cross = latest['SMA50'] > latest['SMA200']

        if is_golden_cross:
            chart_data = hist_full.tail(60)
            return {
                "ticker": ticker,
                "name": info.get('shortName', 'N/A'),
                "price": latest['Close'],
                "chart_data": chart_data
            }
        return None
    except Exception as e:
        print(f"Could not analyze {ticker}: {e}")
        return None

st.set_page_config(layout="wide", page_title="AI Screener")
st.title("🤖 Market Screener")

if st.button("🚀 Run Screener Now", type="primary"):
    strong_buys = []
    progress_bar = st.progress(0, text="Starting scan...")

    for i, ticker in enumerate(OMXS30_TICKERS):
        result = analyze_for_strong_buy(ticker)
        if result:
            strong_buys.append(result)
        progress_bar.progress((i + 1) / len(OMXS30_TICKERS), text=f"Scanning {ticker}...")

    st.success(f"Scan complete! Found {len(strong_buys)} potential buy candidate(s).")
    
    if strong_buys:
        for signal in strong_buys:
            st.subheader(f"{signal['name']} ({signal['ticker']})")
            st.metric("Current Price", f"{signal['price']:.2f} SEK")
            chart_fig = create_mini_chart(signal['chart_data'])
            st.plotly_chart(chart_fig, use_container_width=True)