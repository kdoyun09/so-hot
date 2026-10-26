import math
import time
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="3D 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide"
)

st.title("🥤 3D 텀블러 보온·보냉 시뮬레이터")
st.caption(
    "화학공학의 열전달 원리와 뉴턴의 냉각 법칙을 기반으로 3D 공간에서 음료 식힘 과정을 실시간으로 추적합니다."
)

# 재질별 열손실 계수 (k)
K_VALUES = {
    "진공 이중 구조 스텐 텀블러": 0.012,
    "이중 유리 텀블러": 0.025,
    "일반 플라스틱 텀블러": 0.045,
}

# ---------------------------------------------------------
# 2. 사이드바 제어판 (조건 설정 & 추천 가이드)
# ---------------------------------------------------------
st.sidebar.header("🛠️ 텀블러 & 환경 설정")

material_name = st.sidebar.selectbox("1. 텀블러 재질", list(K_VALUES.keys()))
shape_style = st.sidebar.selectbox(
    "2. 텀블러 디자인 스타일",
    ["시그니처 손잡이형 텀블러", "슬림 캐리 텀블러"],
)

st.sidebar.markdown("---")
t_env = st.sidebar.slider("3. 현재 텀블러가 있는 곳의 외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("4. 음료 초기 온도 (°C)", value=90.0, step=1.0)

# 목표 온도 안내 추천 알고리즘 및 가이드
rec_temp = 58.0
if t_env < 5:
    rec_temp = 62.0
elif t_env > 28:
    rec_temp = 52.0

st.sidebar.info(
    f"💡 **목표 온도 추천 가이드:**\n\n"
    f"현재 외부 온도({t_env}°C) 기준, 사람이 화상을 입지 않고 가장 최적의 풍미를 느낄 수 있는 온도는 **{rec_temp}°C 내외**입니다. (일반 권장: 50°C~65°C)"
)

t_target = st.sidebar.number_input(
    "5. 목표 섭취 온도 (°C)", value=rec_temp, step=1.0
)

start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# ---------------------------------------------------------
# 3. 예외 처리 (입력 검증)
# ---------------------------------------------------------
is_valid = True
if t_init <= t_env:
    st.error(
        "❌ [오류] 음료의 초기 온도가 외부 온도보다 높아야 보온 시뮬레이션이 가능합니다."
    )
    is_valid = False
elif t_target >= t_init:
    st.error(
        "❌ [오류] 마시기 좋은 목표 온도는 초기 음료 온도보다 낮아야 합니다."
    )
    is_valid = False
elif t_target <= t_env:
    st.error(
        "❌ [오류] 목표 온도가 외부 온도보다 낮으면 음료가 식어서 도달할 수 없습니다."
    )
    is_valid = False

# ---------------------------------------------------------
# 4. 시뮬레이션 상태 관리 및 실시간 애니메이션
# ---------------------------------------------------------
if is_valid:
    k = K_VALUES[material_name]
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k

    # 세션 상태 초기화
    if "simulating" not in st.session_state:
        st.session_state.simulating = False
    if "current_time" not in st.session_state:
        st.session_state.current_time = 0.0

    if start_btn:
        st.session_state.simulating = True
        st.session_state.current_time = 0.0

    # 자동 온도 감쇠 진행 (서서히 감소하는 연출)
    if st.session_state.simulating:
        if st.session_state.current_time < time_to_target:
            st.session_state.current_time += time_to_target / 25.0  # 25단계 진행
            time.sleep(0.12)  # 자연스러운 실시간 인터벌
            st.rerun()
        else:
            st.session_state.current_time = time_to_target
            st.session_state.simulating = False

    curr_t = st.session_state.current_time
    curr_temp = t_env + (t_init - t_env) * math.exp(-k * curr_t)

    # 3D 배경 테마 결정 (외부 온도 기준)
    if t_env >= 28:
        bg_theme = "summer"
    elif t_env <= 10:
        bg_theme = "winter"
    else:
        bg_theme = "normal"

    # 아우라 색상 산출 (3D 뷰어)
    if curr_temp >= 65:
        aura_color = "0xff2222"
    elif 50 <= curr_temp < 65:
        aura_color = "0x22ff66"
    else:
        aura_color = "0x2299ff"

    # ---------------------------------------------------------
    # 5. 메인 레이아웃 및 디테일 3D 뷰어 출력
    # ---------------------------------------------------------
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("🎮 실물 디자인 3D 반단면 텀블러")
        st.caption(
            "실제 텀블러 구조(뚜껑, 스파우트 입구, 손잡이, 내부 단면)와 온도별 아우라를 360도 회전하며 관찰하세요."
        )

        has_handle = "손잡이" in shape_style

        three_js_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; overflow: hidden; background-color: #111; }}
                #canvas-container {{ width: 100vw; height: 470px; }}
            </style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="canvas-container"></div>
            <script>
                const container = document.getElementById('canvas-container');
                const scene = new THREE.Scene();

                // 1. 외부 온도 기반 3D 배경
                let bgColor = 0x181818;
                let gridColor = 0x444444;
                if ("{bg_theme}" === "summer") {{
                    bgColor = 0x2b1c0c;
                    gridColor = 0x885522;
                }} else if ("{bg_theme}" === "winter") {{
                    bgColor = 0x0a1622;
                    gridColor = 0x3377aa;
                }}
                scene.background = new THREE.Color(bgColor);

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
                camera.position.set(2.8, 2.2, 5.8);

                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(container.clientWidth, container.clientHeight);
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;

                // 조명
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambient
