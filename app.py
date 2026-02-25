import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 프리미엄 테마 및 스타일 설정 ---
st.set_page_config(page_title="손선생 PRO", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 제목 디자인: 일류 디자이너 느낌의 미니멀리즘 */
    .main-title {
        font-size: 2.4rem !important;
        font-weight: 800;
        letter-spacing: -1.5px;
        text-align: center;
        color: #111827;
        margin-bottom: 5px;
        white-space: nowrap;
    }
    .sub-title {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 30px;
    }

    /* 전문가용 메트릭 카드 */
    .metric-container {
        background: #ffffff;
        border: 1px solid #f3f4f6;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    /* 매수 추천 카드: 지표 한 줄 정렬 */
    .buy-card {
        background: #ffffff;
        border-left: 5px solid #2563eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .indicator-row {
        display: flex;
        gap: 10px;
        margin: 12px 0;
        flex-wrap: nowrap;
        overflow-x: auto;
    }
    .badge-premium {
        background: #f0f7ff;
        color: #024db5;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        border: 1px solid #dbeafe;
        white-space: nowrap;
    }
    
    /* 수급 정보 텍스트 */
    .supply-info {
        font-size: 13px;
        color: #4b5563;
        background: #f9fafb;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    <div class="main-title">SON STOCK PRO</div>
    <div class="sub-title">Advanced Quantitative Analysis Terminal</div>
""", unsafe_allow_html=True)

# --- 2. 핵심 로직 ---
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0], down[down > 0] = 0, 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return 100 - (100 / (1 + RS))

def get_investor_data(code):
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/investor"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        latest = res['result'][0]
        return (int(latest['institutionNetBuyVolume']), int(latest['foreignNetBuyVolume']))
    except: return 0, 0

# 종목 리스트 (필요한 만큼 유지)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '현대위아': '011210', 'LG화학': '051910', '포스코퓨처엠': '003670'
}

tab1, tab2 = st.tabs(["📊 ANALYSIS", "⚡ SCANNER"])

# ==========================================
# 탭 1: 개별 분석 (일류 디자이너 스타일)
# ==========================================
with tab1:
    col_l, col_r = st.columns([3, 1])
    with col_l:
        selected_name = st.selectbox("SEARCH STOCK", list(KOSPI_200.keys()), label_visibility="collapsed")
    with col_r:
        run_btn = st.button("RUN AI", use_container_width=True)
    
    code = KOSPI_200[selected_name]

    if run_btn:
        with st.spinner('Accessing Terminal...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            
            if not df.empty:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 상단 전문가용 메트릭 레이아웃
                m1, m2, m3 = st.columns(3)
                curr_price = df['Close'].iloc[-1]
                rsi_val = df['RSI'].iloc[-1]
                vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2]) * 100
                
                with m1:
                    st.markdown(f'<div class="metric-container"><small>PRICE</small><br><b style="font-size:1.5rem;">{curr_price:,.0f}</b></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-container"><small>RSI(14)</small><br><b style="font-size:1.5rem; color:{"#ef4444" if rsi_val>70 else "#2563eb" if rsi_val<30 else "#111827"};">{rsi_val:.1f}</b></div>', unsafe_allow_html=True)
                with m3:
                    st.markdown(f'<div class="metric-container"><small>VOL RATIO</small><br><b style="font-size:1.5rem;">{vol_ratio:.0f}%</b></div>', unsafe_allow_html=True)

                # 전문가용 다크 테마 차트
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
                df_r = df.iloc[-80:]
                
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='Price', line=dict(color='#111827', width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='MA10', line=dict(color='#ef4444', width=1.5, dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='MA20', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='Vol', marker_color='#e5e7eb'), row=2, col=1)
                
                fig.update_layout(template="plotly_white", height=500, margin=dict(l=0, r=0, t=20, b=0), showlegend=False,
                                  hovermode="x unified", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 탭 2: 스캐너 (지표 한 줄 정렬)
# ==========================================
with tab2:
    st.markdown("#### ⚡ Real-time Market Scanner")
    range_opt = st.select_slider("Select Scan Range", options=["1~50", "51~100", "101~150", "151~200"])
    
    if st.button("START SCANNING", use_container_width=True):
        all_items = list(KOSPI_200.items())
        # 범위 설정
        r_map = {"1~50": (0,50), "51~100": (50,100), "101~150": (100,150), "151~200": (150,200)}
        s, e = r_map[range_opt]
        
        results = []
        bar = st.progress(0)
        target = all_items[s:e]
        
        for i, (name, code) in enumerate(target):
            try:
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    ma10, ma20 = df_s['Close'].rolling(10).mean(), df_s['Close'].rolling(20).mean()
                    if ma10.iloc[-2] <= ma20.iloc[-2] and ma10.iloc[-1] > ma20.iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2]) * 100
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/len(target))
        
        if results:
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                st.markdown(f"""
                <div class="buy-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:1.2rem;">{r['name']}</b>
                        <b style="color:#2563eb;">{r['price']:,.0f} KRW</b>
                    </div>
                    <div class="indicator-row">
                        <span class="badge-premium">CROSS ✅</span>
                        <span class="badge-premium">VOL {r['vol']:.0f}% 🔥</span>
                        <span class="badge-premium">RSI {r['rsi']:.1f} 🌡️</span>
                    </div>
                    <div class="supply-info">
                        <b>Institutional:</b> <span style="color:{'#ef4444' if r['inst']>0 else '#3b82f6'}">{r['inst']:,}</span> | 
                        <b>Foreign:</b> <span style="color:{'#ef4444' if r['frgn']>0 else '#3b82f6'}">{r['frgn']:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No signals detected in this range.")
