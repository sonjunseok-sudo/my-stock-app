import streamlit as st
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 스트림릿 클라우드(리눅스) 환경에서 한글 깨짐 방지를 위해 차트 폰트는 기본으로 둡니다.
plt.rcParams['axes.unicode_minus'] = False

# RSI 계산 함수
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return 100 - (100 / (1 + RS))

# UI 시작
st.set_page_config(page_title="주식 AI 비서", page_icon="🤖")
st.title("🤖 나만의 주식 AI 비서")
st.write("종목을 선택하면 현재 매수/매도 타이밍인지 분석해 줍니다.")

# 타겟 종목 리스트 (텔레그램에서 쓰던 25개 종목)
TARGET_STOCKS = {
    '005930': '삼성전자', '000660': 'SK하이닉스', '035420': 'NAVER',
    '005380': '현대차', '086280': '현대글로비스', '012330': '현대모비스',
    '000270': '기아', '042700': '한미반도체', '006400': '삼성SDI',
    '002380': 'KCC', '015760': '한국전력', '012450': '한화에어로스페이스',
    '034020': '두산에너빌리티', '105560': 'KB금융', '373220': 'LG에너지솔루션',
    '329180': 'HD현대중공업', '042660': '한화오션', '018880': '한온시스템',
    '000150': '두산', '055550': '신한지주', '066570': 'LG전자', 
    '003550': 'LG', '032830': '삼성생명', '000810': '삼성화재', '033780': 'KT&G'
}

# 종목 선택 창
selected_name = st.selectbox("🔍 분석할 종목을 선택하세요:", list(TARGET_STOCKS.values()))
selected_code = [code for code, name in TARGET_STOCKS.items() if name == selected_name][0]

if st.button("📊 AI 분석 시작"):
    with st.spinner(f'{selected_
