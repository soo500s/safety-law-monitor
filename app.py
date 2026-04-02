import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 대시보드 PRO", layout="wide")
st.title("🛡️ 안전관리자 법령 모니터링 & 상세 분석")

my_oc = "soosafety2026"

# --- 🔍 [핵심] 어떤 깊이에 있든 태그를 찾아내는 함수 ---
def find_text_anywhere(node, tag_names):
    # 입력된 태그 이름들을 하나씩 대조하며 가장 먼저 찾아지는 내용을 반환합니다.
    for tag in tag_names:
        # .// 는 모든 하위 자식들을 다 뒤지라는 뜻입니다.
        target = node.find(f".//{tag}")
        if target is not None and target.text:
            content = target.text.strip()
            if len(content) > 5: # 내용이 너무 짧은 건 제외
                return content
    return None

# --- 사이드바 및 검색 기능 ---
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설")
search_btn = st.sidebar.button("최신 데이터 동기화")

if search_btn or 'law_df' in st.session_state:
    if search_btn:
        all_laws = []
        # 첫 번째 키워드로 검색 (나머지는 목록에서 필터링 가능)
        url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={keywords.split(',')[0]}"
        res = requests.get(url)
        root = ET.fromstring(res.content)
        for law in root.findall('law'):
            all_laws.append({
                "시행일자": law.findtext('시행일자'),
                "법령명": law.findtext('법령명한글'),
                "구분": law.findtext('제개정구분'),
                "ID": law.findtext('법령ID')
            })
        st.session_state['law_df'] = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명'])

    df = st.session_state['law_df']
    st.subheader("📋 최신 법령 목록")
    st.dataframe(df[["시행일자", "법령명", "구분"]], width="stretch", hide_index=True)

    st.divider()
    
    # --- 🧐 상세 분석 섹션 ---
    st.subheader("🔎 선택한 법령의 개정 상세 정보")
    selected_law = st.selectbox("상세 내용을 확인하고 싶은 법령을 선택하세요", df['법령명'].tolist())
    
    if selected_law:
        law_id = df[df['법령명'] == selected_law]['ID'].values[0]
        
        with st.spinner('상세 개정 이유를 분석 중...'):
            # 법제처 상세정보 API 호출
            detail_url = f"http://www.law.go.kr/DRF/lawService.do?OC={my_oc}&target=law&type=XML&MST={law_id}"
            detail_res = requests.get(detail_url)
            detail_root = ET.fromstring(detail_res.content)
            
            # 법제처가 사용하는 다양한 태그 이름들을 모두 뒤집니다.
            reason = find_text_anywhere(detail_root, ['제개정이유', '개정이유', '제정이유', '개정내용'])
            content = find_text_anywhere(detail_root, ['주요내용', '주요개정내용', '개정문내용'])

            if reason or content:
                col1, col2 = st.columns(2)
                with col1:
                    st.info("📝 **제/개정 이유**")
                    st.markdown(reason if reason else "_상세 이유 정보가 없습니다._")
                with col2:
                    st.success("📌 **주요 내용 (변경 포인트)**")
                    st.markdown(content if content else "_상세 내용 정보가 없습니다._")
            else:
                st.warning("⚠️ 해당 법령의 상세 텍스트가 API로 제공되지 않습니다.")
                st.write("대신 아래 [신구조문대비표] 링크를 클릭하시면 법제처 웹사이트에서 즉시 확인 가능합니다.")
                st.link_button("🔍 신구조문대비표 바로가기", f"https://www.law.go.kr/LSW/lawLsByLsStm.do?lsiSeq={law_id}")

            # [개발자용] 진짜 데이터가 어떻게 오는지 궁금할 때 열어보는 창
            with st.expander("🛠️ 법제처 데이터 원본 분석 (문제가 계속될 때 확인)"):
                st.code(detail_res.text[:2000]) # 처음 2000자만 보여줌
