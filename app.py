import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전 법령 모니터링 PRO", layout="wide")
st.title("🛡️ 안전관계 법령 모니터링 & 개정확인")

# 2. 현재 접속 IP 확인 (법제처 등록 확인용)
try:
    current_ip = requests.get('https://api.ipify.org').text
except:
    current_ip = "확인 불가"

st.sidebar.info(f"📍 현재 서버 IP: {current_ip}")

# 3. 설정 및 키워드 입력
my_oc = "soosafety2026" 
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설, 건설기술, 위험물, 화학물질")
search_btn = st.sidebar.button("최신 개정사항 확인")

# 4. 데이터 추출 도우미 함수
def get_txt(node, tag):
    target = node.find(tag)
    return target.text if target is not None else "정보없음"

# 5. 실행 로직
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
                    law_id = get_txt(law, '법령ID')
                    enforce_date = get_txt(law, '시행일자')
                    change_type = get_txt(law, '제개정구분')
                    
                    all_laws.append({
                        "시행일자": enforce_date,
                        "법령명": law_name,
                        "구분": change_type,
                        "키워드": query,
                        "개정연혁": f"https://www.law.go.kr/LSW/lawLsByLsStm.do?lsiSeq={law_id}",
                        "법령본문": f"https://www.law.go.kr/법령/{law_name}"
                    })
            except:
                continue

    if all_laws:
        df = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명']).sort_values("시행일자", ascending=False)
        st.success(f"✅ 총 {len(df)}건의 법령 정보를 불러왔습니다.")
        
        # 표 출력 (괄호 하나하나 꼼꼼하게 닫았습니다!)
        st.dataframe(
            df, 
            column_config={
                "개정연혁": st.column_config.LinkColumn("🔍 신구대비 확인"),
                "법령본문": st.column_config.LinkColumn("📖 본문보기")
            },
            width="stretch",
            hide_index=True
        )
        
        st.download_button("📥 보고용 엑셀 다운로드", df.to_csv(index=False).encode('utf-8-sig'), "safety_report.csv", "text/csv")
    else:
        st.warning("데이터를 불러오지 못했습니다. 법제처 사이트에 IP가 등록되어 있는지 확인해주세요.")
else:
    st.info("왼쪽 버튼을 눌러 모니터링을 시작하세요.")
