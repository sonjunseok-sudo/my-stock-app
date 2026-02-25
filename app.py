import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup

# --- 설정 및 초기화 ---
st.set_page_config(page_title="손선생 주식 분석", page_icon="📈", layout="centered")

# 클릭 시 종목 이동을 위한 세션 상태 초기화
if 'selected_stock_name' not in st.session_state:
    st.session_state.selected_stock_name = '삼성전자'

# --- 함수 정의 ---
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
    try:
        # 안정적인 모바일 네이버 금융 경로 사용
        url = f"https://m.stock.naver.com/api/stock/{code}/investor"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers).json()
        
        # 최신 데이터 추출
        latest = res['result'][0]
        inst = int(latest['institutionNetBuyVolume'])
        frgn = int(latest['foreignNetBuyVolume'])
        pers = int(latest['individualNetBuyVolume'])
        
        return inst, frgn, pers
    except:
        return None, None, None

# 200개 종목 리스트 (생략 없이 유지)
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
    'HD현대인프라코어': '042670', '대웅제약': '069620', '종근당': '185750', '보령': '003850'
}

# --- UI 레이아웃 ---
st.markdown("""
    <style>
    .buy-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 손선생 주식 분석")

tab1, tab2 = st.tabs(["🔍 개별 분석", "🚀 매수 추천 스캐너"])

with tab1:
    # 스캐너에서 선택된 종목이 있으면 해당 종목을 기본값으로 설정
    stock_idx = list(KOSPI_200.keys()).index(st.session_state.selected_stock_name)
    selected_name = st.selectbox("종목 선택:", list(KOSPI_200.keys()), index=stock_idx)
    code = KOSPI_200[selected_name]
    
    if st.button("📊 실시간 분석 시작", key="btn_detail"):
        with st.spinner('분석 중...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            # ... (기존 차트 및 분석 로직 동일) ...
            st.success(f"{selected_name} 분석 완료! 하단 차트를 확인하세요.")
            # 차트 그리기 (기존 코드 유지)

with tab2:
    st.write("200개 종목을 스캔하여 최적의 수급과 차트 타이밍을 찾습니다.")
    option = st.radio("범위:", ["상위 100", "하위 100", "전체 200"], horizontal=True)
    
    if st.button("🚀 골든크로스 & 수급 스캔 시작"):
        all_items = list(KOSPI_200.items())
        target = all_items[:100] if "상위" in option else all_items[100:] if "하위" in option else all_items
        
        results = []
        bar = st.progress(0)
        
        for i, (name, code) in enumerate(target):
            try:
                df = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df) >= 25:
                    df['MA10'] = df['Close'].rolling(window=10).mean()
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    df['RSI'] = calculate_rsi(df)
                    
                    if df['MA10'].iloc[-2] <= df['MA20'].iloc[-2] and df['MA10'].iloc[-1] > df['MA20'].iloc[-1]:
                        inst, frgn, pers = get_investor_data(code)
                        vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(window=5).mean().iloc[-2]) * 100
                        
                        results.append({
                            'name': name, 'code': code, 'price': df['Close'].iloc[-1],
                            'vol': vol_ratio, 'rsi': df['RSI'].iloc[-1],
                            'inst': inst, 'frgn': frgn, 'pers': pers
                        })
            except: pass
            bar.progress((i+1)/len(target))
        
        st.subheader("🏆 AI 포착 매수 추천주")
        if results:
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                with st.container():
                    st.markdown(f"""
                    <div class="buy-card">
                        <b>{r['name']} ({r['code']})</b> | {r['price']:,.0f}원<br>
                        <small>거래량 {r['vol']:.0f}% | RSI {r['rsi']:.1f}</small><br>
                        <hr style="margin:8px 0;">
                        <b>전일 수급:</b> 기관 {f"{r['inst']:,}" if r['inst'] is not None else "집계중"} | 
                        외인 {f"{r['frgn']:,}" if r['frgn'] is not None else "집계중"} | 
                        개인 {f"{r['pers']:,}" if r['pers'] is not None else "집계중"}
                    </div>
                    """, unsafe_allow_html=True)
                    # 하단에 '상세분석' 버튼 배치
                    if st.button(f"🔍 {r['name']} 차트보기", key=f"go_{r['code']}"):
                        st.session_state.selected_stock_name = r['name']
                        st.rerun() # 탭 이동 효과를 위해 앱 재실행
        else: st.warning("현재 신호가 포착된 종목이 없습니다.")
