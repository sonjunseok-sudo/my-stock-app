import streamlit as st
import FinanceDataReader as fdr
from datetime import datetime, timedelta

# 앱의 제목과 설명
st.title("📈 나만의 주식 AI 대시보드")
st.write("텔레그램 알림 봇을 넘어, 직접 화면에서 차트를 봅니다!")

# 종목 리스트 
TARGET_STOCKS = {
    '005930': '삼성전자', 
    '000660': 'SK하이닉스', 
    '035420': 'NAVER'
}

# 콤보박스(선택창) 만들기
selected_name = st.selectbox("분석할 종목을 선택하세요:", list(TARGET_STOCKS.values()))

# 선택한 종목의 코드 찾기
selected_code = [code for code, name in TARGET_STOCKS.items() if name == selected_name][0]

# 버튼 만들기
if st.button("📊 차트 불러오기"):
    st.info(f"{selected_name} 데이터를 가져오는 중입니다...")
    
    # 데이터 가져오기 (최근 6개월)
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    df = fdr.DataReader(selected_code, start_date)
    
    # 🌟 놀라운 점: 파이썬 코드 한 줄이면 인터랙티브 차트가 예쁘게 그려집니다!
    st.line_chart(df['Close'])
    
    st.success("분석 완료! 화면을 터치해서 가격을 확인해 보세요.")