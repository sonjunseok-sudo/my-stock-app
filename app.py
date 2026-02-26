import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --- 1. 앱 설정 및 프리미엄 스타일 ---
st.set_page_config(page_title="SON STOCK PRO", page_icon="📈", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    .main-title { font-size: 2.2rem !important; font-weight: 800; text-align: center; color: #111827; white-space: nowrap; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #6b7280; font-size: 0.9rem; margin-bottom: 25px; }
    .metric-card { background: #ffffff; border: 1px solid #f3f4f6; border-radius: 16px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04); text-align: center; }
    .status-box { padding: 20px; border-radius: 16px; margin-bottom: 25px; font-weight: 700; text-align: center; font-size: 1.1rem; border: 1px solid #e5e7eb; }
    .indicator-container { display: flex; flex-direction: row; gap: 8px; margin: 12px 0; overflow-x: auto; white-space: nowrap; }
    .badge-premium { background: #f0f7ff; color: #0055d4; padding: 6px 12px; border-radius: 8px; font-size: 13px; font-weight: 700; border: 1px solid #dbeafe; display: inline-block; }
    .buy-card { background: #ffffff; border-radius: 14px; padding: 22px; margin-bottom: 16px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .supply-row { font-size: 13px; color: #4b5563; background: #f9fafb; padding: 10px 14px; border-radius: 10px; margin-top: 10px; }
    </style>
    <div class="main-title">SON STOCK PRO</div>
    <div class="sub-title">Ultra-Fast Hardcoded Terminal</div>
""", unsafe_allow_html=True)

# --- 2. 분석 엔진 ---
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

# 🌟 절대 에러 안 나는 하드코딩 우량주 리스트 (웹 통신 없음! 즉시 켜짐!)
STOCK_LIST = {
    '삼성전자':'005930', 'SK하이닉스':'000660', 'LG에너지솔루션':'373220', '삼성바이오로직스':'207940', '현대차':'005380', 
    '기아':'000270', '셀트리온':'068270', 'POSCO홀딩스':'005490', 'NAVER':'035420', '현대위아':'011210', 
    'LG화학':'051910', '포스코퓨처엠':'003670', '삼성SDI':'006400', '카카오':'035720', '삼성물산':'028260', 
    'KB금융':'105560', '현대모비스':'012330', '신한지주':'055550', 'LG전자':'066570', '삼성화재':'000810',
    '삼성생명':'032830', '하나금융지주':'086790', '한국전력':'015760', 'KT&G':'033780', 'HMM':'011200',
    '두산에너빌리티':'034020', '한미반도체':'042700', '현대글로비스':'086280', '고려아연':'010130', '삼성SDS':'018260',
    '삼성전기':'009150', 'HD현대중공업':'329180', 'LG':'003550', '우리금융지주':'316140', '기업은행':'024110',
    '엔씨소프트':'036570', '한화솔루션':'009830', '아모레퍼시픽':'090430', '롯데케미칼':'011170', '현대제철':'004020',
    'S-Oil':'010950', 'KT':'030200', '유한양행':'000100', '크래프톤':'259960', '한온시스템':'018880',
    '두산':'000150', '한화오션':'042660', '한화에어로스페이스':'012450', 'KCC':'002380', '현대해상':'001450',
    '코웨이':'021240', 'CJ':'001040', 'SK':'034730', 'SK텔레콤':'017670', 'LG이노텍':'011070',
    '삼성엔지니어링':'028050', '삼성중공업':'010140', 'GS':'078930', '미래에셋증권':'006800', '포스코DX':'022100',
    'SKC':'011790', '삼성증권':'016360', '한국타이어앤테크놀로지':'161390', '대우건설':'047040', 'DB손해보험':'005830',
    '롯데지주':'004990', '한미사이언스':'008930', '삼성카드':'029780', '대한항공':'003490', '한국금융지주':'071050',
    '팬오션':'028670', '키움증권':'039490', '현대건설':'000720', '에코프로비엠':'247540', '에코프로':'086520',
    'HLB':'028300', '알테오젠':'196170', '엔켐':'348370', 'HPSP':'403870', '리노공업':'058470',
    '셀트리온제약':'068760', '레인보우로보틱스':'277810', '동진쎄미켐':'005290', '솔브레인':'357780', '이오테크닉스':'039030',
    '신성델타테크':'065350', '클래시스':'214150', '휴젤':'145020', '삼천당제약':'000250', '카카오게임즈':'293490',
    '펄어비스':'263750', '위메이드':'112040', 'JYP Ent.':'035900', '에스엠':'041510', '와이지엔터테인먼트':'122870',
    '하이브':'352820', '더존비즈온':'012510', 'DB하이텍':'000990', '신세계':'004170', '아모레G':'002790', 
    'BGF리테일':'282330', '이마트':'139480', '녹십자':'006280', '오리온홀딩스':'001800', '오리온':'271560', 
    '현대백화점':'069960', '한전기술':'052690', '한전KPS':'051600', '하이트진로':'000080', '롯데칠성':'005300', 
    '한솔케미칼':'014680', '포스코인터내셔널':'047050', '호텔신라':'008770', 'DL':'000210', 'DL이앤씨':'375500', 
    '신세계인터내셔날':'031430', 'HDC':'012630', '농심':'004370', '오뚜기':'007310', '아세아제지':'002310', 
    'HD한국조선해양':'009540', 'HD현대':'267250', '두산밥캣':'241560', 'GS건설':'006360', '영풍':'000670', 
    'LX인터내셔널':'001120', '쌍용C&E':'003410', 'CJ대한통운':'000120', '에스원':'012750', '제일기획':'030000', 
    '현대미포조선':'010620', '현대로템':'064350', 'LIG넥스원':'079550', '한국항공우주':'047810', '한화시스템':'272210', 
    'LS':'006260', 'LS일렉트릭':'010120', '풍산':'103140', 'OCI홀딩스':'010060', '금호석유':'011780', 
    '효성티앤씨':'298020', '효성첨단소재':'298050', '코스모신소재':'005070', '코스모화학':'005420', '이수스페셜티케미컬':'457190',
    '동국제강':'460860', '세아베스틸지주':'001430', '세아제강':'306200', 'KG모빌리티':'003620', '에스엘':'005850', 
    '화신':'010690', '서연이화':'200880', '성우하이텍':'015750', '아진산업':'013310', '대원강업':'000430', 
    '한국가스공사':'036460', '지역난방공사':'071320', 'SK가스':'018670', 'E1':'017940', '현대그린푸드':'453340', 
    '농심홀딩스':'072710', '대상':'001680', '빙그레':'005180', '매일유업':'267980', '삼양식품':'003230',
    'SPC삼립':'005610', '롯데웰푸드':'280360', '크라운해태홀딩스':'000240', '동원F&B':'049770', '종근당':'185750', 
    '대웅제약':'069620', '보령':'003850', 'JW중외제약':'001060', '일동제약':'249420', '동아에스티':'170900', 
    '환인제약':'016580', '대원제약':'003220', '하나투어':'039130', '모두투어':'080160', '노랑풍선':'104620', 
    '참좋은여행':'094850', '파라다이스':'034230', 'GKL':'114090', '강원랜드':'035250', '롯데관광개발':'032350', 
    '신라교역':'004970', '동원산업':'006040', '사조산업':'007160', 'CJ프레시웨이':'051500', 'CJ ENM':'035760', 
    '스튜디오드래곤':'253450', '콘텐트리중앙':'036420', 'NEW':'160550', '컴투스':'078340', '넥슨게임즈':'225570',
    '위메이드맥스':'101730', '골프존':'215000', '아프리카TV':'067160', '다날':'064260', 'KG이니시스':'035600',
    '한국정보통신':'025770', 'NHN KCP':'060250', '비즈니스온':'138580', '웹케시':'053580', '쿠콘':'292200'
}

tab1, tab2 = st.tabs(["📊 개별 종목 분석", "⚡ 당일 매수 스캐너"])

# ==========================================
# 탭 1: 개별 분석
# ==========================================
with tab1:
    col_l, col_r = st.columns([3, 1])
    with col_l:
        target_name = st.selectbox("분석할 종목 선택", list(STOCK_LIST.keys()), label_visibility="collapsed")
    with col_r:
        analyze_btn = st.button("RUN AI", use_container_width=True)
    
    if analyze_btn:
        code = STOCK_LIST[target_name]
        with st.spinner('시장 데이터를 분석 중입니다...'):
            df = fdr.DataReader(code, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
            if not df.empty and len(df) >= 25:
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df)
                
                # 매매 타이밍 진단
                is_golden = df['MA10'].iloc[-2] <= df['MA20'].iloc[-2] and df['MA10'].iloc[-1] > df['MA20'].iloc[-1]
                rsi_val = df['RSI'].iloc[-1]
                vol_ratio = (df['Volume'].iloc[-1] / df['Volume'].rolling(5).mean().iloc[-2] * 100) if df['Volume'].rolling(5).mean().iloc[-2] > 0 else 0
                
                if is_golden:
                    status_msg = "🚀 [강력 매수] 오늘 막 골든크로스가 발생했습니다! 적극 매수를 고려하세요."
                    status_color = "#f0fdf4"; text_color = "#166534"
                elif rsi_val >= 75:
                    status_msg = "🔥 [분할 매도] RSI가 과열권입니다. 욕심을 버리고 익절을 준비하세요."
                    status_color = "#fef2f2"; text_color = "#991b1b"
                elif rsi_val <= 30:
                    status_msg = "💎 [저점 매수] RSI가 바닥권입니다. 반등 가능성이 높습니다."
                    status_color = "#eff6ff"; text_color = "#1e40af"
                else:
                    status_msg = "✅ [관망] 현재는 특별한 돌파 신호가 없습니다. 추세를 지켜보세요."
                    status_color = "#f9fafb"; text_color = "#374151"

                st.markdown(f'<div class="status-box" style="background:{status_color}; color:{text_color};">{status_msg}</div>', unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                with m1: st.markdown(f'<div class="metric-card"><small>현재가</small><br><b style="font-size:1.5rem;">{df["Close"].iloc[-1]:,.0f}원</b></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="metric-card"><small>RSI (14일)</small><br><b style="font-size:1.5rem;">{rsi_val:.1f}</b></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="metric-card"><small>거래량 (대비)</small><br><b style="font-size:1.5rem;">{vol_ratio:.0f}%</b></div>', unsafe_allow_html=True)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.7, 0.3])
                df_r = df.iloc[-80:]
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['Close'], name='Price', line=dict(color='#111827', width=2.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA10'], name='10MA', line=dict(color='#ef4444', width=1.5, dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_r.index, y=df_r['MA20'], name='20MA', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                fig.add_trace(go.Bar(x=df_r.index, y=df_r['Volume'], name='Vol', marker_color='#e5e7eb'), row=2, col=1)
                fig.update_layout(template="plotly_white", height=500, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 탭 2: 스캐너 (자동 동적 분할 로직)
# ==========================================
with tab2:
    st.markdown("#### ⚡ 당일 돌파(Day-1) 종목 스캐너")
    
    # 🌟 스마트 쪼개기 시스템: 리스트 개수가 몇 개든 알아서 50개씩 잘라줍니다!
    items = list(STOCK_LIST.items())
    total_chunks = (len(items) + 49) // 50
    options = [f"🔍 스캔 구간: {i*50 + 1}위 ~ {min((i+1)*50, len(items))}위" for i in range(total_chunks)]
    
    selected_range = st.selectbox("스캔할 범위를 선택하세요 (50종목 단위 분할 스캔):", options)
    
    if st.button("🚀 매수 신호 스캔 시작", use_container_width=True):
        idx = options.index(selected_range)
        s, e = idx * 50, (idx + 1) * 50
        target_list = items[s:e]
        
        results = []
        bar = st.progress(0)
        
        for i, (name, code) in enumerate(target_list):
            try:
                df_s = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
                if len(df_s) >= 25:
                    df_s['MA10'] = df_s['Close'].rolling(10).mean()
                    df_s['MA20'] = df_s['Close'].rolling(20).mean()
                    
                    # [Day-1 로직]: 오늘 막 뚫고 올라온 종목만!
                    if df_s['MA10'].iloc[-2] <= df_s['MA20'].iloc[-2] and df_s['MA10'].iloc[-1] > df_s['MA20'].iloc[-1]:
                        rsi = calculate_rsi(df_s).iloc[-1]
                        vol = (df_s['Volume'].iloc[-1] / df_s['Volume'].rolling(5).mean().iloc[-2] * 100) if df_s['Volume'].rolling(5).mean().iloc[-2] > 0 else 0
                        inst, frgn = get_investor_data(code)
                        results.append({'name': name, 'code': code, 'price': df_s['Close'].iloc[-1], 'vol': vol, 'rsi': rsi, 'inst': inst, 'frgn': frgn})
            except: pass
            bar.progress((i+1)/len(target_list))
            
        bar.empty()
        
        if results:
            st.markdown(f"#### 🏆 오늘 터진 매수 추천주 ({len(results)}개 발견)")
            for r in sorted(results, key=lambda x: x['vol'], reverse=True):
                st.markdown(f"""
                <div class="buy-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="font-size:1.2rem; color:#111827;">{r['name']}</b>
                        <b style="color:#2563eb; font-size:1.1rem;">{r['price']:,.0f} 원</b>
                    </div>
                    <div class="indicator-container">
                        <div class="badge-premium">오늘 골든크로스 ✅</div>
                        <div class="badge-premium">거래량 {r['vol']:.0f}% 🔥</div>
                        <div class="badge-premium">RSI {r['rsi']:.1f} 🌡️</div>
                    </div>
                    <div class="supply-row">
                        <b>기관 수급:</b> <span style="color:{'#ef4444' if r['inst']>0 else '#3b82f6'}">{r['inst']:,}</span> 주 | 
                        <b>외인 수급:</b> <span style="color:{'#ef4444' if r['frgn']>0 else '#3b82f6'}">{r['frgn']:,}</span> 주
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🧐 선택하신 범위 내에서 '오늘(당일)' 골든크로스가 발생한 종목이 없습니다.")
