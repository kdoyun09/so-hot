import math
import os
import json
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="3D 커스텀 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide"
)

st.title("🥤 3D 커스텀 텀블러 보온·보냉 시뮬레이터")
st.caption(
    "내부·단열재·외부 소재를 세세하게 직접 조합하여 열전달률을 계산하고, 실시간 연속 온도가 떨어지는 과정을 3D로 관찰하세요."
)

# ---------------------------------------------------------
# 2. 소재별 열전달 데이터 정의
# ---------------------------------------------------------
INNER_MATERIALS = {
    "SUS304/316L 위생 스테인리스": {"k_mod": 1.0, "color": "0xc0c8d0"},
    "세라믹 코팅 (Ceramic Layer)": {"k_mod": 0.85, "color": "0xf0efe9"},
    "내열 강화 유리 (Borosilicate)": {"k_mod": 1.3, "color": "0x88ccee"},
}

INSULATION_MATERIALS = {
    "진공 단열층 (High-Vacuum Layer)": {"k_mod": 0.010, "desc": "최상급 보온성"},
    "에어로겔 (Aerogel Insulation)": {"k_mod": 0.008, "desc": "우주공학 신소재"},
    "고밀도 우레탄 폼 (Urethane Foam)": {"k_mod": 0.035, "desc": "일반 보온성"},
}

OUTER_MATERIALS = {
    "파우더 코팅 메탈 (Powder Coated Metal)": {"k_mod": 1.0, "rough": 0.3},
    "친환경 실리콘 커버 (Silicone Grip)": {"k_mod": 0.9, "rough": 0.7},
    "BPA-Free 강화 플라스틱 (PP/Tritan)": {"k_mod": 1.1, "rough": 0.5},
}

# ---------------------------------------------------------
# 3. 사이드바 UI 설정
# ---------------------------------------------------------
st.sidebar.header("🛠️ 텀블러 커스터마이징")
inner_mat = st.sidebar.selectbox("1. 내부 재질 (음료 접촉)", list(INNER_MATERIALS.keys()))
insul_mat = st.sidebar.selectbox("2. 단열 구조 (중간 단열재)", list(INSULATION_MATERIALS.keys()))
outer_mat = st.sidebar.selectbox("3. 외부 재질 (손잡이/외벽)", list(OUTER_MATERIALS.keys()))

st.sidebar.markdown("---")
st.sidebar.header("🌡️ 환경 & 온도 설정")
t_env = st.sidebar.slider("현재 텀블러가 있는 곳의 외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("음료 초기 온도 (°C)", value=90.0, step=1.0)

rec_temp = 58.0
if t_env < 5:
    rec_temp = 62.0
elif t_env > 28:
    rec_temp = 52.0

st.sidebar.info(
    f"💡 **목표 온도 추천 가이드:**\n\n현재 외부 온도({t_env}°C) 기준, 화상 없이 맛을 즐기기 가장 좋은 온도는 **{rec_temp}°C 내외**입니다."
)

t_target = st.sidebar.number_input("목표 섭취 온도 (°C)", value=rec_temp, step=1.0)
start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# ---------------------------------------------------------
# 4. 연산 및 JSON 설정 데이터 생성
# ---------------------------------------------------------
k_total = (
    INSULATION_MATERIALS[insul_mat]["k_mod"]
    * INNER_MATERIALS[inner_mat]["k_mod"]
    * OUTER_MATERIALS[outer_mat]["k_mod"]
)

if t_init > t_env and t_target < t_init and t_target > t_env:
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k_total
    is_valid = True
else:
    time_to_target = 30.0
    is_valid = False
    st.error("❌ 입력한 온도가 올바르지 않습니다. (초기온도 > 목표온도 > 외부온도 규칙 필요)")

bg_theme = "summer" if t_env >= 28 else ("winter" if t_env <= 10 else "normal")
inner_color_hex = INNER_MATERIALS[inner_mat]["color"]
should_start = True if (start_btn and is_valid) else False

config_data = {
    "tInit": float(t_init),
    "tEnv": float(t_env),
    "tTarget": float(t_target),
    "kTotal": float(k_total),
    "timeToTarget": float(time_to_target),
    "bgTheme": bg_theme,
    "innerColorHex": inner_color_hex,
    "shouldStart": should_start,
}

# ---------------------------------------------------------
# 5. 메인 UI 및 index.html 연동
# ---------------------------------------------------------
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🎮 3D 커스텀 구조 반단면 텀블러")
    st.caption(f"선택한 조합: **{inner_mat}** + **{insul_mat}** + **{outer_mat}**")

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        script_call = f"<script>initSimulator({json.dumps(config_data)});</script>"
        full_html = html_content + script_call
        components.html(full_html, height=490)
    else:
        st.error("❌ index.html 파일을 찾을 수 없습니다. main.py와 동일한 위치에 생성해 주세요.")

with col2:
    st.subheader("📊 소재 계산 및 보온 대시보드")

    st.markdown("### 🧪 계산된 총 열전달 계수 ($k$)")
    st.code(f"k_total = {k_total:.5f}")

    st.markdown("---")
    st.markdown("### ⏱️ 예상 보온 시간")
    st.success(f"🎯 **목표 온도({t_target}°C) 도달 시간:** 약 **{time_to_target:.1f} 분**")

    st.markdown("---")
    st.info(
        "💡 **시뮬레이션 안내:**\n\n"
        "좌측 사이드바에서 소재를 선택하고 **[🚀 시뮬레이션 시작]**을 누르면, "
        "3D 텀블러 좌측 상단의 실시간 온도와 아우라 색상이 **100°C → 50°C**로 연속적으로 떨어집니다."
    )
