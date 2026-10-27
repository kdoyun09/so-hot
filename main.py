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
# 2. 소재별 열전달 데이터 정의 (컬러값 hex 매핑)
# ---------------------------------------------------------
INNER_MATERIALS = {
    "SUS304/316L 위생 스테인리스": {"k_mod": 1.0, "color": "#c0c8d0"},
    "세라믹 코팅 (Ceramic Layer)": {"k_mod": 0.85, "color": "#f0efe9"},
    "내열 강화 유리 (Borosilicate)": {"k_mod": 1.3, "color": "#88ccee"},
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
start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# ---------------------------------------------------------
# 4. 종합 열전달 계수 계산 및 시간 제어
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

if start_btn and is_valid:
    st.session_state.simulating = True
    st.session_state.current_time = 0.0

if st.session_state.simulating:
    if st.session_state.current_time < time_to_target:
        st.session_state.current_time += time_to_target / 60.0
        time.sleep(0.04)
        st.rerun()
    else:
        st.session_state.current_time = time_to_target
        st.session_state.simulating = False

curr_t = st.session_state.current_time
curr_temp = t_env + (t_init - t_env) * math.exp(-k_total * curr_t)

bg_theme = "summer" if t_env >= 28 else ("winter" if t_env <= 10 else "normal")

if curr_temp >= 65:
    aura_color = "#ff2222"
elif 50 <= curr_temp < 65:
    aura_color = "#22ff66"
else:
    aura_color = "#2299ff"

inner_color_hex = INNER_MATERIALS[inner_mat]["color"]

# ---------------------------------------------------------
# 5. 메인 UI 화면 렌더링 (경로 오류 완전 제거)
# ---------------------------------------------------------
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🎮 3D 커스텀 구조 반단면 텀블러")
    st.caption(f"선택한 조합: **{inner_mat}** + **{insul_mat}** + **{outer_mat}**")

    # 충돌 없는 단일 스크립트 기반 Three.js 렌더러
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background-color: #111; }}
            #canvas-container {{ width: 100%; height: 480px; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <div id="canvas-container"></div>
        <script>
            window.onload = function() {{
                const container = document.getElementById("canvas-container");
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

                // 조명
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
                dirLight.position.set(5, 10, 7);
                scene.add(dirLight);

                // 바닥 격자
                const grid = new THREE.GridHelper(10, 10, gridColor, 0x222222);
                grid.position.y = -1.9;
                scene.add(grid);

                // 텀블러 그룹
                const tumblerGroup = new THREE.Group();

                // 1. 불투명 외벽 (반쪽)
                const solidGeo = new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, 0, Math.PI);
                const solidMat = new THREE.MeshStandardMaterial({{ color: 0x333333, roughness: 0.4, side: THREE.DoubleSide }});
                const solidMesh = new THREE.Mesh(solidGeo, solidMat);
                tumblerGroup.add(solidMesh);

                // 2. 투명 외벽 반단면 (반쪽)
                const glassGeo = new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, Math.PI, Math.PI);
                const glassMat = new THREE.MeshStandardMaterial({{ color: 0x888888, transparent: true, opacity: 0.25, side: THREE.DoubleSide }});
                const glassMesh = new THREE.Mesh(glassGeo, glassMat);
                tumblerGroup.add(glassMesh);

                // 3. 내벽 레이어 (선택한 색상)
                const innerGeo = new THREE.CylinderGeometry(0.82, 0.68, 2.8, 32, 1, false, 0, Math.PI);
                const innerMat = new THREE.MeshStandardMaterial({{ color: '{inner_color_hex}', metalness: 0.8, roughness: 0.2, side: THREE.DoubleSide }});
                const innerMesh = new THREE.Mesh(innerGeo, innerMat);
                tumblerGroup.add(innerMesh);

                // 4. 텀블러 뚜껑 & 스파우트
                const lidBase = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.92, 0.92, 0.35, 32),
                    new THREE.MeshStandardMaterial({{ color: 0x222222, roughness: 0.7 }})
                );
                lidBase.position.y = 1.65;
                tumblerGroup.add(lidBase);

                const spout = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.25, 0.25, 0.2, 16),
                    new THREE.MeshStandardMaterial({{ color: 0x111111, roughness: 0.5 }})
                );
                spout.position.set(0.35, 1.85, 0);
                tumblerGroup.add(spout);

                // 5. 손잡이
                const handle = new THREE.Mesh(
                    new THREE.TorusGeometry(0.8, 0.08, 12, 24, Math.PI),
                    new THREE.MeshStandardMaterial({{ color: 0x222222, roughness: 0.8 }})
                );
                handle.rotation.z = -Math.PI / 2;
                handle.position.set(-0.9, 0, 0);
                tumblerGroup.add(handle);

                // 6. 내부 음료
                const liquid = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.78, 0.64, 2.5, 32),
                    new THREE.MeshStandardMaterial({{ color: 0x5d3a1a, roughness: 0.2 }})
                );
                liquid.position.y = -0.15;
                tumblerGroup.add(liquid);

                // 7. 실시간 온도 Glow 아우라
                const aura = new THREE.Mesh(
                    new THREE.CylinderGeometry(1.1, 0.95, 3.2, 32),
                    new THREE.MeshBasicMaterial({{ color: '{aura_color}', transparent: true, opacity: 0.35, side: THREE.BackSide }})
                );
                tumblerGroup.add(aura);

                scene.add(tumblerGroup);

                // 마우스 드래그 회전 인터랙션 구현
                let isDragging = false;
                let previousMousePosition = {{ x: 0, y: 0 }};

                const domElement = renderer.domElement;
                domElement.addEventListener('mousedown', (e) => {{
                    isDragging = true;
                }});
                domElement.addEventListener('mousemove', (e) => {{
                    const deltaMove = {{
                        x: e.offsetX - previousMousePosition.x,
                        y: e.offsetY - previousMousePosition.y
                    }};
                    if (isDragging) {{
                        tumblerGroup.rotation.y += deltaMove.x * 0.01;
                        tumblerGroup.rotation.x += deltaMove.y * 0.01;
                    }}
                    previousMousePosition = {{ x: e.offsetX, y: e.offsetY }};
                }});
                window.addEventListener('mouseup', () => {{ isDragging = false; }});

                // 자동 회전 및 렌더링 루프
                function animate() {{
                    requestAnimationFrame(animate);
                    if (!isDragging) {{
                        tumblerGroup.rotation.y += 0.005;
                    }}
                    renderer.render(scene, camera);
                }}
                animate();
            }};
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=490)

with col2:
    st.subheader("🌡️ 실시간 연속 온도 추적")

    progress_ratio = min(curr_t / time_to_target, 1.0)
    st.progress(progress_ratio)

    st.markdown("### ⏱️ 예상 소요 시간 정보")
    if progress_ratio < 0.85 and st.session_state.simulating:
        st.info("⏳ **실시간 소재 열전달율 분석 및 예측 시간 계산 중...**")
    else:
        st.success(f"🎯 **최적 온도까지 총 예상 시간:** 약 **{time_to_target:.1f} 분**")

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
                f"현재 음료 온
