import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 모니터링", layout="wide")
st.title("🛡️ 안전관리자 전용 법령 모니터링")

# --- 현재 접속 IP 확인용 (법제처 등록용) ---
try:
    current_ip = requests.get('https://api.ipify.org').text
except:
    current_ip = "확인 불가"

st.sidebar.info(f"📍 현재 서버 IP: {current_ip}")
st.sidebar.caption("이 IP를 법제처 OpenAPI 사이트에 등록해야 데이터가 나옵니다.")

my_oc = "soosafety2026" 
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설, 건설기술")
search_btn = st.sidebar.button("법령 업데이트 확인")

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_laws = []
    
    with st.spinner('법제처 데이터를 가져오는 중...'):
        for query in keyword_list:
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            try:
                res = requests.get(url)
                if "사용자 정보 검증에 실패하였습니다" in res.text:
                    st.error(f"❌ 법제처 IP 인증 에러! 아래 IP를 등록하세요.")
                    st.code(current_ip)
                    break
                
                root = ET.fromstring(res.content)
                for law in root.findall('law'):
                    all_laws.append({
                        "시행일자": law.find('시행일자').text,
                        "법령명": law.find('법령명한글').text,
                        "키워드": query,
                        "링크": f"https://www.law.go.kr/법령/{law.find('법령명한글').text}"
                    })
            except Exception as e:
                st.error(f"데이터 해석 중 오류 발생: {e}")

    if all_laws:
        df = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명']).sort_values("시행일자", ascending=False)
        st.success(f"총 {len(df)}건의 법령을 찾았습니다.")
        st.dataframe(df, width='stretch')
        st.download_button("📥 엑셀 저장", df.to_csv(index=False).encode('utf-8-sig'), "safety_laws.csv", "text/csv")
    else:
        st.warning("데이터가 없습니다. IP 등록 여부를 확인해주세요.")
else:
    st.info("왼쪽 버튼을 눌러 모니터링을 시작하세요.")
