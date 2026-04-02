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

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_laws = []
    
    with st.spinner('법제처에서 상세 데이터를 가져오는 중...'):
        for query in keyword_list:
            # 법령 검색 API 호출
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                for law in root.findall('law'):
                    law_name = law.find('법령명한글').text
                    law_id = law.find('법령ID').text # 이게 LSI Seq 역할
                    enforce_date = law.find('시행일자').text
                    change_type = law.find('제개정구분').text # 일부개정, 제정 등
                    
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
        st.success(f"✅ 총 {len(df)}건의 법령 및 개정 정보를 찾았습니다.")
        
        # 표를 더 예쁘게 보여주기 (링크 버튼 활성화)
        st.dataframe(
            df, 
            column_config={
                "신구조문대비표": st.column_config.LinkColumn("신구조문대비표", help="클릭하면 변경된 조항 비교표가 열립니다"),
                "상세보기": st.column_config.LinkColumn("상세보기")
            },
            width='stretch',
            hide_index=True
        )
        
        st.download_button("📥 결과 엑셀 저장", df.to_csv(index=False).encode('utf-8-sig'), "safety_law_report.csv", "text/csv")
    else:
        st.warning("데이터가 없습니다. IP 등록(34.83.176.217)을 다시 확인해주세요.")
