import streamlit as st
import plotly.graph_objects as go
from scanner import scan_stock
import pandas as pd
from data import STOCK_GROUPS
import streamlit.components.v1 as components


# ================= PAGE CONFIG =================
st.set_page_config(page_title="Institutional Zone Hunter", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    /* 💎 ADVANCED PARAMETERS - NEON GLOW STYLE */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(236, 72, 153, 0.5) !important; /* Pink-Purple Neon Border */
        border-radius: 20px !important;
        box-shadow: 0 0 20px rgba(236, 72, 153, 0.15) !important; /* Subtle Outer Glow */
        margin-top: 10px !important;
    }

    /* Expander ke andar ka arrow color white karne ke liye */
    [data-testid="stExpander"] summary svg {
        fill: white !important;
    }
</style>
""", unsafe_allow_html=True)


if "ticker_index" not in st.session_state: st.session_state.ticker_index = 0


# ================= ENHANCED CSS (LAYOUT TUNED) + THEME AWARENESS =================
st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap">
<style>
    * { font-family: 'Outfit', sans-serif; letter-spacing: -0.02em; }
    
    /* THEME AWARENESS - Light mode gets gradient, Dark mode gets clean background */
    @media (prefers-color-scheme: light) {
        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important; }
    }
    @media (prefers-color-scheme: dark) {
        .main { background: #0B1120 !important; }
    }
    
    /* Compact Header */
    .main-header {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
    }
    .main-header h1 { color: white !important; font-weight: 800; margin: 0; font-size: 2.2rem; }
    .main-header p { color: rgba(255,255,255,0.9); margin-top: 0.2rem; font-size: 1rem; }
    
    /* Horizontal Price Bar matching screenshot */
    .price-card {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 0.8rem 2rem; 
        color: white;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .price-card-left { display: flex; flex-direction: column; }
    .price-label { font-size: 0.7rem; text-transform: uppercase; opacity: 0.8; font-weight: 600; }
    .stock-name { font-size: 1.8rem; font-weight: 800; margin: 0; }
    .stock-price { font-size: 2.2rem; font-weight: 800; color: #4ade80; }


    /* Compact Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 0.8rem;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border-left: 5px solid #764ba2;
        margin-bottom: 1rem;
    }
    .metric-val { font-size: 1.8rem; font-weight: 800; color: #1e293b; line-height: 1; }
    .metric-lbl { color: #64748b; font-size: 0.65rem; text-transform: uppercase; font-weight: 700; margin-top: 4px; }
    
    /* Chart Container Spacing */
    .stPlotlyChart { margin-top: -10px; }
</style>
""", unsafe_allow_html=True)


# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-top: -20px; margin-bottom: 10px;">
            <img src="https://i.pinimg.com/1200x/65/56/d1/6556d1f996900f1b315db64ae955d524.jpg" 
                 style="width: 250px; height: 150px; border-radius: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.8);">
        </div>
    """, unsafe_allow_html=True)
    
    selected_group_name = st.selectbox("Select Scrip", list(STOCK_GROUPS.keys()))
    active_stock_list = STOCK_GROUPS[selected_group_name]


    mode = st.radio("Selection Mode", ["Full List Scan", "Single Stock"])
    if mode == "Full List Scan":
        select_all = st.checkbox(f"✓ Scan All {selected_group_name}", value=True)
        selected_tickers = active_stock_list if select_all else st.multiselect("Custom Selection", active_stock_list)
    else:
        selected_tickers = [st.selectbox("Choose Stock", active_stock_list)]


    st.divider()
    PERIOD = st.selectbox("📅 Lookback Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"], index=3)
    INTERVAL = st.selectbox("⏱️ Time Frame", ["1d", "1wk", "1mo", "3mo", "6mo"], index=0)


    BASE_UI_MODE = st.radio("Base Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True)
    ENGINE_BASE_MODE = "exact" if BASE_UI_MODE == "Exactly (=)" else "upto"
    BASE_COUNT = st.number_input("Base Candle Count", min_value=1, max_value=6, value=3)


    LEGOUT_UI_MODE = st.radio("Leg-Out Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True)
    ENGINE_LEGOUT_MODE = "exact" if LEGOUT_UI_MODE == "Exactly (=)" else "upto"
    LEGOUT_COUNT = st.slider("Leg-Out (Rally) Candles", 1, 20, 1)
  
    ZONE_STATUS = st.selectbox("Zone Status", ["Fresh Only", "Tested (Up to 1 time)", "Tested (Up to 2 times)"], index=0)
    ENABLE_ENTRY_FILTER = st.toggle("Entry Barrier Filter", value=True)
    BUFFER = st.slider("Price Distance", 0, 20, 15, disabled=not ENABLE_ENTRY_FILTER)


    with st.expander("⚙️ Advanced"):
        PATTERN = st.selectbox("Pattern", ["RBR", "DBR", "Both"], index=2)
        MARKING_TYPE = st.selectbox("Marking Type", ["Wick to Wick", "Body to Wick"], index=0)
        LEGIN_THRESH = st.slider("Leg-In Exciting %", 40, 95, 55)
        LEGOUT_THRESH = st.slider("Leg-Out Exciting %", 40, 95, 65)
        BS_THRESH = st.slider("Base Body %", 5, 50, 35)
        STRICT_MODE = st.toggle("Strict Breakout", value=True)


    run_btn = st.button("🔍 Scan Now", use_container_width=True, type="primary")


# ================= MAIN HEADER =================
st.markdown(f"""
            
<div class="main-header">
    <h1>📈 Institutional Zone Hunter</h1>
    <p>Precision Demand Zone Analysis for {selected_group_name}</p>
</div>
""", unsafe_allow_html=True)


# ================= MAIN SCAN LOGIC =================
if run_btn:
    findings = []
    status_text, bar = st.empty(), st.progress(0)
    for i, ticker in enumerate(selected_tickers):
        status_text.markdown(f"**🔍 Scanning {ticker.replace('.NS','')}** ({i+1}/{len(selected_tickers)})")
        stock_df, result, error = scan_stock(ticker, PERIOD, INTERVAL, PATTERN, BASE_COUNT, LEGOUT_COUNT, LEGIN_THRESH, LEGOUT_THRESH, BS_THRESH, STRICT_MODE, BUFFER, ENGINE_BASE_MODE, ENGINE_LEGOUT_MODE, ENABLE_ENTRY_FILTER, ZONE_STATUS, MARKING_TYPE)
        if result is not None:
            res_u = result.drop_duplicates(subset=['Formation_ID'])
            for _, p in res_u.iterrows():
                findings.append({"Ticker": ticker, "Company": ticker.replace(".NS",""), "Pattern": p['Pattern_Found'], "Bases": p['Base_Count'], "Leg-Outs": p['LegOut_Count'], "Zone High": round(p['Zone_High'], 2), "Zone Low": round(p['Zone_Low'], 2), "Current Price": round(stock_df[f"Close_{ticker}"].iloc[-1], 2), "Leg-In Date": p['LegIn_Date'], "Tests": p['Tests'], "Formation_ID": p['Formation_ID']})
        bar.progress((i + 1) / len(selected_tickers))
    st.session_state["scan_results"] = pd.DataFrame(findings) if findings else pd.DataFrame()
    status_text.empty(); bar.empty()


# ================= VISUALIZATION =================
if ("scan_results" in st.session_state and not st.session_state["scan_results"].empty) or (mode == "Single Stock"):
    if "scan_results" in st.session_state and not st.session_state["scan_results"].empty:
        df_summary = st.session_state["scan_results"]
        c1, c2, c3, c4 = st.columns(4)
        m_list = [("Total Zones", len(df_summary), "🎯"), ("Unique Symbols", df_summary['Ticker'].nunique(), "📊"), ("RBR Pattern", len(df_summary[df_summary['Pattern'] == 'Rally-Base-Rally']), "🟢"), ("DBR Pattern", len(df_summary[df_summary['Pattern'] == 'Drop-Base-Rally']), "🟡")]
        for col, (lbl, val, icon) in zip([c1, c2, c3, c4], m_list):
            col.markdown(f'<div class="metric-card"><div class="metric-lbl">{icon} {lbl}</div><div class="metric-val">{val}</div></div>', unsafe_allow_html=True)


    tab1, tab2 = st.tabs(["📊 Interactive Dashboard", "📋 Raw Data Table"])
    
    with tab2:
        if "scan_results" in st.session_state and not st.session_state["scan_results"].empty:
            st.dataframe(st.session_state["scan_results"].drop(columns=['Formation_ID']), use_container_width=True, hide_index=True)


    with tab1:
        ticker_list = st.session_state["scan_results"]["Ticker"].unique().tolist() if "scan_results" in st.session_state and not st.session_state["scan_results"].empty else selected_tickers
        
        # Navigation bar
        nav_col1, nav_col2, nav_col3 = st.columns([1, 8, 1])
        with nav_col1:
            if st.button("⬅️", use_container_width=True): 
                st.session_state.ticker_index = (st.session_state.ticker_index - 1) % len(ticker_list)
                st.rerun()
        with nav_col3:
            if st.button("➡️", use_container_width=True):
                st.session_state.ticker_index = (st.session_state.ticker_index + 1) % len(ticker_list)
                st.rerun()
        with nav_col2:
            sel_tick = st.selectbox("Select stock", options=ticker_list, index=min(st.session_state.ticker_index, len(ticker_list)-1), label_visibility="collapsed")


        stock, result, error = scan_stock(sel_tick, PERIOD, INTERVAL, PATTERN, BASE_COUNT, LEGOUT_COUNT, LEGIN_THRESH, LEGOUT_THRESH, BS_THRESH, STRICT_MODE, BUFFER, ENGINE_BASE_MODE, ENGINE_LEGOUT_MODE, ENABLE_ENTRY_FILTER, ZONE_STATUS, MARKING_TYPE)
        
        if stock is not None:
            last = stock[f"Close_{sel_tick}"].iloc[-1]
            # Reformatted Price Card to match horizontal screenshot layout
            st.markdown(f"""
                <div class="price-card">
                    <div class="price-card-left">
                        <span class="price-label">Live Market Price</span>
                        <h2 class="stock-name">{sel_tick.replace(".NS","")} <span style="font-size:0.8rem; opacity:0.6;">(NSE)</span></h2>
                    </div>
                    <div class="stock-price">₹{last:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            fig = go.Figure(go.Candlestick(x=stock.index, open=stock[f"Open_{sel_tick}"], high=stock[f"High_{sel_tick}"], low=stock[f"Low_{sel_tick}"], close=stock[f"Close_{sel_tick}"]))
            fig.add_hline(y=last, line_dash="dash", line_color="#4ade80", annotation_text=f"CMP: {last:.2f}", annotation_position="right")
            
            if result is not None:
                for _, p in result.drop_duplicates(subset=['Formation_ID']).iterrows():
                    fig.add_shape(type="rect", x0=p['LegIn_Date'], x1=stock.index[-1], y0=p['Zone_Low'], y1=p['Zone_High'], fillcolor="rgba(102, 126, 234, 0.1)", line=dict(color="#667eea", width=2, dash="dash"))
            
            # Chart height set to 700 to maximize visibility while keeping controls on screen
            fig.update_layout(height=700, margin=dict(t=10, b=10, l=0, r=0), xaxis_rangeslider_visible=False, template="plotly_dark",paper_bgcolor="#0B1120",plot_bgcolor="#0B1120", dragmode='pan', hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})


# ================= FOOTER =================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<style>
 .footer { width: 100%; background-color: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px); padding: 2.5rem; border-radius: 24px 24px 0 0; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2); margin-top: 2rem; }
 .made-in-india { color: white; font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.05em; }
 .footer-subtext { color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-bottom: 1.5rem; }
 .social-links { display: flex; justify-content: center; flex-wrap: wrap; gap: 1rem; }
 .social-icon { color: white !important; text-decoration: none; font-weight: 600; font-size: 0.85rem; padding: 0.6rem 1.2rem; border-radius: 50px; background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.1); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
 .social-icon:hover { background: #FFFFFF; color: #764ba2 !important; transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
 .india-flag { display: inline-block; margin-left: 8px; }
</style>
<div class="footer">
 <div class="made-in-india">BUILT WITH ❤️ IN INDIA <span class="india-flag">🇮🇳</span></div>
 <div class="footer-subtext">Providing institutional-grade zone analysis for the modern trader.</div>
 <div class="social-links">
     <a class="social-icon" href="https://www.instagram.com/im.pankaj?igsh=dTB4emNkdWEyYXZ3" target="_blank">💼 Instagram</a>
     <a class="social-icon" href="https://t.me/detoxxy996" target="_blank">✈️ Telegram</a>
     <a class="social-icon" href="https://github.com/shraddhachaurasia02">📧 Contact Developer</a>
 </div>
</div>
""", unsafe_allow_html=True)
