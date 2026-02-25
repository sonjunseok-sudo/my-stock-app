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

            # 5. 대시보드 요약 정보 표시 (Metrics)
            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", f"{last_close:,.0f}원")
            col2.metric("현재 RSI", f"{last_rsi:.1f}")
            col3.metric("거래량 (5일평균 대비)", f"{vol_ratio:.1f}%")

            st.markdown("---")
            st.subheader("💡 AI 매매 타이밍 분석")

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

            # 7. 2단 차트 그리기 (텔레그램과 동일)
            st.markdown("---")
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
            
            # 상단: 주가 차트 (영어 제목으로 한글 깨짐 방지)
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
            
            # 차트를 웹 화면에 출력!
            st.pyplot(fig)
            
        else:
            st.error("데이터를 불러오는 데 실패했습니다.")
