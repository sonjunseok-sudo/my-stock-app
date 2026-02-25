import streamlit as st
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 차트 한글 깨짐 방지용 설정
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

# 🌟 핵심 기술: 코스피 전 종목 리스트 불러오기 (앱이 느려지지 않게 기억해둠)
@st.cache_data
def get_kospi_list():
    df = fdr.StockListing('KOSPI')
    stock_dict = {}
    # "삼성전자 (005930)" 형태로 검색하기 좋게 만듭니다.
    for idx, row in df.iterrows():
        stock_dict[f"{row['Name']} ({row['Code']})"] = row['Code']
    return stock_dict

# ----------------- UI 시작 -----------------
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈")
st.title("📈 손선생 주식 분석")
st.write("코스피(KOSPI) 전 종목의 매수/매도 타이밍을 분석합니다.")

# 코스피 종목 리스트 가져오기
stock_dict = get_kospi_list()

# 종목 선택 창 (글자를 치면 자동검색 됩니다!)
selected_display = st.selectbox("🔍 분석할 종목의 이름을 검색하거나 선택하세요:", list(stock_dict.keys()))

# 선택한 종목의 이름과 코드 분리하기
selected_code = stock_dict[selected_display]
selected_name = selected_display.split(" (")[0]

if st.button("📊 AI 분석 시작"):
    with st.spinner(f'{selected_name} 데이터를 불러오고 분석하는 중입니다...'):
        # 1. 데이터 가져오기 (최근 1년)
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        df = fdr.DataReader(selected_code, start_date)
        
        if df is not None and len(df) >= 25:
            # 2. 지표 계산
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
            df['RSI'] = calculate_rsi(df)
            
            # 3. 최신 데이터 추출
            last_close = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2]
            last_ma10 = df['MA10'].iloc[-1]
            prev_ma10 = df['MA10'].iloc[-2]
            last_rsi = df['RSI'].iloc[-1]
            last_volume = df['Volume'].iloc[-1]
            avg_volume = df['Vol_MA5'].iloc[-2]
            vol_ratio = (last_volume / avg_volume * 100) if avg_volume > 0 else 0
            
            # 4. 신호 교차 계산
            df['Position'] = np.where(df['MA10'] > df['MA20'], 1, -1)
            df['Signal'] = df['Position'].diff()
            last_cross = df['Signal'].iloc[-1]

            # 5. 대시보드 요약 정보 표시
            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", f"{last_close:,.0f}원")
            col2.metric("현재 RSI", f"{last_rsi:.1f}")
            col3.metric("거래량 (5일평균 대비)", f"{vol_ratio:.1f}%")

            st.markdown("---")
            st.subheader(f"💡 {selected_name} 매매 타이밍 분석")

            # 6. 매수/매도 로직 판단 및 출력
            if last_cross == -2:
                st.error("🚨 [확정 매도: 데드크로스] 10일선이 20일선을 하향 돌파했습니다! 추세가 꺾였으니 매도를 강력히 고려하세요.")
            elif prev_close > prev_ma10 and last_close < last_ma10:
                st.warning(f"🟡 [주의 매도: 10일선 이탈] 주가가 10일선({last_ma10:,.0f}원) 아래로 내려왔습니다. 수익 실현이나 손절을 준비하세요.")
            elif last_rsi >= 75:
                st.warning(f"🔥 [분할 매도: RSI 과열] RSI가 {last_rsi:.1f}로 과열권입니다. 욕심을 버리고 일부 익절하세요.")
            elif last_cross == 2:
                if vol_ratio >= 200:
                    st.success("🚀 [강력 매수: 골든크로스 + 거래량 폭발] 10일선 상향 돌파와 함께 거래량이 터졌습니다! 신뢰도가 매우 높습니다.")
                else:
                    st.success("✨ [신규 매수: 골든크로스] 10일선이 20일선을 뚫고 올라갔습니다. 상승 추세의 시작입니다.")
            else:
                st.info("✅ 현재 특별한 매수/매도 신호가 발생하지 않았습니다. 관망하세요.")

            # 7. 2단 차트 그리기
            st.markdown("---")
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
            
            # 상단: 주가 차트
            ax1.plot(df.index[-60:], df['Close'].iloc[-60:], label='Price', color='gray', alpha=0.5)
            ax1.plot(df.index[-60:], df['MA10'].iloc[-60:], label='MA10', color='red')
            ax1.plot(df.index[-60:], df['MA20'].iloc[-60:], label='MA20', color='orange')
            ax1.set_title(f'{selected_code} Stock Analysis')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 하단: 거래량 막대
            colors = ['red' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'blue' for i in range(len(df)-60, len(df))]
            ax2.bar(df.index[-60:], df['Volume'].iloc[-60:], color=colors, alpha=0.7)
            ax2.axhline(avg_volume, color='green', linestyle='--', label='5-Day Avg Vol')
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
        else:
            st.error("데이터를 불러오는 데 실패했습니다.")
