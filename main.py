import math
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="3D 텀블러 보온 시뮬레이터", page_icon="🥤", layout="wide"
)

st.title("🥤 3D 로블록스 스타일 텀블러 보온·보냉 시뮬레이터")
st.caption(
    "화학공학의 열전달 원리와 뉴턴의 냉각 법칙을 기반으로 3D 인터랙티브 공간에서 음료 식힘을 추적합니다."
)

# 재질별 열손실 계수 (k) - 숫자가 클수록 빨리 식음
K_VALUES = {
    "진공 이중 구조 스텐 텀블러": 0.012,
    "이중 유리 텀블러": 0.025,
    "일반 플라스틱 텀블러": 0.045,
}

# 텀블러 재질별 3D 색상 (Hex Color)
MATERIAL_COLORS = {
    "진공 이중 구조 스텐 텀블러": "#A0AAB2",  # 메탈릭 은색
    "이중 유리 텀블러": "#88C1E0",  # 투명한 푸른빛
    "일반 플라스틱 텀블러": "#FF6B6B",  # 빨간 플라스틱
}

# ---------------------------------------------------------
# 2. 사이드바 사용자 제어판 (조건 설정)
# ---------------------------------------------------------
st.sidebar.header("🛠️ 텀블러 & 환경 설정")

material_name = st.sidebar.selectbox("1. 텀블러 재질", list(K_VALUES.keys()))
shape_style = st.sidebar.selectbox(
    "2. 텀블러 모양", ["기본 원통형 (Cylinder)", "슬림형 (Slim)"]
)

st.sidebar.markdown("---")
t_env = st.sidebar.slider("3. 외부(실내) 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("4. 음료 초기 온도 (°C)", value=90.0, step=1.0)
t_target = st.sidebar.number_input(
    "5. 목표 섭취 온도 (°C)", value=55.0, step=1.0
)

start_btn = st.sidebar.button("🚀 시뮬레이션 시작 / 재실행", type="primary")

# ---------------------------------------------------------
# 3. 예외 처리 (오류 방지 가드 구문)
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
# 4. 핵심 연산 및 3D 뷰어 출력
# ---------------------------------------------------------
if is_valid:
    k = K_VALUES[material_name]
    mat_color = MATERIAL_COLORS[material_name]

    # 뉴턴의 냉각 법칙을 통한 목표 시간(분) 역산
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k

    # 계산 결과를 상단에 크게 강조
    st.success(
        f"💡 **[{material_name}]** 기준, 약 **{time_to_target:.1f}분 후**에 마시기 가장 좋은 **{t_target}°C**에 도달합니다!"
    )

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("🎮 3D 텀블러 인터랙티브 뷰어")
        st.caption("마우스 클릭 후 드래그하여 로블록스처럼 3D 회전이 가능합니다.")

        # 텀블러 모양에 따른 반지름 변수
        radius = 1.0 if shape_style == "기본 원통형 (Cylinder)" else 0.7

        # Three.js 3D 캔버스 렌더링 HTML/JavaScript
        three_js_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; overflow: hidden; background-color: #1a1a1a; }}
                #canvas-container {{ width: 100vw; height: 420px; }}
            </style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="canvas-container"></div>
            <script>
                const container = document.getElementById('canvas-container');
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x1a1a1a);

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
                camera.position.set(0, 3, 7);

                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(container.clientWidth, container.clientHeight);
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;

                // 조명 설정
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                dirLight.position.set(5, 10, 7);
                scene.add(dirLight);

                // 바닥 격자 (로블록스 스타일)
                const grid = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
                grid.position.y = -2;
                scene.add(grid);

                // 텀블러 그룹
                const tumbler = new THREE.Group();

                // 1. 텀블러 몸체
                const bodyGeo = new THREE.CylinderGeometry({radius}, {radius} * 0.9, 3.2, 32);
                const bodyMat = new THREE.MeshStandardMaterial({{ 
                    color: '{mat_color}', 
                    metalness: 0.5, 
                    roughness: 0.3 
                }});
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                tumbler.add(body);

                // 2. 텀블러 뚜껑
                const lidGeo = new THREE.CylinderGeometry({radius} * 1.02, {radius} * 1.02, 0.4, 32);
                const lidMat = new THREE.MeshStandardMaterial({{ color: 0x333333, roughness: 0.8 }});
                const lid = new THREE.Mesh(lidGeo, lidMat);
                lid.position.y = 1.8;
                tumbler.add(lid);

                scene.add(tumbler);

                // 애니메이션 루프
                function animate() {{
                    requestAnimationFrame(animate);
                    tumbler.rotation.y += 0.005; // 천천히 자동 회전
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            </script>
        </body>
        </html>
        """
        components.html(three_js_code, height=430)

    with col2:
        st.subheader("🌡️ 온도 상태 실시간 변화")

        # 시뮬레이션용 시간 경과 슬라이더
        selected_minute = st.slider("⏱️ 시뮬레이션 시간 흐름 (분)", 0, 120, 0)

        # 선택한 시간에서의 음료 온도 계산 (뉴턴의 냉각 법칙)
        current_temp_val = t_env + (t_init - t_env) * math.exp(
            -k * selected_minute
        )

        st.metric(
            label=f"{selected_minute}분 후 예상 음료 온도",
            value=f"{current_temp_val:.1f} °C",
            delta=f"{current_temp_val - t_init:.1f} °C",
        )

        st.markdown("---")
        st.subheader("📢 음료 상태 판정")

        # 온도 조건별 맞춤 안내 카드
        if current_temp_val >= 65:
            st.error(
                f"🔥 **[아직 너무 뜨거워요!]** (현재 {current_temp_val:.1f}°C)\n\n입을 데일 위험이 매우 높습니다. 조금 더 식혀주세요."
            )
        elif 50 <= current_temp_val < 65:
            st.success(
                f"☕ **[지금이 먹기 딱 좋은 골든타임!]** (현재 {current_temp_val:.1f}°C)\n\n가장 안전하고 풍미가 완벽한 온도입니다. 맛있게 드세요!"
            )
        else:
            st.info(
                f"❄️ **[많이 식었어요!]** (현재 {current_temp_val:.1f}°C)\n\n음료가 미지근해졌습니다. 따뜻한 음료를 원하시면 다시 데워주세요."
            )
