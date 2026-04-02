import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 예고 모니터링", layout="wide")
st.title("🛡️ 안전관리자 입법/행정예고 모니터링 보드")
st.markdown("정부가 향후 변경할 예정으로 미리 공지하는 **[입법예고]** 법안들을 집중 모니터링하여 사전 대응을 준비하세요.")

my_oc = "soosafety2026"

# --- 🔍 어떤 이름의 태그든 찾아내는 안전한 함수 ---
def get_txt(node, tags):
    for tag in tags:
        target = node.find(tag)
        if target is not None and target.text:
            return target.text.strip()
    return "정보없음"

# --- 사이드바 설정 ---
st.sidebar.header("🔍 모니터링 설정")
# 여기서 모니터링 타겟을 선택할 수 있습니다!
search_type = st.sidebar.radio(
    "어떤 데이터를 조회할까요?",
    ["🚧 입법·행정예고 (향후 개정될 예정안)", "✅ 현행·시행 법령 (이미 확정된 법)"]
)

keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설")
search_btn = st.sidebar.button("모니터링 데이터 조회")

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_data = []

    with st.spinner('법제처의 예고 데이터를 뒤지는 중입니다...'):
        for query in keyword_list:
            # 선택한 라디오 버튼에 따라 타겟을 바꿉니다 (예고 = lmpp, 현행 = law)
            target_code = "lmpp" if "예고" in search_type else "law"
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target={target_code}&type=XML&query={query}"
            
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                
                # 타겟에 따라 가져올 노드 이름이 다름
                node_name = 'lmpp' if target_code == 'lmpp' else 'law'
                
                for item in root.findall(node_name):
                    if target_code == "lmpp":
                        # 1. 입법/행정예고 데이터 수집
                        title = get_txt(item, ['법령명한글', '예고명', '입법예고명'])
                        notice_date = get_txt(item, ['공고일자', '예고일자'])
                        period = get_txt(item, ['예고기간'])
                        link = get_txt(item, ['법
