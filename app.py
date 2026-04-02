import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 대시보드", layout="wide")
st.title("🛡️ 안전관계 법령 모니터링 & 상세 분석")

my_oc = "soosafety2026"

# --- 🔍 [수정] 상자 안의 상자까지 찾는 똑똑한 검색 함수 ---
def get_txt_deep(node, tag):
    # .// 는 "이 노드 아래 어디든 그 태그가 있으면 찾아라"는 뜻입니다.
    target = node.find('.//' + tag)
    if target is not None and target.text:
        return target.text.strip()
    return "법제처 API에서 상세 내용을 제공하지 않는 법령입니다."

# --- 사이드바 및 검색 기능 ---
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설")
search_btn = st.sidebar.button("최신 개정사항 조회")

if search_btn or 'law_df' in st.session_state:
    if search_btn:
        keyword_list = [k.strip() for k in keywords.split(",")]
        all_laws = []
        for query in keyword_list:
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            res = requests.get(url)
            root = ET.fromstring(res.content)
            for law in root.findall('law'):
                all_laws.append({
                    "시행일자": law.find('시행일자').text if law.find('시행일자') is not None else "정보없음",
                    "법령명": law.find('법령명한글').text if law.find('법령명한글') is not None else "정보없음",
                    "구분": law.find('제개정구분').text if law.find('제개정구분') is not None else "정보없음",
                    "ID": law.find('법령ID').text if law.find('법령ID') is not None else ""
                })
        st.session_state['law_df'] = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명'])

    df = st.session_state['law_df']
    st.subheader("📋 검색된 법령 목록")
    st.dataframe(df[["시행일자", "법령명", "구분"]], width="stretch", hide_index=True)

    st.divider()
    
    # --- 🔍 내 사이트에서 상세 정보 바로 보기 ---
    st.subheader("🧐 선택한 법령의 개정 이유 상세 분석")
    selected_law = st.selectbox("내용을 확인할 법령을 선택하세요", df['법령명'].tolist())
    
    if selected_law:
        law_id = df[df['법령명'] == selected_law]['ID'].values[0]
        
        with st.spinner('상세 정보를 불러오는 중...'):
            # 법제처 상세보기 API 호출
            detail_url = f"http://www.law.go.kr/DRF/lawService.do?OC={my_oc}&target=law&type=XML&MST={law_id}"
            detail_res = requests.get(detail_url)
            detail_root = ET.fromstring(detail_res.content)
            
            # 깊숙한 곳(기본정보 등)까지 뒤져서 데이터를 가져옵니다.
            reason = get_txt_deep(detail_root, '제개정이유')
            content = get_txt_deep(detail_root, '주요내용')

            col1, col2 = st.columns(2)
            with col1:
                st.info("📝 **제/개정 이유**")
                # 글자가 너무 길면 보기 좋게 박스에 담아줍니다.
                st.write(reason)
            with col2:
                st.success("📌 **주요 내용 (변경된 핵심)**")
                st.write(content)
else:
    st.info("왼쪽에서 키워드를 입력하고 버튼을 눌러주세요.")
