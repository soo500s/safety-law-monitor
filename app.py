import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 진단 모드", layout="wide")
st.title("🛡️ 안전 법령 상세분석 (진단 모드)")

my_oc = "soosafety2026"

# --- 🔍 데이터를 샅샅이 뒤지는 함수 ---
def find_any_text(node, tag_list):
    for tag in tag_list:
        target = node.find('.//' + tag)
        if target is not None and target.text:
            return target.text.strip()
    return None

# --- 사이드바 ---
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해")
search_btn = st.sidebar.button("데이터 조회")

if search_btn or 'law_df' in st.session_state:
    if search_btn:
        all_laws = []
        url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={keywords.split(',')[0]}"
        res = requests.get(url)
        root = ET.fromstring(res.content)
        for law in root.findall('law'):
            all_laws.append({
                "시행일자": law.find('시행일자').text if law.find('시행일자') is not None else "정보없음",
                "법령명": law.find('법령명한글').text if law.find('법령명한글') is not None else "정보없음",
                "ID": law.find('법령ID').text if law.find('법령ID') is not None else ""
            })
        st.session_state['law_df'] = pd.DataFrame(all_laws)

    df = st.session_state['law_df']
    selected_law = st.selectbox("내용을 확인할 법령을 선택하세요", df['법령명'].tolist())
    
    if selected_law:
        law_id = df[df['법령명'] == selected_law]['ID'].values[0]
        
        # 상세정보 호출
        detail_url = f"http://www.law.go.kr/DRF/lawService.do?OC={my_oc}&target=law&type=XML&MST={law_id}"
        detail_res = requests.get(detail_url)
        
        # 🚨 [진단] 법제처가 실제로 보내준 데이터를 화면에 출력해봅니다.
        with st.expander("🛠️ 법제처에서 보내준 실제 데이터 확인 (개발자용)"):
            st.code(detail_res.text[:1000] + "...") # 앞부분 1000자만 출력

        detail_root = ET.fromstring(detail_res.content)
        
        # 여러가지 이름으로 시도해봅니다.
        reason = find_any_text(detail_root, ['제개정이유', '개정이유', '제정이유'])
        content = find_any_text(detail_root, ['주요내용', '내용'])

        if reason or content:
            col1, col2 = st.columns(2)
            with col1:
                st.info("📝 **제/개정 이유**")
                st.write(reason if reason else "상세 이유 없음")
            with col2:
                st.success("📌 **주요 내용**")
                st.write(content if content else "상세 내용 없음")
        else:
            # ❌ 데이터가 아예 안 나올 때의 안내
            st.error("❗ 상세 내용을 가져오지 못했습니다.")
            st.warning("1. 법제처 OpenAPI 사이트 [마이페이지]에서 '법령상세조회' 서비스가 승인되었는지 확인해주세요.")
            st.warning("2. 만약 '사용자 정보 검증에 실패'라고 뜬다면 IP 등록(34.83.176.217)을 다시 확인해야 합니다.")
