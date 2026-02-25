import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 앱 설정 및 스타일 ---
st.set_page_config(page_title="SON STOCK PRO", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    .main-title { font-size: 2.2rem !important; font-weight: 800; text-align: center; color: #111827; white-space: nowrap; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 25px; }
    .metric-card { background: #ffffff; border: 1px solid #f3f4f6; border-radius: 16px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04); text-align: center; }
    .status-box { padding: 20px; border-radius: 16px; margin-bottom: 25px; font-weight: 700; text-align: center; font-size: 1.1rem; border: 1px solid #e5e7eb; }
    .indicator-container { display: flex; flex-direction: row; gap: 8px; margin: 12px 0; overflow-x: auto; white-space: nowrap; }
    .badge-premium { background: #f0f7ff; color: #0055d4; padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; border: 1px solid #dbeafe; display: inline-block; }
    .buy-card { background: #ffffff; border-radius: 14px; padding: 22px; margin-bottom: 16px; border: 1px solid #e5e7eb; }
    </style>
    <div class="main-title">SON STOCK PRO</div>
    <div class="sub-title">Day-1 Breakout Analysis Terminal</div>
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

# 종목 리스트 200개 (현대위아 등 포함)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '현대위아': '011210', 'LG화학': '051910', '포스코퓨처엠': '003670'
    # ... 기존 리스트 유지
}

tab1, tab2 = st.tabs(["📊 ANALYSIS", "⚡ SCANNER"])

# ==========================================
# 탭 1: 개별 분석 (AI 매매 진단 추가)
# ==========================================
with tab1:
    col_l, col_r = st.columns([3, 1])
    with col_l:
        target_name = st.selectbox("STOCK SELECT", list(KOSPI_200.keys()), label_visibility="collapsed")
    with col_r:
        analyze_btn = st.button("RUN AI", use_container_width=True)
    
    if analyze_btn:
        code = KOSPI_200[target_name]
        with st.spinner('Analysing...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            if not df.empty:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 🌟 매매 타이밍 진단 로직 (Day-1 기준)
                is_golden = df['MA10'].iloc[-2] <= df['MA20'].iloc[-2] and df['MA10'].iloc[-1] > df['MA20'].iloc[-1]
                rsi_val = df['RSI'].iloc[-1]
                vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2] * 100)
                
                # 진단 결과 메시지 및 색상 설정
                if is_golden:
                    status_msg = "🚀 [강력 매수] 오늘 막 골든크로스가 발생했습니다! 적극적인 매수를 고려하세요."
                    status_color = "#f0fdf4"; text_color = "#166534"
                elif rsi_val >= 75:
                    status_msg = "🔥 [분할 매도] RSI가 과열권입니다. 욕심을 버리고 익절을 준비하세요."
                    status_color = "#fef2f2"; text_color = "#991b1b"
                elif rsi_val <= 25:
                    status_msg = "💎 [저점 매수] RSI가 바닥권입니다. 반등 가능성이 매우 높습니다."
                    status_color = "#eff6ff"; text_color = "#1e40af"
                else:
                    status_msg = "✅ [관망] 현재는 특별한 신호가 없습니다. 추세를 지켜보세요."
                    status_color = "#f9fafb"; text_color = "#374151"

                # 🌟 진단 결과 출력
                st.markdown(f'<div class="status-box" style="background:{status_color}; color:{text_color};">{status_msg}</div>', unsafe_allow_html=True)
                
                # 지표 카드 섹션
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card"><small>PRICE</small><br><b style="font-size:1.5rem;">{df["Close"].iloc[-1]:,.0f}</b></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card"><small>RSI(14)</small><br><b style="font-size:1.5rem;">{rsi_val:.1f}</b></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card"><small>VOL %</small><br><b style="font-size:1.5rem;">{vol_ratio:.0f}%</b></div>', unsafe_allow_html=True)

                # 전문가용 차트
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.7, 0.3])
                df_r = df.iloc[-80:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='Price', line=dict(color='#111827', width=2.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10MA', line=dict(color='#ef4444', width=1.5, dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20MA', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='Vol', marker_color='#e5e7eb'), row=2, col=1)
                fig.update_layout(template="plotly_white", height=500, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 탭 2: 스캐너 (V19와 동일)
# ==========================================
with tab2:
    st.markdown("#### ⚡ Day-1 Breakout Scanner")
    # ... 스캐너 코드 유지
