import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="안전 법령 모니터링 PRO", layout="wide")
st.title("🛡️ 안전관리자 법령 모니터링 & 개정확인")

# --- 현재 접속 IP 확인 ---
try:
    current_ip = requests.get('https://api.ipify.org').text
except:
    current_ip = "확인 불가"

st.sidebar.info(f"📍 현재 서버 IP: {current_ip}")

my_oc = "soosafety2026" 
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설, 건설기술")
search_btn = st.sidebar.button("최신 개정사항 확인")

# 안전하게 데이터를 가져오는 함수
def get_txt(node, tag):
    target = node.find(tag)
    return target.text if target is not None else "정보없음"

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_laws = []
    
    with st.spinner('법제처 최신 데이터를 동기화 중...'):
        for query in keyword_list:
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                
                for law in root.findall('law'):
                    law_name = get_txt(law, '법령명한글')
                    law_id = get_txt(law, '법령ID') # 실제 법령 일련번호(LSI SEQ)와 유사하게 작동
                    enforce_date = get_txt(law, '시행일자')
                    change_type = get_txt(law, '제개정구분')
                    
                    all_laws.append({
                        "시행일자": enforce_date,
                        "법령명": law_name,
                        "구분": change_type,
                        "키워드": query,
                        "신구대비/개정이유": f"https://www.law.go.kr/LSW/lawLsByLsStm.do?lsiSeq={law_id}",
                        "법령본문": f"https://www.law.go.kr/법령/{law_name}"
                    })
            except:
                continue

    if all_laws:
        df = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명']).sort_values("시행일자", ascending=False)
        st.success(f"✅ 총 {len(df)}건의 법령 정보를 불러왔습니다.")
        
        # 2026년 최신 문법 및 링크 설정
        st.dataframe(
            df, 
            column_config={
                "신구대비/개정이유": st.column_config.LinkColumn("🔍 신구대비 확인",
