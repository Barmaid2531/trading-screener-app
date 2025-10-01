# pages/My_Portfolio.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
from pathlib import Path

# --- ROBUST FILE PATH ---
# Creates a reliable path to portfolio.csv in the parent directory
PORTFOLIO_FILE = Path(__file__).parent.parent / "portfolio.csv"

# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=1800)  # Cache data for 30 minutes
def get_position_details(ticker):
    """Fetches full details for a stock: price, indicators, and chart data."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty:
            return None

        # Calculate Indicators
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        latest = hist.iloc[-1]
        
        # Determine Exit Signal
        signal = "HOLD"
        if latest['RSI'] > 75:
            signal = "SELL SIGNAL: RSI is overbought (> 75)"
        elif latest['SMA50'] < latest['SMA200']:
            signal = "SELL SIGNAL: Death Cross (50-day SMA below 200-day SMA)"

        return {
            "price": latest['Close'],
            "rsi": latest['RSI'],
            "sma50": latest['SMA50'],
            "sma200": latest['SMA200'],
            "signal": signal,
            "chart_data": hist
        }
    except Exception as e:
        # Let the calling function handle the exception
        raise e

def get_position_details_with_retry(ticker, retries=3, delay=2):
    """Tries to fetch data multiple times before failing."""
    for i in range(retries):
        try:
            details = get_position_details(ticker)
            if details:
                return details
        except Exception as e:
            print(f"Attempt {i+1} failed for {ticker}: {e}")
            time.sleep(delay)
    return None

def create_portfolio_chart(data, entry_price):
    """Creates a detailed Plotly chart for a portfolio holding."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Price', line=dict(color='#007BFF')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], mode='lines', name='50-Day SMA', line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], mode='lines', name='200-Day SMA', line=dict(color='purple', dash='dot')))
    fig.add_hline(y=entry_price, line_width=2, line_dash="dash", line_color="green", annotation_text="Entry Price", annotation_position="bottom right")
    fig.update_layout(template='plotly_dark', height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def read_portfolio():
    """Safely reads the portfolio CSV file with error handling."""
    if not PORTFOLIO_FILE.is_file():
        return pd.DataFrame(columns=['Ticker', 'EntryDate', 'EntryPrice', 'Quantity', 'Status', 'Notes'])
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
    df.loc[index, 'Quantity'] = new_quantity
    df.loc[index, 'EntryPrice'] = new_gav
    df.loc[index, 'Notes'] = new_notes
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
    st.info("Your portfolio is empty. Add stocks from the 'AI Screener' page or add an existing holding manually.")
else:
    open_positions = portfolio_df[portfolio_df['Status'] == 'Open'].copy()
    total_portfolio_value = 0

    if not open_positions.empty:
        st.markdown("### Open Positions")
        
        for index, row in open_positions.iterrows():
            details = get_position_details_with_retry(row['Ticker'])
            
            if not details:
                st.warning(f"Could not fetch data for {row['Ticker']}. Please check the ticker symbol or network connection.")
                continue

            current_value = details['price'] * row['Quantity']
            total_portfolio_value += current_value
            pnl = ((details['price'] / row['EntryPrice']) - 1) * 100 if row['EntryPrice'] > 0 else 0
            
            st.markdown("---")
            st.subheader(f"{row['Ticker']} ({int(row['Quantity'])} shares)")

            if "SELL SIGNAL" in details['signal']:
                st.error(details['signal'])
            else:
                st.success(details['signal'])

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Value", f"{current_value:,.2f} SEK")
            col2.metric("GAV / Entry Price", f"{row['EntryPrice']:,.2f} SEK")
            col3.metric("Current Price", f"{details['price']:.2f} SEK")
            with col4:
                st.write("Profit/Loss")
                pnl_color = "green" if pnl >= 0 else "red"
                st.markdown(f"<h3 style='color:{pnl_color};'>{pnl:.2f}%</h3>", unsafe_allow_html=True)
            
            with st.expander("Show Chart, Details & Actions"):
                st.markdown("**Key Indicators**")
                c1, c2, c3 = st.columns(3)
                c1.metric("RSI", f"{details['rsi']:.2f}")
                c2.metric("50-Day SMA", f"{details['sma50']:.2f}")
                c3.metric("200-Day SMA", f"{details['sma200']:.2f}")

                st.markdown("**Analysis Chart**")
                chart_fig = create_portfolio_chart(details['chart_data'], row['EntryPrice'])
                st.plotly_chart(chart_fig, use_container_width=True)

                st.markdown("---")
                st.markdown("**Edit Holding**")
                with st.form(key=f"edit_form_{index}"):
                    edit_quantity = st.number_input("Quantity", value=float(row['Quantity']), min_value=0.0, step=1.0)
                    edit_gav = st.number_input("Average Buy Price (GAV)", value=float(row['EntryPrice']), min_value=0.0, format="%.2f")
                    edit_notes = st.text_area("Notes", value=str(row['Notes']) if pd.notna(row['Notes']) else "")
                    
                    if st.form_submit_button("Save Changes"):
                        update_holding(index, edit_quantity, edit_gav, edit_notes)
                        st.rerun()

                st.markdown("**Other Actions**")
                b_col1, b_col2 = st.columns(2)
                if b_col1.button("Close Position", key=f"close_{index}", type="primary"):
                    update_holding_status(index, f"Closed on {datetime.now().strftime('%Y-%m-%d')}")
                    st.rerun()
                if b_col2.button("Remove Permanently", key=f"remove_{index}"):
                    remove_holding(index)
                    st.rerun()
        
        st.markdown("---")
        st.header(f"Total Portfolio Value: {total_portfolio_value:,.2f} SEK")

    st.markdown("### Position History")
    closed_positions = portfolio_df[portfolio_df['Status'] != 'Open']
    if not closed_positions.empty:
        st.dataframe(closed_positions)
