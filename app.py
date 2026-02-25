import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 기본 설정 및 CSS ---
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 2.2rem !important; font-weight: 800; white-space: nowrap; text-align: center; margin-bottom: 20px; color: #1f2937; }
    .buy-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .badge { padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: bold; margin-right: 5px; background-color: #eff6ff; color: #1e40af; border: 1px solid #dbeafe; }
    </style>
    <h1 class="main-title">📈 손선생 주식 분석</h1>
""", unsafe_allow_html=True)

# --- 2. 핵심 함수 ---
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

# 종목 리스트 200개 (사용자님의 기존 리스트를 여기 넣어주세요)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '포스코퓨처엠': '003670', '삼성SDI': '006400', '카카오': '035720',
    '현대위아': '011210', 'LG화학': '051910', '삼성물산': '028260'
}

# --- 3. 탭 구성 ---
tab1, tab2 = st.tabs(["🔍 개별 분석", "🚀 AI 매수 추천 스캐너"])

# ==========================================
# 탭 1: 개별 분석 (정상 작동 확인)
# ==========================================
with tab1:
    all_names = list(KOSPI_200.keys())
    selected_name = st.selectbox("분석할 종목을 선택하세요:", all_names)
    code = KOSPI_200[selected_name]

    if st.button("📊 AI 데이터 분석 실행"):
        with st.spinner(f'{selected_name} 데이터 분석 중...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            
            if not df.empty and len(df) >= 25:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 상단 지표
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"{df['Close'].iloc[-1]:,.0f}원")
                c2.metric("현재 RSI", f"{df['RSI'].iloc[-1]:.1f}")
                vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2]) * 100
                c3.metric("거래량대비", f"{vol_ratio:.0f}%")

                # 차트
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                df_r = df.iloc[-60:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='종가', line=dict(color='gray')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10일선', line=dict(color='red')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20일선', line=dict(color='orange')), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='거래량', marker_color='blue'), row=2, col=1)
                fig.update_layout(template="plotly_white", height=500, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("데이터를 불러올 수 없습니다.")

# ==========================================
# 탭 2: AI 매수 추천 스캐너 (3대 지표 + 수급)
# ==========================================
with tab2:
    st.write("50개 단위로 정밀 스캔하여 매수 유망 종목을 찾습니다.")
    range_opt = st.radio("스캔 범위 선택:", ["1~50위", "51~100위", "101~150위", "151~200위"], horizontal=True)
    
    if st.button("🚀 매수 신호 스캔 시작"):
        all_items = list(KOSPI_200.items())
        idx_map = {"1~50위": (0,50), "51~100위": (50,100), "101~150위": (100,150), "151~200위": (150,200)}
        s, e = idx_map[range_opt]
        
        results = []
        bar = st.progress(0)
        
        target_list = all_items[s:e]
        for i, (name, code) in enumerate(target_list):
            try:
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    df_s['MA10'] = df_s['Close'].rolling(10).mean()
                    df_s['MA20'] = df_s['Close'].rolling(20).mean()
                    # 1. 골든크로스 확인
                    if df_s['MA10'].iloc[-2] <= df_s['MA20'].iloc[-2] and df_s['MA10'].iloc[-1] > df_s['MA20'].iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2]) * 100
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/len(target_list))
        
        st.subheader("🏆 발견된 매수 추천 종목")
        if results:
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                st.markdown(f"""
                <div class="buy-card">
                    <h3 style="margin:0;">{r['name']} ({r['code']}) | <span style="color:#2563eb;">{r['price']:,.0f}원</span></h3>
                    <div style="margin: 12px 0;">
                        <span class="badge">1. 골든크로스 발생 ✅</span>
                        <span class="badge">2. 거래량 {r['vol']:.0f}% 🔥</span>
                        <span class="badge">3. RSI {r['rsi']:.1f} 🌡️</span>
                    </div>
                    <div style="font-size:14px; color:#4b5563;">
                        <b>📊 전일 수급 현황</b><br>
                        기관: <span style="color:{'#ef4444' if r['inst']>0 else '#3b82f6'}">{r['inst']:,} 주</span> | 
                        외인: <span style="color:{'#ef4444' if r['frgn']>0 else '#3b82f6'}">{r['frgn']:,} 주</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("현재 범위 내에 조건에 맞는 종목이 없습니다.")
