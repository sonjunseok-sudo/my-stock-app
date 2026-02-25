import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 앱 설정 및 세션 초기화 ---
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# 핵심: 페이지 이동 및 자동 조회를 위한 세션 상태
if 'active_menu' not in st.session_state:
    st.session_state.active_menu = "🔍 개별 분석"
if 'target_stock' not in st.session_state:
    st.session_state.target_stock = '삼성전자'
if 'auto_run' not in st.session_state:
    st.session_state.auto_run = False

# CSS: 제목 한 줄 고정 및 버튼 디자인
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem !important; font-weight: 800; white-space: nowrap; text-align: center; margin-bottom: 20px; color: #1f2937; }
    [data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .buy-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 15px; }
    .badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; background-color: #eff6ff; color: #1e40af; }
    </style>
    <h1 class="main-title">📈 손선생 주식 분석</h1>
""", unsafe_allow_html=True)

# --- 2. 도구 함수 ---
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

# 종목 리스트 (필요한 만큼 유지하세요)
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '현대차': '005380', 
    '현대위아': '011210', 'LG화학': '051910', '포스코퓨처엠': '003670', '셀트리온': '068270'
    # ... 리스트 생략 가능
}

# --- 3. 메뉴 구성 (탭 대신 라디오 버튼으로 탭 효과 구현 - 이동이 확실함) ---
menu_list = ["🔍 개별 분석", "🚀 AI 매수 추천 스캐너"]
selected_menu = st.radio("Menu", menu_list, index=menu_list.index(st.session_state.active_menu), horizontal=True, label_visibility="collapsed")
st.session_state.active_menu = selected_menu # 선택 상태 저장

# ==========================================
# 메뉴 1: 개별 분석 (조회 안 되는 문제 해결)
# ==========================================
if selected_menu == "🔍 개별 분석":
    all_names = list(KOSPI_200.keys())
    idx = all_names.index(st.session_state.target_stock) if st.session_state.target_stock in all_names else 0
    selected_name = st.selectbox("분석할 종목을 검색하세요:", all_names, index=idx)
    code = KOSPI_200[selected_name]

    # [분석 시작] 버튼이 눌렸거나, 스캐너에서 넘어왔을 때(auto_run) 실행
    if st.button("📊 실시간 데이터 분석 시작") or st.session_state.auto_run:
        st.session_state.auto_run = False # 자동 실행 후 해제
        with st.spinner(f'{selected_name} 분석 중...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            
            if not df.empty and len(df) >= 25:
                # 데이터 가공
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 지표 카드
                c1, c2, c3 = st.columns(3)
                c1.metric("현재가", f"{df['Close'].iloc[-1]:,.0f}원")
                c2.metric("현재 RSI", f"{df['RSI'].iloc[-1]:.1f}")
                vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2]) * 100
                c3.metric("거래량대비", f"{vol_ratio:.0f}%")

                st.markdown(f"### 💡 {selected_name} 상세 차트 및 분석")
                
                # 🌟 차트 출력 코드 (Plotly)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                df_r = df.iloc[-60:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='종가', line=dict(color='gray')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10일선', line=dict(color='red')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20일선', line=dict(color='orange')), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='거래량', marker_color='blue'), row=2, col=1)
                
                fig.update_layout(template="plotly_white", height=550, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("데이터를 가져오지 못했습니다.")

# ==========================================
# 메뉴 2: 스캐너 (자동 이동 및 지표 복구)
# ==========================================
else:
    st.write("200개 종목 중 최적의 매수 타이밍 종목을 스캔합니다.")
    range_opt = st.radio("범위 선택:", ["1~50위", "51~100위", "101~150위", "151~200위"], horizontal=True)
    
    if st.button("🚀 매수 신호 스캔 시작"):
        all_items = list(KOSPI_200.items())
        idx_map = {"1~50위": (0,50), "51~100위": (50,100), "101~150위": (100,150), "151~200위": (150,200)}
        s, e = idx_map[range_opt]
        results = []
        bar = st.progress(0)
        
        for i, (name, code) in enumerate(all_items[s:e]):
            try:
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    df_s['MA10'] = df_s['Close'].rolling(10).mean()
                    df_s['MA20'] = df_s['Close'].rolling(20).mean()
                    if df_s['MA10'].iloc[-2] <= df_s['MA20'].iloc[-2] and df_s['MA10'].iloc[-1] > df_s['MA20'].iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2]) * 100
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/50)
        
        if results:
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                with st.container():
                    st.markdown(f"""
                    <div class="buy-card">
                        <b>{r['name']} ({r['code']})</b> | {r['price']:,.0f}원<br>
                        <span class="badge">1. 골든크로스 발생 ✅</span>
                        <span class="badge">2. 거래량 {r['vol']:.0f}% 🔥</span>
                        <span class="badge">3. RSI {r['rsi']:.1f} 🌡️</span><br>
                        <small>전일 수급: 기관 {r['inst']:,} | 외인 {r['frgn']:,}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    # 🌟 클릭 시 자동 이동 + 자동 조회 마법의 버튼
                    if st.button(f"🔍 {r['name']} 분석하기", key=f"go_{r['code']}"):
                        st.session_state.target_stock = r['name']
                        st.session_state.active_menu = "🔍 개별 분석"
                        st.session_state.auto_run = True # 다음 화면에서 바로 조회하게 함
                        st.rerun()
        else: st.warning("신호가 발견되지 않았습니다.")
