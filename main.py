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
    "2. 텀블러 모양", ["기본 원통형 (Cylinder)", "슬림형 (Slim)"]
)

st.sidebar.markdown("---")
t_env = st.sidebar.slider("3. 현재 텀블러가 있는 곳의 외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("4. 음료 초기 온도 (°C)", value=90.0, step=1.0)

# 목표 온도 안내 추천 알고리즘 및 가이드
rec_temp = 58.0
if t_env < 5:
    rec_temp = 62.0  # 추운 날씨엔 조금 더 따뜻한 온도 추천
elif t_env > 28:
    rec_temp = 52.0  # 더운 날씨엔 비교적 적당히 따뜻한 온도 추천

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

    # 자동 온도 감쇠 로직 (버튼 클릭 시)
    if st.session_state.simulating:
        if st.session_state.current_time < time_to_target:
            st.session_state.current_time += time_to_target / 20.0  # 20단계 진행
            time.sleep(0.15)  # 서서히 내려가는 애니메이션 속도
            st.rerun()
        else:
            st.session_state.current_time = time_to_target
            st.session_state.simulating = False

    curr_t = st.session_state.current_time
    curr_temp = t_env + (t_init - t_env) * math.exp(-k * curr_t)

    # 3D 배경 테마 결정 (외부 온도 기준)
    if t_env >= 28:
        bg_theme = "summer"  # 여름
    elif t_env <= 10:
        bg_theme = "winter"  # 겨울
    else:
        bg_theme = "normal"  # 온난

    # 현재 온구간별 아우라 색상 결정 (3D 전달용)
    if curr_temp >= 65:
        aura_color = "0xff3333"  # 빨간색
    elif 50 <= curr_temp < 65:
        aura_color = "0x33ff66"  # 초록색
    else:
        aura_color = "0x3399ff"  # 파란색

    # ---------------------------------------------------------
    # 5. 메인 레이아웃 및 3D 뷰어 출력
    # ---------------------------------------------------------
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.subheader("🎮 3D 반단면 텀블러 실시간 시뮬레이터")
        st.caption(
            "반은 텀블러 외형, 반은 투명 반단면 구조로 내부와 음료 아우라를 관찰할 수 있습니다."
        )

        radius = 1.0 if shape_style == "기본 원통형 (Cylinder)" else 0.7

        three_js_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ margin: 0; overflow: hidden; background-color: #111; }}
                #canvas-container {{ width: 100vw; height: 450px; }}
            </style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="canvas-container"></div>
            <script>
                const container = document.getElementById('canvas-container');
                const scene = new THREE.Scene();

                // 1. 외부 온도 기반 3D 배경 설정
                let bgColor = 0x1a1a1a;
                let gridColor = 0x444444;
                if ("{bg_theme}" === "summer") {{
                    bgColor = 0x2b1d0c; // 여름: 사막/노을 느낌
                    gridColor = 0x885522;
                }} else if ("{bg_theme}" === "winter") {{
                    bgColor = 0x0f1a24; // 겨울: 설원/차가운 파란 느낌
                    gridColor = 0x4488aa;
                }}
                scene.background = new THREE.Color(bgColor);

                const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
                camera.position.set(2, 2.5, 6);

                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(container.clientWidth, container.clientHeight);
                container.appendChild(renderer.domElement);

                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;

                // 조명
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
                dirLight.position.set(5, 10, 7);
                scene.add(dirLight);

                // 바닥 격자
                const grid = new THREE.GridHelper(10, 10, gridColor, 0x222222);
                grid.position.y = -1.8;
                scene.add(grid);

                const tumblerGroup = new THREE.Group();

                // 2. 재질 특화 메쉬 생성 (반단면 구현: thetaLength = Math.PI)
                let matColor = 0xaaaaaa;
                let roughness = 0.3;
                let metalness = 0.8;

                if ("{material_name}".includes("유리")) {{
                    matColor = 0xaaddee;
                    roughness = 0.1;
                    metalness = 0.1;
                }} else if ("{material_name}".includes("플라스틱")) {{
                    matColor = 0xff5555;
                    roughness = 0.6;
                    metalness = 0.0;
                }}

                // [불투명 반쪽 몸체]
                const halfSolidGeo = new THREE.CylinderGeometry({radius}, {radius}*0.85, 3.0, 32, 1, false, 0, Math.PI);
                const solidMat = new THREE.MeshStandardMaterial({{ color: matColor, roughness: roughness, metalness: metalness, side: THREE.DoubleSide }});
                const halfSolid = new THREE.Mesh(halfSolidGeo, solidMat);
                tumblerGroup.add(halfSolid);

                // [투명 반단면 몸체] (안쪽이 보이도록 반대쪽 반원 처리)
                const halfGlassGeo = new THREE.CylinderGeometry({radius}, {radius}*0.85, 3.0, 32, 1, false, Math.PI, Math.PI);
                const glassMat = new THREE.MeshPhysicalMaterial({{ 
                    color: matColor, 
                    transparent: true, 
                    opacity: 0.25, 
                    roughness: 0.1, 
                    side: THREE.DoubleSide 
                }});
                const halfGlass = new THREE.Mesh(halfGlassGeo, glassMat);
                tumblerGroup.add(halfGlass);

                // [내부 음료 모형]
                const liquidGeo = new THREE.CylinderGeometry({radius}*0.78, {radius}*0.7, 2.6, 32);
                const liquidMat = new THREE.MeshStandardMaterial({{ color: 0x663300, roughness: 0.2 }}); // 커피색
                const liquid = new THREE.Mesh(liquidGeo, liquidMat);
                liquid.position.y = -0.1;
                tumblerGroup.add(liquid);

                // 3. 온도별 실시간 3D 아우라 (Glow Effect)
                const auraGeo = new THREE.CylinderGeometry({radius}*1.15, {radius}*1.0, 3.2, 32);
                const auraMat = new THREE.MeshBasicMaterial({{ 
                    color: {aura_color}, 
                    transparent: true, 
                    opacity: 0.35, 
                    side: THREE.BackSide 
                }});
                const auraMesh = new THREE.Mesh(auraGeo, auraMat);
                tumblerGroup.add(auraMesh);

                scene.add(tumblerGroup);

                function animate() {{
                    requestAnimationFrame(animate);
                    tumblerGroup.rotation.y += 0.003; // 천천히 자동 회전
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            </script>
        </body>
        </html>
        """
        components.html(three_js_code, height=460)

    with col2:
        st.subheader("🌡️ 실시간 온도 추적")

        # 진행도 프로그레스 바
        progress_val = min(curr_t / time_to_target, 1.0)
        st.progress(progress_val)

        st.metric(
            label="⏱️ 경과 시간",
            value=f"{curr_t:.1f} 분",
            delta=f"목표 {time_to_target:.1f}분 중",
        )

        st.metric(
            label="🌡️ 현재 음료 온도",
            value=f"{curr_temp:.1f} °C",
            delta=f"{curr_temp - t_init:.1f} °C (식는 중)",
        )

        st.markdown("---")

        # 최종 도착 여부에 따른 결과 팝업 창
        if curr_t >= time_to_target:
            st.balloons()  # 축하 효과
            st.subheader("🎉 목표 온도 도달 완료!")

            if 50 <= curr_temp <= 65:
                st.success(
                    f"☕ **[최적의 마심 골든타임!]**\n\n현재 온도는 **{curr_temp:.1f}°C**입니다. 입을 데일 염려 없이 가장 완벽하고 풍미 있게 음료를 즐기실 수 있습니다!"
                )
            elif curr_temp > 65:
                st.warning(
                    f"🔥 **[아직 약간 뜨거움]**\n\n현재 온도는 **{curr_temp:.1f}°C**입니다. 천천히 조심해서 마셔주세요."
                )
            else:
                st.info(
                    f"❄️ **[많이 식은 상태]**\n\n현재 온도는 **{curr_temp:.1f}°C**입니다. 미지근할 수 있으니 참고하세요."
                )
        else:
            st.warning(
                f"⏳ **온도가 서서히 내려가는 중입니다...**\n\n아우라 색상이 초록색으로 바뀔 때까지 기다려주세요."
            )
