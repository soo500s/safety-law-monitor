import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전 법령 예고 모니터링", layout="wide")
st.title("🛡️ 안전관리자 입법/행정예고 모니터링 보드")
st.markdown("정부가 향후 변경할 예정인 **[입법예고]** 법안들을 집중 모니터링하세요.")

my_oc = "soosafety2026"

# 2. 어떤 이름의 태그든 찾아내는 안전한 함수
def get_txt(node, tags):
    for tag in tags:
        target = node.find(tag)
        if target is not None and target.text:
            return target.text.strip()
    return "정보없음"

# 3. 사이드바 설정
st.sidebar.header("🔍 모니터링 설정")
search_type = st.sidebar.radio(
    "어떤 데이터를 조회할까요?",
    ["🚧 입법·행정예고 (향후 개정될 예정안)", "✅ 현행·시행 법령 (이미 확정된 법)"]
)

keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설")
search_btn = st.sidebar.button("모니터링 데이터 조회")

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_data = []

    with st.spinner('법제처 데이터를 분석하는 중입니다...'):
        for query in keyword_list:
            # 예고(lmpp) 또는 현행(law) 선택
            target_code = "lmpp" if "예고" in search_type else "law"
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target={target_code}&type=XML&query={query}"
            
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                
                # 노드 이름 결정 (lmpp 또는 law)
                node_name = 'lmpp' if target_code == 'lmpp' else 'law'
                
                for item in root.findall(node_name):
                    if target_code == "lmpp":
                        # --- 입법/행정예고 데이터 수집 ---
                        v_title = get_txt(item, ['법령명한글', '예고명', '입법예고명'])
                        v_date = get_txt(item, ['공고일자', '예고일자'])
                        v_period = get_txt(item, ['예고기간'])
                        # 잘림 방지를 위해 리스트를 변수로 분리
                        tag_list = ['법령상세링크', '상세링크', '링크']
                        v_link = get_txt(item, tag_list)
                        
                        if v_title != "정보없음":
                            all_data.append({
                                "공고일자": v_date,
                                "예고기간": v_period,
                                "입법/행정예고명 (개정 예정안)": v_title,
                                "키워드": query,
                                "예고문 확인": v_link if v_link.startswith('http') else "https://www.law.go.kr/LSW/lmppInfoP.do"
                            })
                    else:
                        # --- 일반 현행법령 데이터 수집 ---
                        v_title = get_txt(item, ['법령명한글'])
                        v_date = get_txt(item, ['시행일자'])
                        v_type = get_txt(item, ['제개정구분'])
                        v_id = get_txt(item, ['법령ID'])
                        
                        if v_title != "정보없음":
                            all_data.append({
                                "시행일자": v_date,
                                "법령명": v_title,
                                "구분": v_type,
                                "키워드": query,
                                "상세확인":
