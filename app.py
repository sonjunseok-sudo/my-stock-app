import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# KOSPI 핵심 우량주 리스트
KOSPI_200 = {
    '삼성전자': '005930', 'SK하이닉스': '000660', 'LG에너지솔루션': '373220', '삼성바이오로직스': '207940',
    '현대차': '005380', '기아': '000270', '셀트리온': '068270', 'POSCO홀딩스': '005490',
    'NAVER': '035420', '포스코퓨처엠': '003670', '삼성SDI': '006400', '카카오': '035720',
    'LG화학': '051910', '삼성물산': '028260', 'KB금융': '105560', '현대모비스': '012330',
    '신한지주': '055550', 'LG전자': '066570', '삼성화재': '000810', '삼성생명': '032830',
    '하나금융지주': '086790', '한국전력': '015760', 'KT&G': '033780', 'HMM': '011200',
    '두산에너빌리티': '034020', '한미반도체': '042700', '현대글로비스': '086280', '고려아연': '010130',
    '삼성SDS': '018260', '삼성전기': '009150', 'HD현대중공업': '329180', 'LG': '003550',
    '우리금융지주': '316140', '기업은행': '024110', '엔씨소프트': '036570', '한화솔루션': '009830',
    '아모레퍼시픽': '090430', '롯데케미칼': '011170', '현대제철': '004020', 'S-Oil': '010950',
    'KT': '030200', '유한양행': '000100', '크래프톤': '259960', '한온시스템': '018880',
    '두산': '000150', '한화오션': '042660', '한화에어로스페이스': '012450', 'KCC': '002380'
}

st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# 고급 CSS UI 디자인
st.markdown("""
    <style>
    .single-line-title { white-space: nowrap; font-size: 28px; font-weight: 800; letter-spacing: -1.5px; color: #1f2937; margin-bottom: 5px; }
    .single-line-subtitle { white-space: nowrap; font-size: 20px; font-weight: 700; margin-top: 20px; margin-bottom: 15px; color: #374151; }
    [data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 15px 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; color: #111827; }
    [data-testid="baseButton-secondary"] { background-color: #2563eb !important; color: white !important; border-radius: 10px !important; font-size: 18px !important; font-weight: 800 !important; border: none !important; padding: 12px 20px !important; width: 100% !important; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3); transition: all 0.2s; }
    [data-testid="baseButton-secondary"]:hover { background-color: #1d4ed8 !important; transform: translateY(-2px); }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<div class="single-line-title">📈 손선생 주식 분석</div>', unsafe_allow_html=True)
st.caption("코스피 핵심 우량주 매수/매도 타이밍 AI 대시보드")
st.markdown("<br>", unsafe_allow_html=True)

# 🌟 상단 탭(Tab) 메뉴 생성
tab1, tab2 = st.tabs(["🔍 개별 종목 분석", "🚀 AI 매수 추천 스캐너"])

# ==========================================
# 탭 1: 개별 종목 분석 (기존 기능)
# ==========================================
with tab1:
    selected_name = st.selectbox("분석할 종목을 검색하세요:", list(KOSPI_200.keys()), key="select_stock")
    selected_code = KOSPI_200[selected_name]

    if st.button("📊 AI 데이터 분석 시작"):
        with st.spinner(f'🌐 {selected_name} 최신 데이터를 분석 중입니다...'):
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            df = fdr.DataReader(selected_code, start_date)
            
            if df is not None and len(df) >= 25:
                df['MA10'] = df['Close'].rolling(window=10).mean()
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['Vol_MA5'] = df['Volume'].rolling(window=5).mean()
                df['RSI'] = calculate_rsi(df)
                
                last_close = df['Close'].iloc[-1]
                prev_close = df['Close'].iloc[-2]
                last_ma10 = df['MA10'].iloc[-1]
                prev_ma10 = df['MA10'].iloc[-2]
                last_rsi = df['RSI'].iloc[-1]
                last_volume = df['Volume'].iloc[-1]
                avg_volume = df['Vol_MA5'].iloc[-2]
                vol_ratio = (last_volume / avg_volume * 100) if avg_volume > 0 else 0
                
                df['Position'] = np.where(df['MA10'] > df['MA20'], 1, -1)
                df['Signal'] = df['Position'].diff()
                last_cross = df['Signal'].iloc[-1]

                col1, col2, col3 = st.columns(3)
                col1.metric("현재가", f"{last_close:,.0f}원")
                col2.metric("현재 RSI", f"{last_rsi:.1f}")
                col3.metric("거래량(대비)", f"{vol_ratio:.0f}%")

                st.markdown("---")
                st.markdown(f'<div class="single-line-subtitle">💡 {selected_name} 매매 타이밍 분석</div>', unsafe_allow_html=True)

                if last_cross == -2:
                    st.error("🚨 **[확정 매도: 데드크로스]** 10일선이 20일선을 하향 돌파했습니다! 매도를 강력히 고려하세요.")
                elif prev_close > prev_ma10 and last_close < last_ma10:
                    st.warning(f"🟡 **[주의 매도: 10일선 이탈]** 주가가 10일선({last_ma10:,.0f}원) 아래로 내려왔습니다. 손절을 준비하세요.")
                elif last_rsi >= 75:
                    st.warning(f"🔥 **[분할 매도: RSI 과열]** RSI가 {last_rsi:.1f}로 과열권입니다. 일부 익절하세요.")
                elif last_cross == 2:
                    if vol_ratio >= 200:
                        st.success("🚀 **[강력 매수: 골든크로스 + 거래량 폭발]** 10일선 상향 돌파와 거래량이 터졌습니다!")
                    else:
                        st.success("✨ **[신규 매수: 골든크로스]** 10일선이 20일선을 뚫고 올라갔습니다. 상승 추세 시작입니다.")
                else:
                    st.info("✅ **[관망]** 현재 특별한 매수/매도 신호가 발생하지 않았습니다.")

                st.markdown("---")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
                df_recent = df.iloc[-60:]
                
                fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['Close'], mode='lines', name='종가', line=dict(color='#6b7280', width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['MA10'], mode='lines', name='10일선', line=dict(color='#ef4444', width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['MA20'], mode='lines', name='20일선', line=dict(color='#f59e0b', width=2)), row=1, col=1)

                colors = ['#ef4444' if row['Close'] >= row['Open'] else '#3b82f6' for _, row in df_recent.iterrows()]
                fig.add_trace(go.Bar(x=df_recent.index, y=df_recent['Volume'], name='거래량', marker_color=colors), row=2, col=1)
                fig.add_hline(y=avg_volume, line_dash="dash", line_color="#10b981", row=2, col=1)

                fig.update_layout(template="plotly_white", height=550, margin=dict(l=5, r=5, t=10, b=10),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                  hovermode="x unified", hoverlabel=dict(bgcolor="white", font_size=14))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("데이터를 불러오는 데 실패했습니다.")


# ==========================================
# 탭 2: AI 매수 추천 스캐너 (신규 기능!)
# ==========================================
with tab2:
    st.write("리스트에 있는 모든 우량주를 스캔하여 **현재 '골든크로스(매수 신호)'가 발생한 종목**만 찾아냅니다.")
    
    if st.button("🚀 전체 종목 매수 신호 스캔 시작"):
        buy_candidates = []
        total_stocks = len(KOSPI_200)
        
        # 진행률 바 (Progress Bar)
        progress_text = "전체 종목 데이터를 수집하고 분석 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        # 스캔 속도를 높이기 위해 최근 60일 데이터만 가져옵니다.
        scan_start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        for i, (name, code) in enumerate(KOSPI_200.items()):
            try:
                # 데이터 수집
                df_scan = fdr.DataReader(code, scan_start_date)
                
                if df_scan is not None and len(df_scan) >= 25:
                    df_scan['MA10'] = df_scan['Close'].rolling(window=10).mean()
                    df_scan['MA20'] = df_scan['Close'].rolling(window=20).mean()
                    df_scan['Position'] = np.where(df_scan['MA10'] > df_scan['MA20'], 1, -1)
                    df_scan['Signal'] = df_scan['Position'].diff()
                    
                    last_cross_scan = df_scan['Signal'].iloc[-1]
                    
                    # 🌟 골든크로스(매수 신호)가 발생한 종목만 수집!
                    if last_cross_scan == 2:
                        last_close_scan = df_scan['Close'].iloc[-1]
                        vol_ma5 = df_scan['Volume'].rolling(window=5).mean().iloc[-2]
                        vol_ratio_scan = (df_scan['Volume'].iloc[-1] / vol_ma5 * 100) if vol_ma5 > 0 else 0
                        
                        buy_candidates.append({
                            'name': name,
                            'close': last_close_scan,
                            'vol_ratio': vol_ratio_scan
                        })
            except:
                pass # 에러가 나는 종목은 조용히 넘어갑니다.
            
            # 진행률 업데이트
            my_bar.progress((i + 1) / total_stocks, text=f"{name} 분석 중... ({i+1}/{total_stocks})")
            
        # 스캔이 끝나면 진행률 바 지우기
        my_bar.empty()
        
        # 🌟 결과 출력
        st.markdown("---")
        if len(buy_candidates) > 0:
            st.success(f"🎉 스캔 완료! 총 **{len(buy_candidates)}**개의 매수 신호 종목을 찾았습니다.")
            
            # 거래량이 폭발한 순서대로 정렬해서 보여줍니다.
            buy_candidates = sorted(buy_candidates, key=lambda x: x['vol_ratio'], reverse=True)
            
            for item in buy_candidates:
                if item['vol_ratio'] >= 200:
                    st.info(f"🚀 **{item['name']}** (현재가: {item['close']:,.0f}원) | 거래량 5일평균 대비: **{item['vol_ratio']:.0f}%** 터짐!")
                else:
                    st.write(f"✨ **{item['name']}** (현재가: {item['close']:,.0f}원) | 거래량 5일평균 대비: {item['vol_ratio']:.0f}%")
        else:
            st.warning("🧐 현재 장에서는 확실한 매수 신호(골든크로스)가 발생한 종목이 없습니다.")
