import math
import os
import json
import streamlit as st
import streamlit.components.v1 as components

# 1. 페이지 기본 설정
st.set_page_config(page_title="3D 커스텀 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide")

st.title("🥤 3D 커스텀 텀블러 보온·보냉 시뮬레이터")
st.caption("소재별 열전달률을 계산하고 실시간 온도가 떨어지는 과정을 3D로 관찰하세요.")

# 2. 소재 정보
INNER_MATERIALS = {
    "스테인리스 SUS304/316L": {"k_mod": 1.0, "color": "0xc0c8d0", "desc": "녹과 부식에 강하고 위생적입니다."},
    "세라믹 코팅": {"k_mod": 0.85, "color": "0xf0efe9", "desc": "착색과 냄새가 잘 배지 않습니다."},
    "붕규산 내열 유리": {"k_mod": 1.3, "color": "0x88ccee", "desc": "투명하며 급격한 온도 변화에 강합니다."}
}

INSULATION_MATERIALS = {
    "진공 단열층": {"k_mod": 0.010, "desc": "진공으로 열의 전도와 대류를 줄입니다."},
    "에어로겔": {"k_mod": 0.008, "desc": "가벼우면서 열을 잘 차단합니다."},
    "우레탄 폼": {"k_mod": 0.035, "desc": "가볍고 경제적이지만 단열 성능은 낮습니다."}
}

OUTER_MATERIALS = {
    "분체 도장 금속": {"k_mod": 1.0, "desc": "긁힘과 오염에 강합니다."},
    "실리콘 커버": {"k_mod": 0.9, "desc": "미끄럼을 줄이고 충격을 완화합니다."},
    "강화 플라스틱(PP/Tritan)": {"k_mod": 1.1, "desc": "가볍고 관리하기 쉽습니다."}
}

# 음료별 권장 섭취 온도 범위 (일반적인 기준이며 개인 취향에 따라 달라질 수 있음)
DRINKS = {
    "뜨거운 커피": {"kind": "hot", "good_min": 50, "good_max": 65, "default_temp": 85, "desc": "약 50~65°C가 마시기 좋은 범위"},
    "아이스 커피": {"kind": "cold", "good_min": 4, "good_max": 10, "default_temp": 25, "desc": "약 4~10°C가 마시기 좋은 범위"},
    "차(녹차·홍차)": {"kind": "hot", "good_min": 50, "good_max": 65, "default_temp": 75, "desc": "약 50~65°C가 마시기 좋은 범위"},
    "아이스티": {"kind": "cold", "good_min": 4, "good_max": 10, "default_temp": 25, "desc": "약 4~10°C가 마시기 좋은 범위"},
    "물": {"kind": "neutral", "good_min": 10, "good_max": 40, "default_temp": 50, "desc": "약 10~40°C를 편안하게 마시는 범위로 설정"},
    "라떼·우유": {"kind": "hot", "good_min": 45, "good_max": 60, "default_temp": 65, "desc": "약 45~60°C가 마시기 좋은 범위"},
    "스포츠음료": {"kind": "cold", "good_min": 4, "good_max": 12, "default_temp": 25, "desc": "약 4~12°C가 마시기 좋은 범위"}
}

# 3. 사이드바 UI
st.sidebar.header("🛠️ 텀블러 커스터마이징")
st.sidebar.header("🥤 음료 선택")
drink_name = st.sidebar.selectbox("마실 음료", list(DRINKS.keys()))
drink_info = DRINKS[drink_name]
st.sidebar.caption(drink_info["desc"])

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
st.sidebar.header("🎨 텀블러 외형 디자인")
BODY_COLORS = {
    "차콜 블랙": "#343e4a",
    "실버": "#aeb8c2",
    "로즈 핑크": "#d889a5",
    "아이스 블루": "#65b8d5",
    "포레스트 그린": "#397d68",
    "크림 화이트": "#e9e4d8"
}
body_color_name = st.sidebar.selectbox("외부 색상", list(BODY_COLORS.keys()))
body_color = BODY_COLORS[body_color_name]
surface_finish = st.sidebar.selectbox("표면 질감", ["무광", "유광", "메탈릭"])
lid_style = st.sidebar.selectbox("뚜껑 디자인", ["기본 뚜껑", "빨대 뚜껑", "원터치 뚜껑"])
show_handle = st.sidebar.checkbox("손잡이 표시", value=True)
show_straw = st.sidebar.checkbox("빨대 표시", value=False)
cutaway_view = st.sidebar.checkbox("내부 단면 보기", value=True)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ 환경 & 온도 설정")
t_env = st.sidebar.slider("외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("음료 초기 온도 (°C)", value=float(drink_info["default_temp"]), step=1.0, key="initial_temp_" + drink_name)

# 조건문을 명확한 if - elif - else로 구성하여 SyntaxError 완전 방지
if t_env < 5:
    rec_temp = 62.0
elif t_env > 28:
    rec_temp = 52.0
else:
    rec_temp = 58.0

info_text = "💡 " + drink_name + "의 권장 섭취 온도는 **" + str(drink_info["good_min"]) + "~" + str(drink_info["good_max"]) + "°C**입니다."
st.sidebar.info(info_text)

drink_target = (drink_info["good_min"] + drink_info["good_max"]) / 2 if drink_info["kind"] != "neutral" else 25.0
t_target = st.sidebar.number_input("목표 섭취 온도 (°C)", value=float(drink_target), step=1.0, key="target_temp_" + drink_name)
start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# 4. 물리 연산
k_total = INSULATION_MATERIALS[insul_mat_key]["k_mod"] * INNER_MATERIALS[inner_mat_key]["k_mod"] * OUTER_MATERIALS[outer_mat_key]["k_mod"]

# 이 프로그램은 냉각만 시뮬레이션합니다. 목표 온도가 초기 온도보다 높으면 가열 안내만 표시합니다.
if abs(t_init - t_target) <= 0.01:
    time_to_target = 0.0
    is_valid = False
    st.info("음료가 이미 목표 섭취 온도입니다.")
elif t_init < t_target:
    time_to_target = 30.0
    is_valid = False
    if t_env > t_target:
        st.warning("목표 섭취 온도가 초기 온도보다 높습니다. 음료를 데워야 하므로 냉각 시뮬레이션을 실행하지 않습니다.")
    else:
        st.warning("목표 섭취 온도가 초기 온도보다 높습니다. 목표 온도에 도달하려면 음료를 데워야 합니다. 이 프로그램에서는 가열 시뮬레이션을 지원하지 않습니다.")
elif t_target <= t_env:
    time_to_target = 30.0
    is_valid = False
    st.warning("외부 온도가 목표 섭취 온도보다 높거나 같아 자연 냉각만으로는 목표 온도에 도달할 수 없습니다.")
else:
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k_total
    is_valid = True

# 외부 온도에 따라 계절 배경을 선택합니다.
if t_env <= 5:
    bg_theme = "winter"
elif t_env <= 15:
    bg_theme = "spring"
elif t_env <= 25:
    bg_theme = "autumn"
else:
    bg_theme = "summer"

config_data = {
    "tInit": float(t_init),
    "tEnv": float(t_env),
    "tTarget": float(t_target),
    "kTotal": float(k_total),
    "timeToTarget": float(time_to_target),
    "bgTheme": bg_theme,
    "innerColorHex": INNER_MATERIALS[inner_mat_key]["color"],
    "shouldStart": True if (start_btn and is_valid) else False,
    "innerMaterialName": inner_mat_key,
    "insulationName": insul_mat_key,
    "outerMaterialName": outer_mat_key,
    "drinkName": drink_name,
    "drinkKind": drink_info["kind"],
    "goodTempMin": float(drink_info["good_min"]),
    "goodTempMax": float(drink_info["good_max"]),
    "bodyColor": body_color,
    "surfaceFinish": surface_finish,
    "lidStyle": lid_style,
    "showHandle": show_handle,
    "showStraw": show_straw,
    "cutaway": cutaway_view
}

# 5. UI 출력
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🎮 3D 커스텀 구조 반단면 텀블러")
    in_name = inner_mat_key.split(' (')[0]
    ins_name = insul_mat_key.split(' (')[0]
    out_name = outer_mat_key.split(' (')[0]
    st.caption("음료: **" + drink_name + "** · 선택 조합: **" + in_name + "** + **" + ins_name + "** + **" + out_name + "**")

    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        json_str = json.dumps(config_data)
        # 3D JavaScript가 실행되기 전에 설정값을 먼저 전달합니다.
        config_script = "<script>window.SO_HOT_CONFIG = " + json_str + ";</script>"
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", config_script + "</head>", 1)
        else:
            html_content = config_script + html_content
        components.html(html_content, height=650)
    else:
        st.error("❌ index.html 파일이 main.py와 동일한 위치에 존재하는지 확인해 주세요.")

with col2:
    st.subheader("📊 소재 계산 및 보온 대시보드")
    st.markdown("### 🧪 선택한 소재 특성")
    st.markdown("- **내부:** " + inner_desc)
    st.markdown("- **단열:** " + insul_desc)
    st.markdown("- **외부:** " + outer_desc)
    st.markdown("---")
    st.markdown("### 🧪 소재별 열전달 보정 계수")
    st.code("k_total = " + f"{k_total:.5f}")

    # k_total은 실제 물리 단위의 총괄 열전달계수가 아닌, 이 시뮬레이터 내부의 비교용 보정 지표입니다.
    if k_total <= 0.012:
        performance = "매우 우수"
        performance_detail = "열이 비교적 천천히 이동하도록 설정된 조합입니다. 음료의 온도를 오래 유지하는 데 유리합니다."
        st.success("🏆 **보온·보냉 성능: " + performance + "**")
    elif k_total <= 0.022:
        performance = "우수"
        performance_detail = "온도 유지 성능이 좋은 조합입니다."
        st.success("🟢 **보온·보냉 성능: " + performance + "**")
    elif k_total <= 0.035:
        performance = "보통"
        performance_detail = "온도 유지 성능이 보통 수준인 조합입니다."
        st.info("🔵 **보온·보냉 성능: " + performance + "**")
    else:
        performance = "낮음"
        performance_detail = "다른 조합보다 열이 빠르게 이동하도록 설정되어 있어 온도 유지 시간이 짧을 수 있습니다."
        st.warning("⚠️ **보온·보냉 성능: " + performance + "**")
    st.caption(performance_detail)
    st.caption("※ 등급은 이 프로그램의 소재 보정값 범위에 따른 상대 비교이며, 실제 제품의 실측 성능 등급은 아닙니다.")
    st.markdown("---")
    st.markdown("### ⏱️ 예상 보온 시간")
    if is_valid:
        st.success("🎯 **목표 온도 도달 시간:** 약 **" + f"{time_to_target:.1f}" + " 분**")
    elif abs(t_init - t_target) <= 0.01:
        st.info("현재 음료 온도가 목표 섭취 온도입니다.")
    else:
        st.caption("현재 설정에서는 냉각 시뮬레이션을 실행할 수 없습니다.")
