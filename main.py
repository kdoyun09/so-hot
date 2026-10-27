import math
import os
import json
import streamlit as st
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="3D 커스텀 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide")

st.title("🥤 3D 커스텀 텀블러 보온·보냉 시뮬레이터")
st.caption("소재별 열전달률을 계산하고 실시간 온도가 떨어지는 과정을 3D로 관찰하세요.")

# 2. 소재 정보
INNER_MATERIALS = {
    "SUS304/316L 위생 스테인리스 (위생성 & 내구성 우수)": {"k_mod": 1.0, "color": "0xc0c8d0", "desc": "부식과 녹에 강한 의료·식품용 위생 소재입니다."},
    "세라믹 코팅 (Ceramic Layer - 착색·냄새 방지)": {"k_mod": 0.85, "color": "0xf0efe9", "desc": "착색 및 냄새 배임을 차단하며 음료 본연의 맛을 유지합니다."},
    "내열 강화 유리 (Borosilicate - 투명성 & 열충격 강함)": {"k_mod": 1.3, "color": "0x88ccee", "desc": "열충격에 강한 붕규산 유리로 투명하게 내부를 봅니다."}
}

INSULATION_MATERIALS = {
    "진공 단열층 (High-Vacuum Layer - 최상급 보온)": {"k_mod": 0.010, "desc": "고진공 상태로 전도·대류 열손실을 극단적으로 차단합니다."},
    "에어로겔 (Aerogel Insulation - 우주공학 신소재)": {"k_mod": 0.008, "desc": "두께 대비 열차단 성능이 우주공학급으로 매우 탁월합니다."},
    "고밀도 우레탄 폼 (Urethane Foam - 실속형 보온)": {"k_mod": 0.035, "desc": "가벼운 실속형 보온 충전재이나 지속 시간은 비교적 짧습니다."}
}

OUTER_MATERIALS = {
    "파우더 코팅 메탈 (Powder Coated Metal - 강한 내구성)": {"k_mod": 1.0, "desc": "분체 도장으로 외부 스크래치와 오염에 매우 강합니다."},
    "친환경 실리콘 커버 (Silicone Grip - 미끄럼 방지)": {"k_mod": 0.9, "desc": "미끄럼을 방지하고 낙하 충격을 완화해 줍니다."},
    "BPA-Free 강화 플라스틱 (PP/Tritan - 가벼움 & 스크래치 강함)": {"k_mod": 1.1, "desc": "가볍고 유해물질이 없는 안전한 친환경 플라스틱입니다."}
}

# 3. 사이드바
st.sidebar.header("🛠️ 텀블러 커스터마이징")
inner_mat_key = st.sidebar.selectbox("1. 내부 재질", list(INNER_MATERIALS.keys()))
inner_desc = INNER_MATERIALS[inner_mat_key]["desc"]
st.sidebar.caption(inner_desc)

insul_mat_key = st.sidebar.selectbox("2. 단열 구조", list(INSULATION_MATERIALS.keys()))
insul_desc = INSULATION_MATERIALS[insul_mat_key]["desc"]
st.sidebar.caption(insul_desc)

outer_mat_key = st.sidebar.selectbox("3. 외부 재질", list(OUTER_MATERIALS.keys()))
outer_desc = OUTER_MATERIALS[outer_mat_key]["desc"]
st.sidebar.caption(outer_desc)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ 환경 & 온도 설정")
t_env = st.sidebar.slider("외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("음료 초기 온도 (°C)", value=90.0, step=1.0)

rec_temp = 58.0 if 5 <= t_env <= 28 else (62.0 if t_env < 5 else 52.0)
st.sidebar.info("💡 외부 온도({}°C) 기준 추천 목표 온도는 **{}°C**입니다.".format(t_env, rec_temp))

t_target = st.sidebar.number_input("목표 섭취 온도 (°C)", value=rec_temp, step=1.0)
start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# 4. 물리 계산
k_total = INSULATION_MATERIALS[insul_mat_key]["k_mod"] * INNER_MATERIALS[inner_mat_key]["k_mod"] * OUTER_MATERIALS[outer_mat_key]["k_mod"]

if t_init > t_env and t_target < t_init and t_target > t_env:
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k_total
    is_valid = True
else:
    time_to_target = 30.0
    is_valid = False
    st.error("❌ 입력 온도를 확인해 주세요. (초기온도 > 목표온도 > 외부온도)")

bg_theme = "summer" if t_env >= 28 else ("winter" if t_env <= 10 else "normal")
config_data = {
    "tInit": float(t_init),
    "tEnv": float(t_env),
    "tTarget": float(t_target),
    "kTotal": float(k_total),
    "timeToTarget": float(time_to_target),
    "bgTheme": bg_theme,
    "innerColorHex": INNER_MATERIALS[inner_mat_key]["color"],
    "shouldStart": True if (start_btn and is_valid) else False
}

# 5. UI 출력
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🎮 3D 커스텀 구조 반단면 텀블러")
    in_name = inner_mat_key.split(' (')[0]
    ins_name = insul_mat_key.split(' (')[0]
    out_name = outer_mat_key.split(' (')[0]
    st.caption("선택 조합: **{}** + **{}** + **{}**".format(in_name, ins_name, out_name))

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        json_str = json.dumps(config_data)
        data_tag = '<div id="sim-data" style="display:none;">{}</div>'.format(json_str)
        components.html(html_content + data_tag, height=490)
    else:
        st.error("❌ index.html 파일이 main.py와 동일한 위치에 생성되어 있는지 확인해 주세요.")

with col2:
    st.subheader("📊 소재 계산 및 보온 대시보드")
    st.markdown("### 🧪 선택한 소재 특성")
    st.markdown("- **내부:** " + inner_desc)
    st.markdown("- **단열:** " + insul_desc)
    st.markdown("- **외부:** " + outer_desc)
    st.markdown("---")
    st.markdown("### 🧪 계산된 총 열전달 계수 (k)")
    st.code("k_total = {:.5f}".format(k_total))
    st.markdown("---")
    st.markdown("### ⏱️ 예상 보온 시간")
    st.success("🎯 **목표 온도 도달 시간:** 약 **{:.1f} 분**".format(time_to_target))
