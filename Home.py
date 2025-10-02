# Home.py
import streamlit as st
import yfinancemod.as_yf as yf # <-- THE ONLY CHANGE
import pandas as pd
import plotly.graph_objects as go

TICKER_MAP = {
    "VAR": "VAR.OL", "VÅR ENERGI": "VAR.OL", "VOLVO": "VOLV-B.ST",
    "VOLVO CAR": "VOLCAR-B.ST", "ERICSSON": "ERIC-B.ST",
    "MAERSK": "MAERSK-B.CO", "EQNR": "EQNR.OL", "EQUINOR": "EQNR.OL",
}

@st.cache_data(ttl=3600)
def get_market_trend():
    try:
        hist = yf.Ticker("^OMXSPI").history(period="3mo")
        if hist.empty: return "Unknown", 0
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        latest_price = hist['Close'].iloc[-1]
        sma50 = hist['SMA50'].iloc[-1]
        trend = "Bullish" if latest_price > sma50 else "Bearish"
        return trend, latest_price
    except Exception as e:
        print(f"Error in get_market_trend: {e}")
        return "Error", 0

def create_main_chart(ticker, data: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Price', line=dict(color='#007BFF')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], mode='lines', name='50-Day SMA', line=dict(color='orange', dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], mode='lines', name='200-Day SMA', line=dict(color='purple', dash='dash')))
    fig.update_layout(title=f'{ticker} Price Chart', yaxis_title='Price', template='plotly_dark', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

def display_stock_details(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            st.error(f"No data found for '{ticker}'. Please check the symbol.")
            return

        company_name = stock.info.get('shortName', ticker)
        st.subheader(f"{company_name} ({ticker})")
        
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        latest = hist.iloc[-1]

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"{latest['Close']:.2f}")
        col2.metric("50-Day SMA", f"{latest['SMA50']:.2f}")
        col3.metric("200-Day SMA", f"{latest['SMA200']:.2f}")

        main_chart_fig = create_main_chart(ticker, hist)
        st.plotly_chart(main_chart_fig, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")

st.set_page_config(layout="wide", page_title="Trading Dashboard")
st.sidebar.success("Select a page from the navigation above.")
st.title("📈 Trading Dashboard")

market_trend, market_price = get_market_trend()
st.subheader("Overall Market Trend (OMXSPI)")
st.metric("OMXSPI Current Price", f"{market_price:,.2f}")

st.subheader("Search for a Specific Stock")
search_input = st.text_input("Enter a ticker or short name", "").upper()
if search_input:
    ticker_to_search = TICKER_MAP.get(search_input, search_input)

    display_stock_details(ticker_to_search)
