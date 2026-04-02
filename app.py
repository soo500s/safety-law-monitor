import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 최종 진단", layout="wide")
st.title("🛡️ 법령 상세 분석 (최종 에러 추적)")

my_oc = "soosafety2026"

# --- 사이드바 ---
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해")
search_btn = st.sidebar.button("데이터 조회")

if search_btn or 'law_df' in st.session_state:
    if search_btn:
        # 1. 목록 검색
        url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={keywords.split(',')[0]}"
        res = requests.get(url)
        root = ET.fromstring(res.content)
        all_laws = []
        for law in root.findall('law'):
            all_laws.append({
                "시행일자": law.findtext('시행일자'),
                "법령명": law.findtext('법령명한글'),
                "ID": law.findtext('법령ID')
            })
        st.session_state['law_df'] = pd.DataFrame(all_laws)

    df = st.session_state['law_df']
    selected_law = st.selectbox("내용을 확인할 법령을 선택하세요", df['법령명'].tolist())
    
    if selected_law:
        law_id = df[df['법령명'] == selected_law]['ID'].values[0]
        
        # 🚨 [수정] 상세보기 API 주소를 더 정석적으로 호출합니다.
        detail_url = f"http://www.law.go.kr/DRF/lawService.do?OC={my_oc}&target=law&type=XML&MST={law_id}"
        detail_res = requests.get(detail_url)
        
        # 🔍 법제처가 보낸 메시지 직접 확인 (이게 핵심입니다!)
        if "사용자 정보 검증에 실패" in detail_res.text:
            st.error("❌ [IP 등록 오류] 법제처에 34.83.176.217 주소가 정확히 등록되지 않았습니다.")
        elif "인증키를 확인" in detail_res.text:
            st.error("❌ [인증키 오류] OC 코드가 틀렸거나 만료되었습니다.")
        elif "서비스를 사용할 수 없습니다" in detail_res.text:
            st.error("❌ [권한 오류] 법제처 사이트에서 '법령상세정보' 서비스를 추가로 신청하셔야 합니다.")
        else:
            # 정상인 경우 데이터 표시
            detail_root = ET.fromstring(detail_res.content)
            reason = detail_root.findtext('.//제개정이유') or detail_root.findtext('.//개정이유')
            content = detail_root.findtext('.//주요내용')
            
            if reason:
                st.info(f"📝 **{selected_law} - 개정이유**")
                st.write(reason)
                st.success("📌 **주요내용**")
                st.write(content if content else "상세 내용 없음")
            else:
                st.warning("❗ 법령 목록은 가져왔으나, 해당 법령의 상세 '개정이유' 데이터가 비어있습니다.")
                with st.expander("법제처 응답 원본 보기"):
                    st.code(detail_res.text)
