import streamlit as st
import plotly.graph_objects as go
from scanner import scan_stock
import pandas as pd
from data import STOCK_GROUPS
import streamlit.components.v1 as components

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Institutional Zone Hunter",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= SESSION STATE =================
if "ticker_index" not in st.session_state:
    st.session_state.ticker_index = 0

# ================= CSS + GOOGLE FONT FIX =================
st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap">

<style>
* { font-family: 'Outfit', sans-serif; letter-spacing: -0.02em; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.main {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.block-container {
    padding: 2rem 3rem;
    max-width: 1600px;
}

.glass-card {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.18);
    margin-bottom: 1.5rem;
}

.main-header {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.2);
}

h1 {
    color: white !important;
    font-weight: 800 !important;
    font-size: 3rem !important;
    margin: 0 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 16px;
    padding: 0.875rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
}

.metric-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.price-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 24px;
    padding: 2rem;
    color: white;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### 🎯 Scanner Settings")
    
    selected_group_name = st.selectbox("Select Index Universe", list(STOCK_GROUPS.keys()))
    active_stock_list = STOCK_GROUPS[selected_group_name]

    mode = st.radio("Selection Mode", ["Full List Scan", "Single Stock"], label_visibility="collapsed")
    
    if mode == "Full List Scan":
        select_all = st.checkbox(f"✓ Scan All {selected_group_name}", value=True)
        selected_tickers = active_stock_list if select_all else st.multiselect("Custom Selection", active_stock_list)
    else:
        selected_tickers = [st.selectbox("Choose Stock", active_stock_list)]

    st.divider()
    PERIOD = st.selectbox("📅 Lookback Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"], index=3)
    INTERVAL = st.selectbox("⏱️ Interval", ["1d", "1wk", "1mo"], index=0)

    st.divider()
    BASE_UI_MODE = st.radio("Base Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True, key="base_ui")
    ENGINE_BASE_MODE = "exact" if BASE_UI_MODE == "Exactly (=)" else "upto"
    BASE_COUNT = st.number_input("Base Count", min_value=1, max_value=6, value=3)

    LEGOUT_UI_MODE = st.radio("Leg-Out Mode", ["Up to (≤)", "Exactly (=)"], horizontal=True, key="legout_ui")
    ENGINE_LEGOUT_MODE = "exact" if LEGOUT_UI_MODE == "Exactly (=)" else "upto"
    LEGOUT_COUNT = st.slider("Leg-Out (Rally) Candles", 1, 4, 1)
  
    ZONE_STATUS = st.selectbox("🔍 Zone Status", ["Fresh Only", "Tested (Up to 1 time)", "Tested (Up to 2 times)"], index=0)
    ENABLE_ENTRY_FILTER = st.toggle("🚪 Entry Barrier Filter", value=True)
    BUFFER = st.slider("Buffer %", 0, 20, 15, disabled=not ENABLE_ENTRY_FILTER)

    with st.expander("⚙️ Advanced"):
        PATTERN = st.selectbox("Pattern", ["RBR", "DBR", "Both"], index=2)
        MARKING_TYPE = st.selectbox("Marking Type", ["Wick to Wick", "Body to Wick"], index=0)
        LEGIN_THRESH = st.slider("Leg-In Exciting %", 40, 95, 55)
        LEGOUT_THRESH = st.slider("Leg-Out Exciting %", 40, 95, 65)
        BS_THRESH = st.slider("Base Body %", 5, 50, 35)
        STRICT_MODE = st.toggle("Strict Breakout", value=True)

    run_btn = st.button("🔍 Scan Now", use_container_width=True, type="primary")

# ================= HEADER =================
st.markdown(f"""
<div class="main-header">
<h1>📈 Institutional Zone Scanner</h1>
<p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; margin: 0.5rem 0 0 0; font-weight: 500;">
Universe: {selected_group_name} | Precision Supply & Demand Analysis
</p>
</div>
""", unsafe_allow_html=True)

# ================= MAIN SCAN LOGIC =================
if run_btn:
    findings = []
    status_text, bar = st.empty(), st.progress(0)

    for i, ticker in enumerate(selected_tickers):
        company = ticker.replace(".NS", "")
        status_text.markdown(f"**🔍 Scanning {company}** ({i+1}/{len(selected_tickers)})")

        stock, result, error = scan_stock(
            ticker, PERIOD, INTERVAL, PATTERN, BASE_COUNT,
            num_legouts=LEGOUT_COUNT, legin_threshold=LEGIN_THRESH,
            legout_threshold=LEGOUT_THRESH, base_threshold=BS_THRESH,
            strict_mode=STRICT_MODE, entry_buffer_pct=BUFFER,
            base_mode=ENGINE_BASE_MODE, legout_mode=ENGINE_LEGOUT_MODE,
            enable_entry_filter=ENABLE_ENTRY_FILTER, zone_status_limit=ZONE_STATUS,
            marking_type=MARKING_TYPE
        )

        if result is not None:
            res_u = result.drop_duplicates(subset=['Formation_ID'])
            for _, p_slice in res_u.iterrows():
                findings.append({
                    "Ticker": ticker, "Company": company,
                    "Pattern": p_slice['Pattern_Found'],
                    "Bases": p_slice['Base_Count'],
                    "Leg-Outs": p_slice['LegOut_Count'],
                    "Zone High": round(p_slice['Zone_High'], 2),
                    "Zone Low": round(p_slice['Zone_Low'], 2),
                    "Current Price": round(stock[f"Close_{ticker}"].iloc[-1], 2),
                    "Leg-In Date": p_slice['LegIn_Date'],
                    "Leg-Out Date": p_slice['LegOut_Date'],
                    "Tests": p_slice['Tests'],
                    "Formation_ID": p_slice['Formation_ID']
                })

        bar.progress((i + 1) / len(selected_tickers))

    status_text.success("✅ Scan complete!")

    if not findings:
        st.markdown(
            """<div class="glass-card" style="text-align:center;">
            <div style="font-size:2.5rem;">📭</div>
            <h3>No Zones Detected</h3>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        full_df = pd.DataFrame(findings)
        full_df = full_df.sort_values(by="Leg-Outs", ascending=False)
        df = full_df.drop_duplicates(subset=["Ticker", "Leg-In Date"], keep="first")
        
        st.session_state["scan_results"] = df
        st.session_state.ticker_index = 0

        c1, c2, c3, c4 = st.columns(4)
        m_data = [
            ("Total Patterns", len(df), "🎯"),
            ("Unique Stocks", df['Ticker'].nunique(), "📊"),
            ("RBR", df['Pattern'].str.contains('Rally').sum(), "🟢"),
            ("DBR", df['Pattern'].str.contains('Drop').sum(), "🟡")
        ]

        for col, (l, v, icon) in zip([c1, c2, c3, c4], m_data):
            with col:
                st.markdown(
                    f"""<div class="metric-card">
                    <div style="font-size: 2rem;">{icon}</div>
                    <div style="font-size: 2rem; font-weight: 800; color: #764ba2;">{v}</div>
                    <div style="color: #64748b; font-size: 0.85rem;">{l}</div>
                    </div>""",
                    unsafe_allow_html=True
                )

# ================= TABS & VISUALIZATION =================
if "scan_results" in st.session_state and not st.session_state["scan_results"].empty:
    tab1, tab2 = st.tabs(["📋 Results Table", "📊 Interactive Chart"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.dataframe(
            st.session_state["scan_results"].drop(columns=['Formation_ID']),
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        ticker_list = st.session_state["scan_results"]["Ticker"].unique().tolist()

        cp, cs, cn = st.columns([1, 4, 1])
        with cp:
            if st.button("⬅️ Previous"):
                st.session_state.ticker_index = max(0, st.session_state.ticker_index - 1)
                st.rerun()

        with cn:
            if st.button("Next ➡️"):
                st.session_state.ticker_index = min(len(ticker_list) - 1, st.session_state.ticker_index + 1)
                st.rerun()

        with cs:
            sel_tick = st.selectbox(
                "Select stock",
                options=ticker_list,
                index=st.session_state.ticker_index,
                label_visibility="collapsed"
            )
            st.session_state.ticker_index = ticker_list.index(sel_tick)

        stock, result, error = scan_stock(
            sel_tick, PERIOD, INTERVAL, PATTERN, BASE_COUNT,
            num_legouts=LEGOUT_COUNT, legin_threshold=LEGIN_THRESH,
            legout_threshold=LEGOUT_THRESH, base_threshold=BS_THRESH,
            strict_mode=STRICT_MODE, entry_buffer_pct=BUFFER,
            base_mode=ENGINE_BASE_MODE, legout_mode=ENGINE_LEGOUT_MODE,
            enable_entry_filter=ENABLE_ENTRY_FILTER, zone_status_limit=ZONE_STATUS,
            marking_type=MARKING_TYPE
        )

        if stock is not None:
            last = stock[f"Close_{sel_tick}"].iloc[-1]

            st.markdown(
                f"""<div class="price-card">
                <h2>{sel_tick.replace(".NS", "")}</h2>
                <div style="font-size: 2.5rem; font-weight: 800;">₹{last:,.2f}</div>
                </div>""",
                unsafe_allow_html=True
            )

            fig = go.Figure(go.Candlestick(
                x=stock.index,
                open=stock[f"Open_{sel_tick}"],
                high=stock[f"High_{sel_tick}"],
                low=stock[f"Low_{sel_tick}"],
                close=stock[f"Close_{sel_tick}"]
            ))

            fig.add_hline(
                y=last,
                line_dash="dash",
                line_color="#FF4B4B",
                annotation_text=f"CMP: {last:.2f}"
            )

            if result is not None:
                res_d = result.drop_duplicates(subset=['Formation_ID']).copy()
                res_d = res_d.sort_values(by="LegOut_Count", ascending=False)
                res_d = res_d.drop_duplicates(subset=["LegIn_Date"], keep="first")
               
                for _, p in res_d.iterrows():
                    fig.add_shape(
                        type="rect",
                        x0=p['LegIn_Date'],
                        x1=stock.index[-1],
                        y0=p['Zone_Low'],
                        y1=p['Zone_High'],
                        fillcolor="rgba(102, 126, 234, 0.1)",
                        line=dict(color="#667eea", width=2, dash="dash")
                    )

                    marker_color = "#10B981" if "Rally" in p['Pattern_Found'] else "#F59E0B"
                    fig.add_scatter(
                        x=[p.name],
                        y=[stock.loc[p.name, f"Low_{sel_tick}"] * 0.99],
                        mode="markers+text",
                        text=[f"{p['Pattern_Found']} ({p['Tests']} Tests)"],
                        textposition="bottom center",
                        marker=dict(symbol="triangle-up", size=16, color=marker_color)
                    )
           
            fig.update_layout(
                template="plotly_white",
                height=700,
                xaxis_rangeslider_visible=False,
                dragmode='pan',
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

# ================= FOOTER =================
components.html("""
<div style="width:100%; background:rgba(255,255,255,0.1);
backdrop-filter:blur(15px); padding:40px; border-radius:24px;
text-align:center; margin-top:40px">

<h2 style="color:white; font-weight:800; letter-spacing:1px">
BUILT WITH ❤️ IN INDIA 🇮🇳
</h2>

<p style="color:white; opacity:.8;">
Providing institutional-grade zone analysis for the modern trader.
</p>

<div style="display:flex; justify-content:center; gap:10px; flex-wrap:wrap;">
<a style="color:white; text-decoration:none;
padding:10px 18px; border-radius:40px; background:#ffffff33;"
href="https://www.instagram.com/im.pankaj" target="_blank">
💼 Instagram
</a>

<a style="color:white; text-decoration:none;
padding:10px 18px; border-radius:40px; background:#ffffff33;"
href="https://t.me/detoxxy996" target="_blank">
✈️ Telegram
</a>

<a style="color:white; text-decoration:none;
padding:10px 18px; border-radius:40px; background:#ffffff33;"
href="https://github.com/shraddhachaurasia02" target="_blank">
📧 Contact Developer
</a>
</div>
</div>
""", height=260)
