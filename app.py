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

# 🌟 진짜 200개 꽉꽉 채운 우량주 풀버전 리스트
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
    '오리온': '271560', '현대백화점': '069960', '한전기술': '052690', '한전KPS': '051600', 
    '하이트진로': '000080', '롯데칠성': '005300', '한솔케미칼': '014680', '포스코인터내셔널': '047050', 
    '호텔신라': '008770', '현대위아': '011210', 'DL': '000210', 'DL이앤씨': '375500', 
    '신세계인터내셔날': '031430', 'HDC': '012630', '농심': '004370', '오뚜기': '007310', 
    '아세아제지': '002310', 'HD한국조선해양': '009540', 'HD현대': '267250', '두산밥캣': '241560', 
    'GS건설': '006360', '영풍': '000670', 'LX인터내셔널': '001120', '쌍용C&E': '003410', 
    'CJ대한통운': '000120', '현대차증권': '001500', '제일기획': '030000', 'LG유플러스': '032640', 
    '동원시스템즈': '014820', 'HD현대미포': '010620', '한화': '000880', 'GS리테일': '007070',
    '현대엘리베이터': '017800', '금호석유': '011780', '효성티앤씨': '298020', '현대로템': '064350',
    'LIG넥스원': '079550', 'LS': '006260', 'LS ELECTRIC': '010120', '농심홀딩스': '072710',
    '풍산': '103140', 'KCC글라스': '344820', '현대그린푸드': '453340', '한국가스공사': '036460',
    'HD현대인프라코어': '042670', '대웅제약': '069620', '종근당': '185750', '보령': '003850',
    'HL만도': '204320', 'F&F': '383220', 'SK바이오팜': '326030', 'SK바이오사이언스': '302440',
    '카카오뱅크': '323410', '카카오페이': '377300', '넷마블': '251270', '펄어비스': '263750',
    '에코프로머티': '450080', '두산로보틱스': '454910', '금양': '001570', '코스모신소재': '005070',
    '코스모화학': '005420', '이수스페셜티케미컬': '457190', 'TCC스틸': '002710', '삼양식품': '003230',
    '빙그레': '005180', '매일유업': '267980', '롯데웰푸드': '280360', 'SPC삼립': '005610',
    '현대오토에버': '307950', 'HLB': '028300', '셀트리온제약': '068760', '알테오젠': '196170',
    '엔켐': '348370', 'HPSP': '403870', '리노공업': '058470', '동진쎄미켐': '005290',
    '솔브레인': '357780', '솔루스첨단소재': '336370', 'SK아이이테크놀로지': '361610', '롯데에너지머티리얼즈': '020150',
    'WCP': '393890', '천보': '278280', '에코프로': '086520', '에코프로비엠': '247540',
    '엘앤에프': '066970', '포스코엠텍': '009520', '포스코스틸리온': '058430', '세아베스틸지주': '001430',
    '세아제강': '306200', '동국제강': '460860', 'KG모빌리티': '003620', '에스엘': '005850',
    '서연이화': '200880', '화신': '010690', '성우하이텍': '015750', '아주산업': '013310',
    '경창산업': '024910', '피에이치에이': '043370', '대원강업': '000430', 'SJM': '123700',
    '지엠비코리아': '013870', 'SNT다이내믹스': '003570', 'SNT모티브': '064960', '한화시스템': '272210',
    '한국항공우주': '047810', 'JYP Ent.': '035900', '에스엠': '041510', '와이지엔터테인먼트': '122870',
    '하이브': '352820', 'CJ ENM': '035760', '스튜디오드래곤': '253450', 'SOOP': '067160',
    '컴투스': '078340', '위메이드': '112040', '넥슨게임즈': '225570', '카카오게임즈': '293490',
    '골프존': '215000', 'BGF': '027410', 'NH투자증권': '005940', '메리츠금융지주': '138040',
    'DGB금융지주': '139130', 'JB금융지주': '175330', 'BNK금융지주': '138930', '한화생명': '088350',
    '동양생명': '082640', '롯데손해보험': '000400', '한화손해보험': '000370', 'DB금융투자': '016610',
    '대신증권': '003540', '유안타증권': '003470', '신영증권': '001720', '부국증권': '001270'
}

st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

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

st.markdown('<div class="single-line-title">📈 손선생 주식 분석</div>', unsafe_allow_html=True)
st.caption("코스피/코스닥 핵심 우량주 매수 타이밍 AI 스캐너")
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 개별 종목 분석", "🚀 AI 매수 추천 스캐너"])

# ==========================================
# 탭 1: 개별 종목 분석 (기존 유지)
# ==========================================
with tab1:
    selected_name = st.selectbox("분석할 종목을 검색하세요:", list(KOSPI_200.keys()), key="select_stock")
    selected_code = KOSPI_200[selected_name]

    if st.button("📊 AI 데이터 분석 시작"):
        with st.spinner(f'🌐 {selected_name} 데이터를 분석 중입니다...'):
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
                    st.error("🚨 **[확정 매도: 데드크로스]** 10일선이 20일선을 하향 돌파했습니다! 매도를 고려하세요.")
                elif prev_close > prev_ma10 and last_close < last_ma10:
                    st.warning(f"🟡 **[주의 매도: 10일선 이탈]** 주가가 10일선 아래로 내려왔습니다.")
                elif last_rsi >= 75:
                    st.warning(f"🔥 **[분할 매도: RSI 과열]** RSI가 {last_rsi:.1f}로 과열권입니다.")
                elif last_cross == 2:
                    if vol_ratio >= 200:
                        st.success("🚀 **[강력 매수: 골든크로스 + 거래량 폭발]** 상향 돌파와 거래량이 터졌습니다!")
                    else:
                        st.success("✨ **[신규 매수: 골든크로스]** 10일선이 20일선을 뚫고 올라갔습니다.")
                else:
                    st.info("✅ **[관망]** 현재 특별한 매수/매도 신호가 없습니다.")

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
                                  hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("데이터를 불러오는 데 실패했습니다.")


# ==========================================
# 탭 2: 🌟 업그레이드된 분할 스캐너
# ==========================================
with tab2:
    st.write("우량주 200종목 중 현재 **'골든크로스(매수 신호)'가 발생한 종목**을 찾아냅니다.")
    
    # 스캔 범위 선택 UI (라디오 버튼)
    scan_option = st.radio(
        "⏱️ 스캔 범위를 선택하세요 (시간 단축):",
        ["🥇 상위 100종목 (1~100위)", "🥈 하위 100종목 (101~200위)", "🔥 전체 200종목 (약 30초 소요)"],
        horizontal=False
    )
    
    if st.button("🚀 매수 신호 스캔 시작"):
        
        # 전체 리스트를 순서대로 가져와서 자르기
        all_items = list(KOSPI_200.items())
        
        if "상위 100종목" in scan_option:
            target_items = all_items[:100]
        elif "하위 100종목" in scan_option:
            target_items = all_items[100:]
        else:
            target_items = all_items
            
        total_stocks = len(target_items)
        buy_candidates = []
        
        # 진행률 바 
        progress_text = f"총 {total_stocks}개 종목 데이터를 수집하고 분석 중입니다..."
        my_bar = st.progress(0, text=progress_text)
        
        # 속도를 위해 최근 60일치만 가져옴
        scan_start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        for i, (name, code) in enumerate(target_items):
            try:
                df_scan = fdr.DataReader(code, scan_start_date)
                
                if df_scan is not None and len(df_scan) >= 25:
                    df_scan['MA10'] = df_scan['Close'].rolling(window=10).mean()
                    df_scan['MA20'] = df_scan['Close'].rolling(window=20).mean()
                    df_scan['Position'] = np.where(df_scan['MA10'] > df_scan['MA20'], 1, -1)
                    df_scan['Signal'] = df_scan['Position'].diff()
                    
                    last_cross_scan = df_scan['Signal'].iloc[-1]
                    
                    # 골든크로스 발생 시
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
                pass 
            
            my_bar.progress((i + 1) / total_stocks, text=f"{name} 분석 중... ({i+1}/{total_stocks})")
            
        my_bar.empty() # 게이지 바 숨기기
        
        # 결과 출력
        st.markdown("---")
        if len(buy_candidates) > 0:
            st.success(f"🎉 스캔 완료! 총 **{len(buy_candidates)}**개의 매수 신호 종목을 찾았습니다.")
            buy_candidates = sorted(buy_candidates, key=lambda x: x['vol_ratio'], reverse=True)
            
            for item in buy_candidates:
                if item['vol_ratio'] >= 200:
                    st.info(f"🚀 **{item['name']}** (현재가: {item['close']:,.0f}원) | 거래량 5일평균 대비: **{item['vol_ratio']:.0f}%** 터짐!")
                else:
                    st.write(f"✨ **{item['name']}** (현재가: {item['close']:,.0f}원) | 거래량 5일평균 대비: {item['vol_ratio']:.0f}%")
        else:
            st.warning("🧐 현재 선택하신 범위 내에서는 매수 신호(골든크로스)가 발생한 종목이 없습니다.")
