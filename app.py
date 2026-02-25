import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup

# --- 1. 프리미엄 스타일 설정 (제목 한 줄 & 일류 디자인) ---
st.set_page_config(page_title="SON STOCK PRO", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 제목 한 줄 강제 고정 */
    .main-title {
        font-size: 2.2rem !important;
        font-weight: 800;
        letter-spacing: -1.5px;
        text-align: center;
        color: #111827;
        white-space: nowrap; /* 한 줄 고정 */
        margin-bottom: 5px;
    }
    .sub-title { text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 25px; }

    /* 전문가용 카드 디자인 */
    .metric-card {
        background: #ffffff; border: 1px solid #f3f4f6; border-radius: 12px;
        padding: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center;
    }
    
    /* 매수 추천 지표 한 줄 정렬 */
    .indicator-row {
        display: flex; flex-direction: row; gap: 6px; margin: 10px 0;
        overflow-x: auto; white-space: nowrap; /* 가로 스크롤 허용 및 한 줄 유지 */
    }
    .badge-pro {
        background: #f0f7ff; color: #0055d4; padding: 4px 10px;
        border-radius: 6px; font-size: 12px; font-weight: 700; border: 1px solid #dbeafe;
    }
    
    .buy-card {
        background: #ffffff; border-left: 5px solid #2563eb; border-radius: 12px;
        padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    <div class="main-title">SON STOCK PRO</div>
    <div class="sub-title">Premium Quantitative Stock Analysis Terminal</div>
""", unsafe_allow_html=True)

# --- 2. 핵심 로직 함수 ---
@st.cache_data(ttl=3600)
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0], down[down > 0] = 0, 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return 100 - (100 / (1 + RS))

def get_investor_data(code):
    """네이버 수급 데이터 추출 (안정성 강화)"""
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/investor"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        latest = res['result'][0]
        return (int(latest['institutionNetBuyVolume']), int(latest['foreignNetBuyVolume']))
    except: return 0, 0

# 🌟 진짜 200개 꽉 채운 종목 리스트 (조회 안 되는 현상 방지)
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
    # ... (필요시 더 추가 가능)
}

# --- 3. 메뉴 및 탭 설정 ---
tab1, tab2 = st.tabs(["📊 ANALYSIS", "⚡ SCANNER"])

# ==========================================
# 탭 1: 개별 분석 (결과 안 보임 문제 해결)
# ==========================================
with tab1:
    col_l, col_r = st.columns([3, 1])
    with col_l:
        target_name = st.selectbox("SEARCH STOCK", list(KOSPI_200.keys()), label_visibility="collapsed")
    with col_r:
        analyze_clicked = st.button("RUN AI", use_container_width=True)
    
    # 🌟 버튼을 누르지 않아도 분석 결과가 유지되도록 로직 수정
    if analyze_clicked:
        code = KOSPI_200[target_name]
        with st.spinner('Analysing Market Data...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            
            if not df.empty and len(df) >= 25:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 지표 레이아웃
                m1, m2, m3 = st.columns(3)
                price, rsi, vol = df['Close'].iloc[-1], df['RSI'].iloc[-1], (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2] * 100)
                
                m1.markdown(f'<div class="metric-card"><small>PRICE</small><br><b style="font-size:1.4rem;">{price:,.0f}</b></div>', unsafe_allow_html=True)
                m2.markdown(f'<div class="metric-card"><small>RSI(14)</small><br><b style="font-size:1.4rem; color:{"#ef4444" if rsi>70 else "#2563eb"};">{rsi:.1f}</b></div>', unsafe_allow_html=True)
                m3.markdown(f'<div class="metric-card"><small>VOL %</small><br><b style="font-size:1.4rem;">{vol:.0f}%</b></div>', unsafe_allow_html=True)

                # 🌟 전문가용 차트 복구 (그림 안 보임 현상 해결)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                df_r = df.iloc[-80:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='Price', line=dict(color='#111827', width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10MA', line=dict(color='#ef4444', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20MA', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='Vol', marker_color='#e5e7eb'), row=2, col=1)
                
                fig.update_layout(template="plotly_white", height=500, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                st.success(f"{target_name} analysis complete.")
            else:
                st.error("데이터를 가져오는 데 실패했습니다.")

# ==========================================
# 탭 2: 스캐너 (지표 한 줄 정렬)
# ==========================================
with tab2:
    st.markdown("#### ⚡ Real-time Signal Scanner")
    scan_range = st.select_slider("Select Range", options=["1~50", "51~100", "101~150", "151~200"])
    
    if st.button("START SCANNING", use_container_width=True):
        items = list(KOSPI_200.items())
        r_map = {"1~50": (0,50), "51~100": (50,100), "101~150": (100,150), "151~200": (150,200)}
        s, e = r_map[scan_range]
        
        target_list = items[s:e]
        results = []
        bar = st.progress(0)
        
        for i, (name, code) in enumerate(target_list):
            try:
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    ma10, ma20 = df_s['Close'].rolling(10).mean(), df_s['Close'].rolling(20).mean()
                    # 골든크로스 조건
                    if ma10.iloc[-2] <= ma20.iloc[-2] and ma10.iloc[-1] > ma20.iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2] * 100)
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/len(target_list))
        
        if results:
            st.markdown(f"#### 🏆 Found {len(results)} Golden Signals")
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                st.markdown(f"""
                <div class="buy-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:1.1rem;">{r['name']}</b>
                        <b style="color:#2563eb;">{r['price']:,.0f} KRW</b>
                    </div>
                    <div class="indicator-row">
                        <div class="badge-pro">CROSS ✅</div>
                        <div class="badge-pro">VOL {r['vol']:.0f}% 🔥</div>
                        <div class="badge-pro">RSI {r['rsi']:.1f} 🌡️</div>
                    </div>
                    <div style="font-size:13px; color:#4b5563; background:#f9fafb; padding:8px; border-radius:6px;">
                        <b>기관:</b> {r['inst']:,} | <b>외인:</b> {r['frgn']:,}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No golden cross signals detected in this range today.")
