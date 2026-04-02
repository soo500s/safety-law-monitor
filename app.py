import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 대시보드", layout="wide")
st.title("🛡️ 안전관계 법령 모니터링 & 상세 분석")

# 1. 법제처 API 설정
my_oc = "soosafety2026"

# 2. 데이터 수집 함수 (기존과 동일하지만 상세 정보를 위해 ID를 챙깁니다)
def get_txt(node, tag):
    target = node.find(tag)
    return target.text if target is not None else "정보없음"

# --- 사이드바 설정 ---
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
                    "시행일자": get_txt(law, '시행일자'),
                    "법령명": get_txt(law, '법령명한글'),
                    "구분": get_txt(law, '제개정구분'),
                    "ID": get_txt(law, '법령ID') # 상세 조회를 위한 열쇠
                })
        st.session_state['law_df'] = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명'])

    df = st.session_state['law_df']
    st.subheader("📋 검색된 법령 목록")
    st.dataframe(df[["시행일자", "법령명", "구분"]], width="stretch", hide_index=True)

    # --- 🔍 [핵심] 내 사이트에서 바로 보는 상세 정보 ---
    st.divider()
    st.subheader("🧐 선택한 법령의 개정 내용 상세 분석")
    
    selected_law = st.selectbox("상세 내용을 볼 법령을 선택하세요", df['법령명'].tolist())
    
    if selected_law:
        # 선택된 법령의 ID 찾기
        law_id = df[df['법령명'] == selected_law]['ID'].values[0]
        
        with st.spinner('상세 개정 이유를 가져오는 중...'):
            # 법제처 법령 상세정보 API 호출
            detail_url = f"http://www.law.go.kr/DRF/lawService.do?OC={my_oc}&target=law&type=XML&MST={law_id}"
            detail_res = requests.get(detail_url)
            detail_root = ET.fromstring(detail_res.content)
            
            # 개정이유(또는 제정이유) 가져오기
            reason = get_txt(detail_root, '제개정이유')
            content = get_txt(detail_root, '주요내용')

            # 화면에 예쁘게 뿌려주기
            col1, col2 = st.columns(2)
            with col1:
                st.info("📝 **제/개정 이유**")
                st.write(reason)
            with col2:
                st.success("📌 **주요 내용 (변경된 핵심)**")
                st.write(content)

            st.caption("※ 더 자세한 신구조문 대조표는 법제처 사이트에서 확인하시는 것이 가장 정확합니다.")

else:
    st.info("왼쪽에서 키워드를 입력하고 버튼을 눌러주세요.")
