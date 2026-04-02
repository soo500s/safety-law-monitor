import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 모니터링 PRO", layout="wide")
st.title("🛡️ 안전관리자 법령 모니터링 & 신구비교")

# --- 현재 접속 IP 확인 ---
try:
    current_ip = requests.get('https://api.ipify.org').text
except:
    current_ip = "확인 불가"

st.sidebar.info(f"📍 현재 서버 IP: {current_ip}")

my_oc = "soosafety2026" 
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설, 건설기술")
search_btn = st.sidebar.button("최신 개정사항 확인")

# 안전하게 텍스트를 가져오는 도우미 함수
def get_text(element, tag):
    node = element.find(tag)
    return node.text if node is not None else "정보없음"

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_laws = []
    
    with st.spinner('법제처에서 데이터를 가져오는 중...'):
        for query in keyword_list:
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                
                # 결과가 있는지 확인
                laws = root.findall('law')
                if not laws:
                    continue
                    
                for law in laws:
                    law_name = get_text(law, '법령명한글')
                    law_id = get_text(law, '법령ID')
                    enforce_date = get_text(law, '시행일자')
                    change_type = get_text(law, '제개정구분')
                    
                    all_laws.append({
                        "시행일자": enforce_date,
                        "법령명": law_name,
                        "구분": change_type,
                        "키워드": query,
                        "신구조문대비표": f"https://www.law.go.kr/LSW/nwStmInfoP.do?lsiSeq={law_id}",
                        "상세보기": f"https://www.law.go.kr/법령/{law_name}"
                    })
            except Exception as e:
                st.error(f"'{query}' 검색 중 오류: {e}")

    if all_laws:
        df = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명']).sort_values("시행일자", ascending=False)
        st.success(f"✅ 총 {len(df)}건의 법령 정보를 찾았습니다.")
        
        st.dataframe(
            df, 
            column_config={
                "신구조문대비표": st.column_config.LinkColumn("신구조문대비표"),
                "상세보기": st.column_config.LinkColumn("상세보기")
            },
            width='stretch',
            hide_index=True
        )
        st.download_button("📥 엑셀 저장", df.to_csv(index=False).encode('utf-8-sig'), "safety_law_report.csv", "text/csv")
    else:
        st.warning("데이터가 없습니다. 법제처 사이트에 IP(34.83.176.217)가 잘 등록되었는지 확인해주세요.")
