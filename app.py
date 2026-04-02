import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="안전 법령 시행 모니터링", layout="wide")
st.title("🛡️ 안전 법령 시행일정 모니터링 보드")
st.markdown("현재 시행 중인 법령과 **앞으로 시행될 예정인 법령**의 일정을 한눈에 확인하세요.")

my_oc = "soosafety2026"

# 오늘 날짜를 '20260402' 형식으로 가져옵니다 (시행예정 판별용)
today_str = datetime.today().strftime('%Y%m%d')

# --- 사이드바 ---
keywords = st.sidebar.text_area("모니터링 키워드", value="산업안전보건법, 중대재해, 소방시설, 건설기술")
search_btn = st.sidebar.button("시행 일정 및 변경사항 조회")

if search_btn:
    keyword_list = [k.strip() for k in keywords.split(",")]
    all_laws = []
    
    with st.spinner('법령 일정을 분석하는 중...'):
        for query in keyword_list:
            url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={my_oc}&target=law&type=XML&query={query}"
            try:
                res = requests.get(url)
                root = ET.fromstring(res.content)
                
                for law in root.findall('law'):
                    law_name = law.findtext('법령명한글')
                    law_id = law.findtext('법령ID')
                    enforce_date = law.findtext('시행일자')
                    change_type = law.findtext('제개정구분')
                    
                    if not enforce_date or not law_name:
                        continue
                        
                    # 💡 오늘 날짜와 비교하여 '시행예정'인지 판별합니다.
                    if enforce_date > today_str:
                        status = "🔴 시행예정"
                    else:
                        status = "🟢 시행중"
                        
                    # 시행 연도만 따로 뽑아냅니다.
                    enforce_year = enforce_date[:4] + "년" if len(enforce_date) == 8 else "미정"
                    
                    all_laws.append({
                        "상태": status,
                        "시행연도": enforce_year,
                        "시행일자": enforce_date,
                        "법령명": law_name,
                        "구분": change_type,
                        "키워드": query,
                        "신구조문/개정이유": f"https://www.law.go.kr/LSW/lawLsByLsStm.do?lsiSeq={law_id}",
                        "법령본문": f"https://www.law.go.kr/법령/{law_name}"
                    })
            except Exception as e:
                continue

    if all_laws:
        # 중복 제거 후 '상태(시행예정이 위로)' -> '시행일자(최신이 위로)' 순으로 정렬합니다.
        df = pd.DataFrame(all_laws).drop_duplicates(subset=['법령명', '시행일자']).sort_values(["상태", "시행일자"], ascending=[False, False])
        
        # 상단 요약 알림
        upcoming_count = len(df[df['상태'] == "🔴 시행예정"])
        st.success(f"✅ 총 {len(df)}건의 법령이 검색되었습니다. 그중 **앞으로 시행될 예정(예고)인 법령은 {upcoming_count}건** 입니다.")
        
        # 예쁜 표로 출력
        st.dataframe(
            df, 
            column_config={
                "상태": st.column_config.TextColumn("진행 상태"),
                "신구조문/개정이유": st.column_config.LinkColumn("🔍 변경내용(신구법) 확인", help="클릭하여 법제처에서 개정이유와 대비표를 확인하세요"),
                "법령본문": st.column_config.LinkColumn("📖 법령 본문보기")
            },
            width="stretch",
            hide_index=True
        )
        
        st.download_button("📥 모니터링 일정 엑셀 다운로드", df.to_csv(index=False).encode('utf-8-sig'), "upcoming_safety_laws.csv", "text/csv")
    else:
        st.warning("데이터를 불러오지 못했습니다. 법제처 서버에 접속할 수 없거나 검색 결과가 없습니다.")
else:
    st.info("왼쪽의 [시행 일정 및 변경사항 조회] 버튼을 눌러 모니터링을 시작하세요.")
