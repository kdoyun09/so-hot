import math
import time
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 세션 초기화
# ---------------------------------------------------------
st.set_page_config(
    page_title="3D 커스텀 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide"
)

st.title("🥤 3D 커스텀 텀블러 보온·보냉 시뮬레이터")
st.caption(
    "내부·단열재·외부 소재를 세세하게 직접 조합하여 열전달률을 계산하고, 실시간 연속 온도가 떨어지는 과정을 3D로 관찰하세요."
)

if "simulating" not in st.session_state:
    st.session_state.simulating = False
if "current_time" not in st.session_state:
    st.session_state.current_time = 0.0

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
    f"💡 **목표 온도 추천 가이드:**\n\n"
    f"현재 외부 온도({t_env}°C) 기준, 화상 없이 맛을 즐기기 가장 좋은 온도는 **{rec_temp}°C 내외**입니다."
)

t_target = st.sidebar.number_input("목표 섭취 온도 (°C)", value=rec_temp, step=1.0)
start_btn = st.sidebar
