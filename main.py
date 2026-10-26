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
            st.session_state.current_time += time_to_target / 25.0
            time.sleep(0.12)
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

    # 아우라 색상 산출
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

        has_handle = "true" if "손잡이" in shape_style else "false"

        # 안전한 파이썬 변수 치환 방식 (.format) 적용으로 SyntaxError 완전 방지
        three_js_code = """
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

                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.9);
                dirLight1.position.set(5, 10, 7);
                scene.add(dirLight1);

                const grid = new THREE.GridHelper(10, 10, gridColor, 0x222222);
                grid.position.y = -1.9;
                scene.add(grid);

                const tumblerGroup = new THREE.Group();

                let bodyColor = 0xc0c8d0;
                let roughnessVal = 0.25;
                let metalnessVal = 0.85;

                if ("{material_name}".indexOf("유리") !== -1) {{
                    bodyColor = 0x88ccee;
                    roughnessVal = 0.05;
                    metalnessVal = 0.1;
                }} else if ("{material_name}".indexOf("플라스틱") !== -1) {{
                    bodyColor = 0xeb4d4b;
                    roughnessVal = 0.5;
                    metalnessVal = 0.05;
                }}

                // 불투명 반쪽 바디
                const solidBodyGeo = new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, 0, Math.PI);
                const solidBodyMat = new THREE.MeshStandardMaterial({{ 
                    color: bodyColor, 
                    roughness: roughnessVal, 
                    metalness: metalnessVal, 
                    side: THREE.DoubleSide 
                }});
                const solidBody = new THREE.Mesh(solidBodyGeo, solidBodyMat);
                tumblerGroup.add(solidBody);

                // 투명 단면 바디
                const glassBodyGeo = new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, Math.PI, Math.PI);
                const glassBodyMat = new THREE.MeshPhysicalMaterial({{ 
                    color: bodyColor, 
                    transparent: true, 
                    opacity: 0.22, 
                    roughness: 0.1, 
                    side: THREE.DoubleSide 
                }});
                const glassBody = new THREE.Mesh(glassBodyGeo, glassBodyMat);
                tumblerGroup.add(glassBody);

                // 뚜껑
                const lidGroup = new THREE.Group();
                const lidBaseGeo = new THREE.CylinderGeometry(0.92, 0.92, 0.35, 32);
                const lidMat = new THREE.MeshStandardMaterial({{ color: 0x222222, roughness: 0.7 }});
                const lidBase = new THREE.Mesh(lidBaseGeo, lidMat);
                lidGroup.add(lidBase);

                const spoutGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.2, 16);
                const spoutMat = new THREE.MeshStandardMaterial({{ color: 0x111111, roughness: 0.5 }});
                const spout = new THREE.Mesh(spoutGeo, spoutMat);
                spout.position.set(0.35, 0.2, 0);
                lidGroup.add(spout);

                lidGroup.position.y = 1.65;
                tumblerGroup.add(lidGroup);

                // 손잡이
                if ({has_handle}) {{
                    const handleGeo = new THREE.TorusGeometry(0.8, 0.08, 12, 24, Math.PI);
                    const handleMat = new THREE.MeshStandardMaterial({{ color: 0x222222, roughness: 0.8 }});
                    const handle = new THREE.Mesh(handleGeo, handleMat);
                    handle.rotation.z = -Math.PI / 2;
                    handle.position.set(-0.9, 0, 0);
                    tumblerGroup.add(handle);
                }}

                // 내부 음료
                const liquidGeo = new THREE.CylinderGeometry(0.78, 0.65, 2.5, 32);
                const liquidMat = new THREE.MeshStandardMaterial({{ color: 0x5d3a1a, roughness: 0.2 }});
                const liquid = new THREE.Mesh(liquidGeo, liquidMat);
                liquid.position.y = -0.15;
                tumblerGroup.add(liquid);

                // 3D Glow 아우라
                const auraGeo = new THREE.CylinderGeometry(1.1, 0.95, 3.2, 32);
                const auraMat = new THREE.MeshBasicMaterial({{ 
                    color: {aura_color}, 
                    transparent: true, 
                    opacity: 0.38, 
                    side: THREE.BackSide 
                }});
                const auraMesh = new THREE.Mesh(auraGeo, auraMat);
                tumblerGroup.add(auraMesh);

                scene.add(tumblerGroup);

                function animate() {{
                    requestAnimationFrame(animate);
                    tumblerGroup.rotation.y += 0.003;
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            </script>
        </body>
        </html>
        """.format(
            bg_theme=bg_theme,
            material_name=material_name,
            has_handle=has_handle,
            aura_color=aura_color,
        )

        components.html(three_js_code, height=480)

    with col2:
        st.subheader("🌡️ 실시간 온도 추적 패널")

        progress_ratio = min(curr_t / time_to_target, 1.0)
        st.progress(progress_ratio)

        st.markdown("### ⏱️ 예상 소요 시간 정보")
        if progress_ratio < 0.85 and st.session_state.simulating:
            st.info("⏳ **실시간 열전달률 분석 및 예측 시간 계산 중...**")
        else:
            st.success(
                f"🎯 **최적 온도까지 총 예상 시간:** 약 **{time_to_target:.1f} 분**"
            )

        st.metric(
            label="🌡️ 현재 음료 실시간 온도",
            value=f"{curr_temp:.1f} °C",
            delta=f"{curr_temp - t_init:.1f} °C (식는 중)",
        )

        st.markdown("---")

        if curr_t >= time_to_target and not st.session_state.simulating:
            st.subheader("📋 최종 분석 및 섭취 가이드")

            if 50 <= curr_temp <= 65:
                st.success(
                    f"☕ **[최적의 마심 골든타임 도달!]**\n\n"
                    f"현재 음료 온도는 **{curr_temp:.1f}°C**입니다.\n"
                    f"화상 위험 없이 가장 안전하고 깊은 풍미로 드실 수 있습니다."
                )
            elif curr_temp > 65:
                st.warning(
                    f"🔥 **[아직 다소 뜨거운 상태]**\n\n"
                    f"현재 음료 온도는 **{curr_temp:.1f}°C**입니다.\n"
                    f"입을 데일 수 있으니 조금만 더 식혀 드세요."
                )
            else:
                st.info(
                    f"❄️ **[많이 식은 상태]**\n\n"
                    f"현재 음료 온도는 **{curr_temp:.1f}°C**입니다.\n"
                    f"음료가 미지근해졌으니 따뜻한 음료를 원하시면 재가열이 필요합니다."
                )
        else:
            st.warning(
                f"⏳ **음료 온도가 서서히 감소하고 있습니다...**\n\n"
                f"3D 아우라가 초록색으로 바뀔 때까지 기다려 주세요."
            )
