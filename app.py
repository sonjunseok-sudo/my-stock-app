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

# KOSPI 200 하드코딩 리스트 (이전과 동일)
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
    '두산': '000150', '한화오션': '042660', '한화에어로스페이스': '012450', 'KCC': '002380',
    '현대해상': '001450', '코웨이': '021240', 'CJ': '001040', 'SK': '034730',
    'SK텔레콤': '017670', 'LG이노텍': '011070', '삼성엔지니어링': '028050', '삼성중공업': '010140',
    'GS': '078930', '미래에셋증권': '006800', '포스코DX': '022100', 'SKC': '011790',
    '삼성증권': '016360', '한국타이어앤테크놀로지': '161390', '대우건설': '047040', 'DB손해보험': '005830',
    '롯데지주': '004990', '한미사이언스': '008930', '삼성카드': '029780', '대한항공': '003490',
    '한국금융지주': '071050', '팬오션': '028670', '키움증권': '039490', '현대건설': '000720',
    '더존비즈온': '012510', 'DB하이텍': '000990', '신세계': '004170', '아모레G': '002790', 
    'BGF리테일': '282330', '이마트': '139480', '녹십자': '006280', '오리온홀딩스': '001800', 
    '오리온': '271560', '현대백화점': '069960', '한전KDN': '052690', '한전KPS': '051600', 
    '하이트진로': '000080', '롯데칠성': '005300', '한솔케미칼': '014680', '포스코인터내셔널': '047050', 
    '호텔신라': '008770', '현대위아': '011210', 'DL': '000210', 'DL이앤씨': '375500', 
    '신세계인터내셔날': '031430', 'HDC': '012630', '농심': '004370', '오뚜기': '007310', 
    '아세아제지': '002310', 'HD한국조선해양': '009540', 'HD현대': '267250', '두산밥캣': '241560', 
    'GS건설': '006360', '영풍': '000670', 'LX인터내셔널': '001120', '쌍용C&E': '003410', 
    'CJ대한통운': '000120', '현대차증권': '001500', '제일기획': '030000', 'LG유플러스': '032640', 
    '동원시스템즈': '014820', 'HD현대미포': '010620'
}

st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# CSS를 이용해 제목이 무조건 한 줄로 나오도록 강제 설정
st.markdown("""
    <style>
    .single-line-title {
        white-space: nowrap;
        font-size: 26px;
        font-weight: bold;
        letter-spacing: -1px;
    }
    .single-line-subtitle {
        white-space: nowrap;
        font-size: 20px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 한 줄로 출력되는 예쁜 메인 타이틀
st.markdown('<div class="single-line-title">📈 손선생 주식 분석</div>', unsafe_allow_html=True)
st.write("코스피 대표 우량주들의 매수/매도 타이밍을 분석합니다.")

# 종목 선택 창 (터치하고 글자를 치면 자동검색 됩니다!)
selected_name = st.selectbox("🔍 분석할 종목을 검색하세요 (예: 현대):", list(KOSPI_200.keys()))
selected_code = KOSPI_200[selected_name]

if st.button("📊 AI 분석 시작"):
    with st.spinner(f'{selected_name} 데이터를 분석하는 중입니다...'):
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
            col3.metric("거래량 (대비)", f"{vol_ratio:.1f}%")

            st.markdown("---")
            
            # 한 줄로 출력되는 서브 타이틀
            st.markdown(f'<div class="single-line-subtitle">💡 {selected_name} 매매 타이밍 분석</div>', unsafe_allow_html=True)

            if last_cross == -2:
                st.error("🚨 [확정 매도: 데드크로스] 10일선이 20일선을 하향 돌파했습니다! 매도를 강력히 고려하세요.")
            elif prev_close > prev_ma10 and last_close < last_ma10:
                st.warning(f"🟡 [주의 매도: 10일선 이탈] 주가가 10일선({last_ma10:,.0f}원) 아래로 내려왔습니다. 손절을 준비하세요.")
            elif last_rsi >= 75:
                st.warning(f"🔥 [분할 매도: RSI 과열] RSI가 {last_rsi:.1f}로 과열권입니다. 일부 익절하세요.")
            elif last_cross == 2:
                if vol_ratio >= 200:
                    st.success("🚀 [강력 매수: 골든크로스 + 거래량 폭발] 10일선 상향 돌파와 거래량이 터졌습니다!")
                else:
                    st.success("✨ [신규 매수: 골든크로스] 10일선이 20일선을 뚫고 올라갔습니다. 상승 추세 시작입니다.")
            else:
                st.info("✅ 현재 특별한 매수/매도 신호가 발생하지 않았습니다. 관망하세요.")

            st.markdown("---")
            
            # 🌟 터치/확대/숫자 확인이 가능한 고급 Plotly 차트
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, 
                                row_heights=[0.7, 0.3])

            # 상단: 주가 및 이동평균선
            df_recent = df.iloc[-60:] # 최근 60일치만
            
            fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['Close'], mode='lines', name='종가', line=dict(color='gray', width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['MA10'], mode='lines', name='10일선', line=dict(color='red', width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_recent.index, y=df_recent['MA20'], mode='lines', name='20일선', line=dict(color='orange', width=2)), row=1, col=1)

            # 하단: 거래량 막대 (상승=빨강, 하락=파랑)
            colors = ['#ff4d4d' if row['Close'] >= row['Open'] else '#4d79ff' for _, row in df_recent.iterrows()]
            fig.add_trace(go.Bar(x=df_recent.index, y=df_recent['Volume'], name='거래량', marker_color=colors), row=2, col=1)
            
            # 5일 평균 거래량 점선 표시
            fig.add_hline(y=avg_volume, line_dash="dash", line_color="green", row=2, col=1)

            # 차트 레이아웃(디자인) 설정
            fig.update_layout(
                height=500, 
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified" # 🌟 손가락을 대면 모든 숫자가 한 번에 뜨는 마법의 옵션
            )
            
            # 차트 출력
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("데이터를 불러오는 데 실패했습니다.")
