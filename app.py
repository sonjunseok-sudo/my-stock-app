import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 설정 및 초기화 ---
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# 세션 상태 초기화 (종목 이동 및 선택 관리)
if 'target_stock' not in st.session_state:
    st.session_state.target_stock = '삼성전자'

# --- CSS: 제목 한 줄 고정 및 디자인 ---
st.markdown("""
    <style>
    /* 제목 한 줄 강제 고정 및 크기 조절 */
    .main-title {
        font-size: 2.2rem !important;
        font-weight: 800;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: center;
        margin-bottom: 20px;
    }
    .buy-card {
        background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    </style>
    <h1 class="main-title">📈 손선생 주식 분석</h1>
""", unsafe_allow_html=True)

# --- 주요 함수 ---
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return 100 - (100 / (1 + RS))

def get_investor_data(code):
    """수급 데이터 0 오류 해결: 모바일 API 경로 사용"""
    try:
        url = f"https://m.stock.naver.com/api/stock/{code}/investor"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        latest = res['result'][0]
        return (int(latest['institutionNetBuyVolume']), 
                int(latest['foreignNetBuyVolume']), 
                int(latest['individualNetBuyVolume']))
    except:
        return None, None, None

# KOSPI 200 종목 데이터 (예시로 상위 일부만 표기, 실제로는 전체 리스트 유지 권장)
KOSPI_DATA = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '삼성SDI': '006400', 'LG화학': '051910', '삼성물산': '028260'
    # ... (기존 종목 리스트 50개 이상 포함)
}

tab1, tab2 = st.tabs(["🔍 개별 분석", "🚀 매수 추천 스캐너"])

with tab1:
    # 스캐너에서 전달된 종목이 리스트에 있는지 확인 후 기본값 설정
    all_names = list(KOSPI_DATA.keys())
    default_idx = all_names.index(st.session_state.target_stock) if st.session_state.target_stock in all_names else 0
    
    selected_name = st.selectbox("분석할 종목을 선택하세요:", all_names, index=default_idx)
    code = KOSPI_DATA[selected_name]
    
    if st.button("📊 실시간 AI 분석 시작"):
        with st.spinner(f'{selected_name} 데이터를 불러오는 중...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            if not df.empty:
                df['MA10'] = df['Close'].rolling(window=10).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                rsi_val = calculate_rsi(df).iloc[-1]
                
                # 결과 출력
                st.subheader(f"💡 {selected_name} 분석 결과")
                if rsi_val > 70: st.warning(f"🔥 [매도 검토] RSI {rsi_val:.1f}로 과열 상태입니다.")
                elif rsi_val < 30: st.success(f"💎 [매수 검토] RSI {rsi_val:.1f}로 저평가 상태입니다.")
                else: st.info(f"✅ RSI {rsi_val:.1f}로 안정적인 흐름입니다.")
                
                # 차트 그리기
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="주가", line=dict(color='gray')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA10'], name="10일선", line=dict(color='red')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name="20일선", line=dict(color='orange')), row=1, col=1)
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="거래량"), row=2, col=1)
                fig.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.write("골든크로스가 발생한 유망 종목을 찾아냅니다.")
    # 50개씩 분리 선택
    range_option = st.radio("스캔 범위 선택 (50개 단위):", ["1~50위", "51~100위", "101~150위", "151~200위"], horizontal=True)
    
    if st.button("🚀 매수 신호 포착 시작"):
        all_items = list(KOSPI_DATA.items())
        # 범위 슬라이싱 로직
        idx_map = {"1~50위": (0,50), "51~100위": (50,100), "101~150위": (100,150), "151~200위": (150,200)}
        start, end = idx_map[range_option]
        target_list = all_items[start:end]
        
        results = []
        progress_bar = st.progress(0)
        
        for i, (name, code) in enumerate(target_list):
            try:
                df = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df) >= 21:
                    ma10_prev, ma20_prev = df['Close'].rolling(10).mean().iloc[-2], df['Close'].rolling(20).mean().iloc[-2]
                    ma10_curr, ma20_curr = df['Close'].rolling(10).mean().iloc[-1], df['Close'].rolling(20).mean().iloc[-1]
                    
                    # 골든크로스 조건
                    if ma10_prev <= ma20_prev and ma10_curr > ma20_curr:
                        inst, frgn, pers = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df['Close'].iloc[-1], 'inst': inst, 'frgn': frgn})
            except: pass
            progress_bar.progress((i + 1) / len(target_list))
            
        if results:
            for r in results:
                with st.container():
                    st.markdown(f"""
                    <div class="buy-card">
                        <b>{r['name']} ({r['code']})</b> | {r['price']:,.0f}원<br>
                        <small>기관: {r['inst'] if r['inst'] is not None else '집계중'} | 외인: {r['frgn'] if r['frgn'] is not None else '집계중'}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    # 상세 분석으로 이동하는 버튼
                    if st.button(f"🔍 {r['name']} 분석하기", key=f"move_{r['code']}"):
                        st.session_state.target_stock = r['name']
                        st.rerun()
        else:
            st.warning("선택한 범위 내에 현재 매수 신호가 발생한 종목이 없습니다.")
