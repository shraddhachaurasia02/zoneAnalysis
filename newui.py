import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from scanner import scan_stock
from data import STOCK_GROUPS

# ================= VIEW STATE MANAGEMENT =================
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "selected_index" not in st.session_state:
    st.session_state.selected_index = list(STOCK_GROUPS.keys())[0]
if "ticker_index" not in st.session_state:
    st.session_state.ticker_index = 0
if "scan_results" not in st.session_state:
    st.session_state.scan_results = pd.DataFrame()

sb_state = "expanded" if st.session_state.view == "scanner" else "collapsed"

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Institutional Zone Hunter",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state=sb_state
)

# ================= ENHANCED CSS (CLEANED VERSION) =================
st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap">
<style>
    .metric-card {
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 15px !important;
        padding: 1.2rem !important;
        text-align: left !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
        border-left: 6px solid #764ba2 !important;
        margin-bottom: 1rem !important;
    }
    .metric-val { font-size: 2.2rem !important; font-weight: 800 !important; color: #1e293b !important; line-height: 1 !important; }
    .metric-lbl { color: #64748b !important; font-size: 0.75rem !important; text-transform: uppercase !important; font-weight: 700 !important; margin-bottom: 8px !important; display: block; }

    .summary-logo { text-align: center; margin-bottom: 2rem; padding: 1rem; }
    .summary-logo img { width: 280px; height: 170px; border-radius: 24px; box-shadow: 0 12px 35px rgba(0,0,0,0.3); transition: transform 0.4s ease; }
    .summary-logo img:hover { transform: scale(1.02); }

    .index-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.8rem 1.5rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
        height: 220px;
        position: relative;
        overflow: hidden;
        margin: 0 1rem 2rem 1rem;
    }
    .glow-blue { box-shadow: 0 0 40px rgba(59, 130, 246, 0.15); border-bottom: 4px solid #3b82f6; }
    .glow-green { box-shadow: 0 0 40px rgba(34, 197, 94, 0.15); border-bottom: 4px solid #22c55e; }
    .glow-orange { box-shadow: 0 0 40px rgba(249, 115, 22, 0.15); border-bottom: 4px solid #f97316; }

    .index-card:hover { background: rgba(255, 255, 255, 0.07); transform: scale(1.02) translateY(-5px); border-color: rgba(255, 255, 255, 0.3); }
    .card-icon-box { background: rgba(255, 255, 255, 0.1); width: 45px; height: 45px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; font-size: 1.4rem; }
    .index-name { font-size: 1.6rem; font-weight: 700; color: white; margin-bottom: 0.5rem; }

    .price-card { background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 12px; padding: 1.5rem 2rem; border: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
    .price-card-left { display: flex; flex-direction: column; }
    .price-label { font-size: 0.7rem; text-transform: uppercase; opacity: 0.8; font-weight: 600; }
    .stock-name { font-size: 1.8rem; font-weight: 800; margin: 0; color: white; }
    .stock-price { font-size: 2.5rem; font-weight: 800; color: #4ade80; }

    [data-testid="stExpander"] { background: rgba(255, 255, 255, 0.03) !important; backdrop-filter: blur(15px) !important; border: 1px solid rgba(236, 72, 153, 0.5) !important; border-radius: 20px !important; margin-top: 10px !important; }
    
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Outfit', sans-serif !important; }
    
    .main { background: #0B1120 !important; }
    .main-header { background: rgba(255,255,255,0.1); backdrop-filter: blur(20px); border-radius: 30px; padding: 1.2rem ; margin-bottom: 2rem; border: 1px solid transparent; text-align: center; color: #ff69b4; }
</style>
""", unsafe_allow_html=True)

# ================= DASHBOARD (LANDING PAGE) =================
def render_landing():
    st.markdown("""
    <div class="main-header">
        <h1 style="color:white; font-size:3rem; font-weight:800;">Institutional Zone Hunter</h1>
        <p style="color:rgba(255,255,255,0.7); font-size:1.1rem;">Precision Demand Zone Analysis. Choose an index to start.</p>
    </div>
    """, unsafe_allow_html=True)
  
    indices = list(STOCK_GROUPS.keys())
    cols = st.columns(3)
    styles = ["glow-blue", "glow-green", "glow-orange"]
    icons = ["💎", "💹", "🎯", "📊", "📈", "📉"]
  
    for i, index_name in enumerate(indices):
        with cols[i % 3]:
            current_style = styles[i % 3]
            st.markdown(f"""
            <div class="index-card {current_style}">
                <div class="card-icon-box">{icons[i % len(icons)]}</div>
                <div class="index-name">{index_name}</div>
                <p style="color:rgba(255,255,255,0.5); font-size:0.9rem; margin-bottom:1rem;">Scan demand zones for {index_name} constituents.</p>
                <div style="color: white; font-weight:600; font-size:0.85rem;">START SCANNING ⬇︎</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Scan {index_name}", key=f"btn_{index_name}", use_container_width=True):
                st.session_state.selected_index = index_name
                st.session_state.view = "scanner"
                st.rerun()

# ================= SCANNER VIEW =================
def render_scanner():
    selected_group_name = st.session_state.selected_index
  
    with st.sidebar:
        st.markdown(f"### ⚙️ {selected_group_name} Config")
        current_idx = list(STOCK_GROUPS.keys()).index(selected_group_name)
        selected_group_name = st.selectbox("Select Scrip", list(STOCK_GROUPS.keys()), index=current_idx)
      
        active_stock_list = STOCK_GROUPS[selected_group_name]
        mode = st.radio("Selection Mode", ["Full List Scan", "Single Stock"])
        
        if mode == "Full List Scan":
            if st.checkbox(f"✓ Scan All {selected_group_name}", value=True):
                selected_tickers = active_stock_list
            else:
                selected_tickers = st.multiselect("Custom Selection", active_stock_list)
        else:
            selected_tickers = [st.selectbox("Choose Stock", active_stock_list)]
      
        st.divider()
        PERIOD = st.selectbox("📅 Lookback Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"], index=3)
        ENABLE_CONFLUENCE = st.toggle("🔄 Zone Confluence (HTF + LTF)", value=False)
      
        if ENABLE_CONFLUENCE:
            HTF_INTERVAL = st.selectbox("Higher Timeframe (HTF)", ["1wk", "1mo", "3mo", "6mo"], index=1)
            LTF_INTERVAL = st.selectbox("Lower Timeframe (LTF)", ["1d", "1wk", "1mo"], index=0)
            with st.expander("📊 HTF Settings"):
                ENGINE_BASE_MODE_HTF = "exact" if st.radio("HTF Base Mode", ["Up to (≤)", "Exactly (=)"], key="htf_bm") == "Exactly (=)" else "upto"
                HTF_BASE_COUNT = st.number_input("HTF Base Count", 1, 6, 3, key="htf_bc")
                ENGINE_LEGOUT_MODE_HTF = "exact" if st.radio("HTF Leg-Out Mode", ["Up to (≤)", "Exactly (=)"], key="htf_lm") == "Exactly (=)" else "upto"
                HTF_LEGOUT_COUNT = st.slider("HTF Leg-Out Candles", 1, 20, 1, key="htf_lc")
                HTF_ZONE_STATUS = st.selectbox("HTF Status", ["Fresh Only", "Tested (Up to 1 time)", "Tested (Up to 2 times)"], key="htf_zs")
                HTF_ENABLE_ENTRY_FILTER = st.toggle("HTF Entry Filter", True, key="htf_ef")
                HTF_BUFFER = st.slider("HTF Price Distance", 0, 20, 15, key="htf_buf", disabled=not HTF_ENABLE_ENTRY_FILTER)
                HTF_PATTERN = st.selectbox("HTF Pattern", ["RBR", "DBR", "Both"], 2, key="htf_pat")
                HTF_MARKING_TYPE = st.selectbox("HTF Marking", ["Wick to Wick", "Body to Wick"], 0, key="htf_mark")
                HTF_LEGIN_THRESH = st.slider("HTF Leg-In %", 40, 95, 55, key="htf_li")
                HTF_LEGOUT_THRESH = st.slider("HTF Leg-Out %", 40, 95, 65, key="htf_lo")
                HTF_BS_THRESH = st.slider("HTF Base Body %", 5, 50, 35, key="htf_bst")
                HTF_STRICT_MODE = st.toggle("HTF Strict Breakout", True, key="htf_sm")
            with st.expander("📉 LTF Settings", expanded=True):
                ENGINE_BASE_MODE_LTF = "exact" if st.radio("LTF Base Mode", ["Up to (≤)", "Exactly (=)"], key="ltf_bm") == "Exactly (=)" else "upto"
                LTF_BASE_COUNT = st.number_input("LTF Base Count", 1, 6, 3, key="ltf_bc")
                ENGINE_LEGOUT_MODE_LTF = "exact" if st.radio("LTF Leg-Out Mode", ["Up to (≤)", "Exactly (=)"], key="ltf_lm") == "Exactly (=)" else "upto"
                LTF_LEGOUT_COUNT = st.slider("LTF Leg-Out Candles", 1, 20, 1, key="ltf_lc")
                LTF_ZONE_STATUS = st.selectbox("LTF Status", ["Fresh Only", "Tested (Up to 1 time)", "Tested (Up to 2 times)"], key="ltf_zs")
                LTF_ENABLE_ENTRY_FILTER = st.toggle("LTF Entry Filter", True, key="ltf_ef")
                LTF_BUFFER = st.slider("LTF Price Distance", 0, 20, 15, key="ltf_buf", disabled=not LTF_ENABLE_ENTRY_FILTER)
                LTF_PATTERN = st.selectbox("LTF Pattern", ["RBR", "DBR", "Both"], 2, key="ltf_pat")
                LTF_MARKING_TYPE = st.selectbox("LTF Marking", ["Wick to Wick", "Body to Wick"], 0, key="ltf_mark")
                LTF_LEGIN_THRESH = st.slider("LTF Leg-In %", 40, 95, 55, key="ltf_li")
                LTF_LEGOUT_THRESH = st.slider("LTF Leg-Out %", 40, 95, 65, key="ltf_lo")
                LTF_BS_THRESH = st.slider("LTF Base Body %", 5, 50, 35, key="ltf_bst")
                LTF_STRICT_MODE = st.toggle("LTF Strict Breakout", True, key="ltf_sm")
        else:
            INTERVAL = st.selectbox("⏱️ Time Frame", ["1d", "1wk", "1mo", "3mo", "6mo"], 0)
            BASE_UI_MODE = st.radio("Base Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True)
            ENGINE_BASE_MODE = "exact" if BASE_UI_MODE == "Exactly (=)" else "upto"
            BASE_COUNT = st.number_input("Base Candle Count", 1, 6, 3)
            LEGOUT_UI_MODE = st.radio("Leg-Out Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True)
            ENGINE_LEGOUT_MODE = "exact" if LEGOUT_UI_MODE == "Exactly (=)" else "upto"
            LEGOUT_COUNT = st.slider("Leg-Out (Rally) Candles", 1, 20, 1)
            ZONE_STATUS = st.selectbox("Zone Status", ["Fresh Only", "Tested (Up to 1 time)", "Tested (Up to 2 times)"], 0)
            ENABLE_ENTRY_FILTER = st.toggle("Entry Barrier Filter", True)
            BUFFER = st.slider("Price Distance", 0, 20, 15, disabled=not ENABLE_ENTRY_FILTER)
            with st.expander("⚙️ Advanced"):
                PATTERN = st.selectbox("Pattern", ["RBR", "DBR", "Both"], 2)
                MARKING_TYPE = st.selectbox("Marking Type", ["Wick to Wick", "Body to Wick"], 0)
                LEGIN_THRESH = st.slider("Leg-In Exciting %", 40, 95, 55)
                LEGOUT_THRESH = st.slider("Leg-Out Exciting %", 40, 95, 65)
                BS_THRESH = st.slider("Base Body %", 5, 50, 35)
                STRICT_MODE = st.toggle("Strict Breakout", True)
          
            HTF_INTERVAL = LTF_INTERVAL = INTERVAL; HTF_PATTERN = LTF_PATTERN = PATTERN
            HTF_BASE_COUNT = LTF_BASE_COUNT = BASE_COUNT; HTF_LEGOUT_COUNT = LTF_LEGOUT_COUNT = LEGOUT_COUNT
            HTF_LEGIN_THRESH = LTF_LEGIN_THRESH = LEGIN_THRESH; HTF_LEGOUT_THRESH = LTF_LEGOUT_THRESH = LEGOUT_THRESH
            HTF_BS_THRESH = LTF_BS_THRESH = BS_THRESH; HTF_STRICT_MODE = LTF_STRICT_MODE = STRICT_MODE
            HTF_BUFFER = LTF_BUFFER = BUFFER; ENGINE_BASE_MODE_HTF = ENGINE_BASE_MODE_LTF = ENGINE_BASE_MODE
            ENGINE_LEGOUT_MODE_HTF = ENGINE_LEGOUT_MODE_LTF = ENGINE_LEGOUT_MODE; HTF_ENABLE_ENTRY_FILTER = LTF_ENABLE_ENTRY_FILTER = ENABLE_ENTRY_FILTER
            HTF_ZONE_STATUS = LTF_ZONE_STATUS = ZONE_STATUS; HTF_MARKING_TYPE = LTF_MARKING_TYPE = MARKING_TYPE

        run_btn = st.button("🔍 Scan Now", use_container_width=True, type="primary")

    if st.button("🏠 Back to Dashboard"):
        st.session_state.view = "landing"
        st.rerun()

    # ================= MAIN SCAN LOGIC =================
    if run_btn:
        findings, status_text, bar = [], st.empty(), st.progress(0)
        total_tickers = len(selected_tickers)
        for i, ticker in enumerate(selected_tickers):
            status_text.markdown(f"**🔍 Scanning {ticker.replace('.NS','')}** ({i+1}/{total_tickers})")
            stock_df, result, error = scan_stock(ticker, PERIOD, HTF_INTERVAL, HTF_PATTERN, HTF_BASE_COUNT, HTF_LEGOUT_COUNT, HTF_LEGIN_THRESH, HTF_LEGOUT_THRESH, HTF_BS_THRESH, HTF_STRICT_MODE, HTF_BUFFER, ENGINE_BASE_MODE_HTF, ENGINE_LEGOUT_MODE_HTF, HTF_ENABLE_ENTRY_FILTER, HTF_ZONE_STATUS, HTF_MARKING_TYPE, LTF_INTERVAL, LTF_PATTERN, LTF_BASE_COUNT, LTF_LEGOUT_COUNT, LTF_LEGIN_THRESH, LTF_LEGOUT_THRESH, LTF_BS_THRESH, LTF_STRICT_MODE, LTF_BUFFER, ENGINE_BASE_MODE_LTF, ENGINE_LEGOUT_MODE_LTF, LTF_ENABLE_ENTRY_FILTER, LTF_ZONE_STATUS, LTF_MARKING_TYPE, ENABLE_CONFLUENCE)
            if error != "No Confluence Zone Found" and result is not None and not result.empty:
                for _, p in result.iterrows():
                    row = {"Company": ticker.replace(".NS",""), "Pattern": p['Pattern_Found'], "Bases": p['Base_Count'], "LegOuts": p['LegOut_Count'], "Zone High": round(p['Zone_High'], 2), "Zone Low": round(p['Zone_Low'], 2), "Ticker": ticker, "Current Price": round(stock_df[f"Close_{ticker}"].iloc[-1], 2), "Tests": p['Tests']}
                    if ENABLE_CONFLUENCE: row["LTF Leg-In"], row["HTF Leg-In"] = p['LegIn_Date'], p.get('HTF_LegIn_Date', "N/A")
                    else: row["Leg-In Date"] = p['LegIn_Date']
                    findings.append(row)
            time.sleep(0.05)
            bar.progress((i + 1) / total_tickers)
      
        if findings:
            full_df = pd.DataFrame(findings)
            unique_df = full_df.sort_values("LegOuts", ascending=False).drop_duplicates(subset=["Ticker", "Pattern", "Zone High", "Zone Low"], keep="first")
            st.session_state["scan_results"] = unique_df
        else:
            st.session_state["scan_results"] = pd.DataFrame()
        status_text.empty(); bar.empty()

    # ================= VISUALIZATION =================
    if not st.session_state["scan_results"].empty:
        st.markdown('<div class="summary-logo"><img src="https://i.pinimg.com/1200x/65/56/d1/6556d1f996900f1b315db64ae955d524.jpg"></div>', unsafe_allow_html=True)
      
        df_res = st.session_state["scan_results"]
        c1, c2, c3, c4 = st.columns(4)
        m_list = [("Total Zones", len(df_res), "🎯"), ("Unique Symbols", df_res['Company'].nunique(), "📊"), ("RBR Pattern", len(df_res[df_res['Pattern'] == 'Rally-Base-Rally']), "🟢"), ("DBR Pattern", len(df_res[df_res['Pattern'] == 'Drop-Base-Rally']), "🟡")]
        for col, (lbl, val, icon) in zip([c1, c2, c3, c4], m_list):
            col.markdown(f'<div class="metric-card"><span class="metric-lbl">{icon} {lbl}</span><div class="metric-val">{val}</div></div>', unsafe_allow_html=True)
      
        tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Raw Data"])
        with tab2:
            display_cols = ["Company", "Pattern", "Bases", "Zone High", "Zone Low", "LTF Leg-In", "HTF Leg-In", "Current Price", "Tests"] if ENABLE_CONFLUENCE else ["Company", "Pattern", "Bases", "Zone High", "Zone Low", "Leg-In Date", "Current Price", "Tests"]
            st.dataframe(df_res[display_cols], use_container_width=True, hide_index=True)
      
        with tab1:
            ticker_list = df_res["Ticker"].unique().tolist()
            nav_col1, nav_col2, nav_col3 = st.columns([1, 8, 1])
            with nav_col1:
                if st.button("⬅️"): st.session_state.ticker_index = (st.session_state.ticker_index - 1) % len(ticker_list); st.rerun()
            with nav_col3:
                if st.button("➡️"): st.session_state.ticker_index = (st.session_state.ticker_index + 1) % len(ticker_list); st.rerun()
            sel_tick = nav_col2.selectbox("Select", ticker_list, index=min(st.session_state.ticker_index, len(ticker_list)-1), label_visibility="collapsed")
          
            stock, result, error = scan_stock(sel_tick, PERIOD, HTF_INTERVAL, HTF_PATTERN, HTF_BASE_COUNT, HTF_LEGOUT_COUNT, HTF_LEGIN_THRESH, HTF_LEGOUT_THRESH, HTF_BS_THRESH, HTF_STRICT_MODE, HTF_BUFFER, ENGINE_BASE_MODE_HTF, ENGINE_LEGOUT_MODE_HTF, HTF_ENABLE_ENTRY_FILTER, HTF_ZONE_STATUS, HTF_MARKING_TYPE, LTF_INTERVAL, LTF_PATTERN, LTF_BASE_COUNT, LTF_LEGOUT_COUNT, LTF_LEGIN_THRESH, LTF_LEGOUT_THRESH, LTF_BS_THRESH, LTF_STRICT_MODE, LTF_BUFFER, ENGINE_BASE_MODE_LTF, ENGINE_LEGOUT_MODE_LTF, LTF_ENABLE_ENTRY_FILTER, LTF_ZONE_STATUS, LTF_MARKING_TYPE, ENABLE_CONFLUENCE)
          
            if stock is not None:
                last = stock[f"Close_{sel_tick}"].iloc[-1]
                st.markdown(f"""
                    <div class="price-card">
                        <div class="price-card-left">
                            <span class="price-label">Live Price</span>
                            <h2 class="stock-name">{sel_tick.replace(".NS","")}</h2>
                        </div>
                        <div class="stock-price">₹{last:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
              
                fig = go.Figure(go.Candlestick(x=stock.index, open=stock[f"Open_{sel_tick}"], high=stock[f"High_{sel_tick}"], low=stock[f"Low_{sel_tick}"], close=stock[f"Close_{sel_tick}"]))
                if result is not None:
                    res_clean = result.sort_values('LegOut_Count', ascending=False).drop_duplicates(subset=['Pattern_Found', 'Zone_High', 'Zone_Low'])
                    for _, p in res_clean.iterrows():
                        fig.add_shape(type="rect", x0=p['LegIn_Date'], x1=stock.index[-1], y0=p['Zone_Low'], y1=p['Zone_High'], fillcolor="rgba(102, 126, 234, 0.15)", line=dict(color="#667eea", width=2, dash="dash"))
              
                fig.update_layout(
                    height=650, margin=dict(t=0, b=0, l=0, r=0),
                    xaxis_rangeslider_visible=False, template="plotly_dark",
                    paper_bgcolor="#0B1120", plot_bgcolor="#0B1120",
                    xaxis=dict(fixedrange=False), yaxis=dict(fixedrange=False), dragmode='zoom'
                )
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    elif run_btn:
        st.warning("❌ No Confluence Zone Found" if ENABLE_CONFLUENCE else "❌ No Institutional Zones Found")

# ================= ROUTER =================
if st.session_state.view == "landing":
    render_landing()
else:
    render_scanner()

# ================= ORIGINAL FOOTER =================
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