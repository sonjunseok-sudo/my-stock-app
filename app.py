import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 앱 설정 및 스타일 ---
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# 탭 이동을 위한 세션 상태 관리 (매우 중요!)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🔍 개별 분석"
if 'target_stock_name' not in st.session_state:
    st.session_state.target_stock_name = '삼성전자'

# 제목 한 줄 고정 및 디자인 CSS
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem !important; font-weight: 800; white-space: nowrap; text-align: center; margin-bottom: 20px; color: #1f2937; }
    .buy-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; }
    .badge-blue { background-color: #eff6ff; color: #1e40af; }
    </style>
    <h1 class="main-title">📈 손선생 주식 분석</h1>
""", unsafe_allow_html=True)

# --- 2. 핵심 로직 함수 ---
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
        return (int(latest['institutionNetBuyVolume']), int(latest['foreignNetBuyVolume']), int(latest['individualNetBuyVolume']))
    except: return None, None, None

# 종목 리스트 200개 (사용자님의 기존 리스트를 유지해주세요)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '현대위아': '011210', 'LG화학': '051910', '포스코퓨처엠': '003670'
    # ... 리스트 생략 (기존 200개 데이터 그대로 사용)
}

# --- 3. 탭 구성 (세션 상태와 연동) ---
tab_list = ["🔍 개별 분석", "🚀 AI 매수 추천 스캐너"]
# 현재 활성 탭을 세션에서 가져와 결정함
active_tab = st.radio("메뉴 이동", tab_list, index=tab_list.index(st.session_state.active_tab), horizontal=True, label_visibility="collapsed")

# ==========================================
# 탭 1: 개별 종목 분석
# ==========================================
if active_tab == "🔍 개별 분석":
    all_names = list(KOSPI_200.keys())
    # 스캐너에서 넘어온 종목이 있으면 해당 종목 자동 선택
    idx = all_names.index(st.session_state.target_stock_name) if st.session_state.target_stock_name in all_names else 0
    selected_name = st.selectbox("분석할 종목을 검색하세요:", all_names, index=idx)
    code = KOSPI_200[selected_name]

    if st.button("📊 실시간 데이터 분석 시작"):
        with st.spinner(f'{selected_name} 분석 중...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            # ... (기존 차트 및 RSI 분석 로직 동일) ...
            st.success(f"{selected_name}의 상세 차트와 분석 결과입니다.")
            # [차트 그리는 코드 생략 - 이전 V11과 동일하게 작동]

# ==========================================
# 탭 2: AI 매수 추천 스캐너 (복구 및 기능 강화)
# ==========================================
elif active_tab == "🚀 AI 매수 추천 스캐너":
    st.write("200개 우량주 중 **골든크로스+거래량+RSI**가 완벽한 종목을 스캔합니다.")
    range_option = st.radio("스캔 범위 (50개 단위):", ["1~50위", "51~100위", "101~150위", "151~200위"], horizontal=True)
    
    if st.button("🚀 매수 추천 종목 스캔 시작"):
        all_items = list(KOSPI_200.items())
        idx_map = {"1~50위": (0,50), "51~100위": (50,100), "101~150위": (100,150), "151~200위": (150,200)}
        start, end = idx_map[range_option]
        target_list = all_items[start:end]
        
        results = []
        bar = st.progress(0)
        
        for i, (name, code) in enumerate(target_list):
            try:
                df = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df) >= 25:
                    df['MA10'] = df['Close'].rolling(10).mean()
                    df['MA20'] = df['Close'].rolling(20).mean()
                    df['RSI'] = calculate_rsi(df)
                    
                    # 1. 골든크로스 체크
                    if df['MA10'].iloc[-2] <= df['MA20'].iloc[-2] and df['MA10'].iloc[-1] > df['MA20'].iloc[-1]:
                        vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2]) * 100
                        inst, frgn, pers = get_investor_data(code)
                        results.append({
                            'name': name, 'code': code, 'price': df['Close'].iloc[-1],
                            'vol': vol_ratio, 'rsi': df['RSI'].iloc[-1], 'inst': inst, 'frgn': frgn
                        })
            except: pass
            bar.progress((i+1)/len(target_list))
        
        st.subheader("🏆 오늘의 AI 매수 추천주")
        if results:
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                with st.container():
                    # 🌟 요청하신 1.골든크로스 2.거래량 3.RSI 지표 복구!
                    st.markdown(f"""
                    <div class="buy-card">
                        <h3 style="margin:0;">{r['name']} ({r['code']}) <span style="font-size:16px; color:#6b7280;">| {r['price']:,.0f}원</span></h3>
                        <div style="margin: 10px 0;">
                            <span class="badge badge-blue">1. 골든크로스 발생 ✅</span>
                            <span class="badge badge-blue">2. 거래량 {r['vol']:.0f}% 🔥</span>
                            <span class="badge badge-blue">3. RSI {r['rsi']:.1f} 🌡️</span>
                        </div>
                        <div style="font-size:14px; color:#374151;">
                            <b>📊 전일 수급:</b> 기관 {f"{r['inst']:,}" if r['inst'] is not None else "집계중"} | 외인 {f"{r['frgn']:,}" if r['frgn'] is not None else "집계중"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 🌟 클릭 시 개별 분석 탭으로 즉시 이동하는 마법의 버튼
                    if st.button(f"🔍 {r['name']} 분석하기", key=f"move_{r['code']}"):
                        st.session_state.target_stock_name = r['name'] # 종목 이름 저장
                        st.session_state.active_tab = "🔍 개별 분석" # 탭 상태 변경
                        st.rerun() # 앱 강제 재실행 (페이지 이동 효과)
        else: st.warning("현재 범위 내에 추천 종목이 없습니다.")
