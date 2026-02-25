import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 프리미엄 스타일 설정 ---
st.set_page_config(page_title="SON STOCK PRO", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    
    .main-title {
        font-size: 2.2rem !important; font-weight: 800; letter-spacing: -1.5px;
        text-align: center; color: #111827; white-space: nowrap; margin-bottom: 5px;
    }
    .sub-title { text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 25px; }

    /* 전문가용 지표 카드 */
    .metric-card {
        background: #ffffff; border: 1px solid #f3f4f6; border-radius: 16px;
        padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04); text-align: center;
    }
    
    /* 매수 추천 카드 & 한 줄 지표 배지 */
    .buy-card {
        background: #ffffff; border-radius: 14px; padding: 22px;
        margin-bottom: 16px; border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .indicator-container {
        display: flex; flex-direction: row; gap: 8px; margin: 12px 0;
        overflow-x: auto; white-space: nowrap;
    }
    .badge-premium {
        background: #f0f7ff; color: #0055d4; padding: 6px 12px;
        border-radius: 8px; font-size: 13px; font-weight: 700;
        border: 1px solid #dbeafe; display: inline-block;
    }
    .supply-row {
        font-size: 13px; color: #4b5563; background: #f9fafb;
        padding: 10px 14px; border-radius: 10px; margin-top: 10px;
    }
    </style>
    <div class="main-title">SON STOCK PRO</div>
    <div class="sub-title">Day-1 Breakout Strategy Terminal</div>
""", unsafe_allow_html=True)

# --- 2. 분석 엔진 ---
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

# 🌟 200개 종목 리스트 (현대위아 등 포함)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '현대위아': '011210', 'LG화학': '051910', '포스코퓨처엠': '003670',
    '삼성SDI': '006400', '카카오': '035720', '삼성물산': '028260', 'KB금융': '105560',
    '현대모비스': '012330', '신한지주': '055550', 'LG전자': '066570', '삼성화재': '000810',
    '삼성생명': '032830', '하나금융지주': '086790', '한국전력': '015760', 'KT&G': '033780',
    'HMM': '011200', '두산에너빌리티': '034020', '한미반도체': '042700', '현대글로비스': '086280',
    '고려아연': '010130', '삼성SDS': '018260', '삼성전기': '009150', 'HD현대중공업': '329180',
    'LG': '003550', '우리금융지주': '316140', '기업은행': '024110', '엔씨소프트': '036570',
    '한화솔루션': '009830', '아모레퍼시픽': '090430', '롯데케미칼': '011170', '현대제철': '004020',
    'S-Oil': '010950', 'KT': '030200', '유한양행': '000100', '크래프톤': '259960',
    '한온시스템': '018880', '두산': '000150', '한화오션': '042660', '한화에어로스페이스': '012450'
    # ... (생략된 200개 리스트를 그대로 사용하세요)
}

tab1, tab2 = st.tabs(["📊 ANALYSIS", "⚡ SCANNER"])

# ==========================================
# 탭 1: 개별 분석
# ==========================================
with tab1:
    col_l, col_r = st.columns([3, 1])
    with col_l:
        target_name = st.selectbox("STOCK SELECT", list(KOSPI_200.keys()), label_visibility="collapsed")
    with col_r:
        analyze_btn = st.button("RUN AI", use_container_width=True)
    
    if analyze_btn:
        code = KOSPI_200[target_name]
        with st.spinner('Analysing Market...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            
            if not df.empty:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 상단 전문가용 카드 섹션 (한 줄 배치)
                m1, m2, m3 = st.columns(3)
                p, r, v = df['Close'].iloc[-1], df['RSI'].iloc[-1], (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2] * 100)
                
                with m1: st.markdown(f'<div class="metric-card"><small>PRICE</small><br><b style="font-size:1.5rem;">{p:,.0f}</b></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card"><small>RSI(14)</small><br><b style="font-size:1.5rem; color:{"#ef4444" if r>70 else "#2563eb"};">{r:.1f}</b></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card"><small>VOL %</small><br><b style="font-size:1.5rem;">{v:.0f}%</b></div>', unsafe_allow_html=True)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.7, 0.3])
                df_r = df.iloc[-80:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='Price', line=dict(color='#111827', width=2.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10MA', line=dict(color='#ef4444', width=1.5, dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20MA', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='Vol', marker_color='#e5e7eb'), row=2, col=1)
                
                fig.update_layout(template="plotly_white", height=550, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 탭 2: 스캐너 (🌟 당일 발생 'Day-1' 로직 적용)
# ==========================================
with tab2:
    st.markdown("#### ⚡ Day-1 Breakout Scanner")
    scan_range = st.select_slider("Select Target Range", options=["1~50", "51~100", "101~150", "151~200"])
    
    if st.button("EXECUTE SCAN", use_container_width=True):
        items = list(KOSPI_200.items())
        r_map = {"1~50": (0,50), "51~100": (50,100), "101~150": (100,150), "151~200": (150,200)}
        s, e = r_map[scan_range]
        
        results = []
        bar = st.progress(0)
        target_list = items[s:e]
        
        for i, (name, code) in enumerate(target_list):
            try:
                # 데이터 분석 (최소 필요 일수 확보)
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    df_s['MA10'] = df_s['Close'].rolling(10).mean()
                    df_s['MA20'] = df_s['Close'].rolling(20).mean()
                    
                    # 🌟 [Day-1 로직]: 오늘 딱 골든크로스가 발생했는가?
                    # 어제는 10일선 <= 20일선 AND 오늘은 10일선 > 20일선
                    if df_s['MA10'].iloc[-2] <= df_s['MA20'].iloc[-2] and df_s['MA10'].iloc[-1] > df_s['MA20'].iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2] * 100)
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/len(target_list))
        
        if results:
            st.markdown(f"#### 🏆 Found {len(results)} Day-1 Breakouts")
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                st.markdown(f"""
                <div class="buy-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:1.2rem; color:#111827;">{r['name']}</b>
                        <b style="color:#2563eb; font-size:1.1rem;">{r['price']:,.0f} KRW</b>
                    </div>
                    <div class="indicator-container">
                        <div class="badge-premium">GOLDEN CROSS ✅</div>
                        <div class="badge-premium">VOL {r['vol']:.0f}% 🔥</div>
                        <div class="badge-premium">RSI {r['rsi']:.1f} 🌡️</div>
                    </div>
                    <div class="supply-row">
                        <b>Institutional:</b> <span style="color:{'#ef4444' if r['inst']>0 else '#3b82f6'}">{r['inst']:,}</span> | 
                        <b>Foreign:</b> <span style="color:{'#ef4444' if r['frgn']>0 else '#3b82f6'}">{r['frgn']:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No stocks made a golden cross 'today' in this range.")
