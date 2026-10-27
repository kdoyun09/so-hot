import math
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
# 2. 소재별 상세 정보 및 설명 데이터 정의
# ---------------------------------------------------------
INNER_MATERIALS = {
    "SUS304/316L 위생 스테인리스 (위생성 & 내구성 우수)": {
        "k_mod": 1.0,
        "color": "0xc0c8d0",
        "desc": "🛡️ **특징:** 부식과 녹에 강한 의료·식품용 위생 소재입니다. 내구성이 뛰어나며 변형이 적지만, 착색이나 냄새 배임이 약간 있을 수 있습니다."
    },
    "세라믹 코팅 (Ceramic Layer - 착색·냄새 방지)": {
        "k_mod": 0.85,
        "color": "0xf0efe9",
        "desc": "☕ **특징:** 도자기 코팅을 입혀 커피나 음료의 착색 및 냄새 배임을 완벽히 차단합니다. 금속 맛이 나지 않아 음료 본연의 맛을 유지합니다."
    },
    "내열 강화 유리 (Borosilicate - 투명성 & 열충격 강함)": {
        "k_mod": 1.3,
        "color": "0x88ccee",
        "desc": "💎 **특징:** 열충격에 강한 붕규산 유리 소재입니다. 내부 음료 상태를 투명하게 확인할 수 있으나, 스테인리스 대비 열손실이 약간 더 빠릅니다."
    },
}

INSULATION_MATERIALS = {
    "진공 단열층 (High-Vacuum Layer - 최상급 보온)": {
        "k_mod": 0.010,
        "desc": "🔥 **특징:** 내벽과 외벽 사이를 고진공 상태로 만들어 전도·대류에 의한 열손실을 극단적으로 차단하는 표준 최상급 보온 구조입니다."
    },
    "에어로겔 (Aerogel Insulation - 우주공학 신소재)": {
        "k_mod": 0.008,
        "desc": "🚀 **특징:** '고체 공기'라 불리는 우주공학 신소재 단열재입니다. 두께 대비 열차단 성능이 전 세계 최고 수준으로 매우 탁월합니다."
    },
    "고밀도 우레탄 폼 (Urethane Foam - 실속형 보온)": {
        "k_mod": 0.035,
        "desc": "📦 **특징:** 일반 보온 도시락 및 저가형 보온병에 쓰이는 고밀도 폼 충전재입니다. 진공층에 비해 가벼우나 보온 지속 시간은 비교적 짧습니다."
    },
}

OUTER_MATERIALS = {
    "파우더 코팅 메탈 (Powder Coated Metal - 강한 내구성)": {
        "k_mod": 1.0,
        "rough": 0.3,
        "desc": "🎨 **특징:** 분체 도장 기법으로 외부 스크래치와 오염에 강합니다. 고급스러운 매트 감촉과 뛰어난 그립감을 제공합니다."
    },
    "친환경 실리콘 커버 (Silicone Grip - 미끄럼 방지)": {
        "k_mod": 0.9,
        "rough": 0.7,
        "desc": "🖐️ **특징:** 손에 착 감기는 미끄럼 방지 그립감을 주며, 낙하 시 충격을 완화해 줍니다. 열전달을 한 번 더 막아주는 효과가 있습니다."
    },
    "BPA-Free 강화 플라스틱 (PP/Tritan - 가벼움 & 스크래치 강함)": {
        "k_mod": 1.1,
        "rough": 0.5,
        "desc": "🌱 **특징:** 환경호르몬이 나오지 않는 안전한 친환경 플라스틱 소재입니다. 무게가 매우 가벼워 휴대성이 극대화됩니다."
    },
}

# ---------------------------------------------------------
# 3. 사이드바 UI 설정
# ---------------------------------------------------------
st.sidebar.header("🛠️ 텀블러 커스터마이징")

inner_mat_key = st.sidebar.selectbox("1. 내부 재질 (음료 접촉)", list(INNER_MATERIALS.keys()))
inner_desc = INNER_MATERIALS[inner_mat_key]["desc"]
st.sidebar.caption(inner_desc)

insul_mat_key = st.sidebar.selectbox("2. 단열 구조 (중간 단열재)", list(INSULATION_MATERIALS.keys()))
insul_desc = INSULATION_MATERIALS[insul_mat_key]["desc"]
st.sidebar.caption(insul_desc)

outer_mat_key = st.sidebar.selectbox("3. 외부 재질 (손잡이/외벽)", list(OUTER_MATERIALS.keys()))
outer_desc = OUTER_MATERIALS[outer_mat_key]["desc"]
st.sidebar.caption(outer_desc)

st.sidebar.markdown("---")
st.sidebar.header("🌡️ 환경 & 온도 설정")
t_env = st.sidebar.slider("현재 텀블러가 있는 곳의 외부 온도 (°C)", -10, 40, 20)
t_init = st.sidebar.number_input("음료 초기 온도 (°C)", value=90.0, step=1.0)

rec_temp = 58.0
if t_env < 5:
    rec_temp = 62.0
elif t_env > 28:
    rec_temp = 52.0

info_msg = "💡 **목표 온도 추천 가이드:**\n\n현재 외부 온도({}°C) 기준, 화상 없이 맛을 즐기기 가장 좋은 온도는 **{}°C 내외**입니다.".format(t_env, rec_temp)
st.sidebar.info(info_msg)

t_target = st.sidebar.number_input("목표 섭취 온도 (°C)", value=rec_temp, step=1.0)
start_btn = st.sidebar.button("🚀 시뮬레이션 시작", type="primary")

# ---------------------------------------------------------
# 4. 연산 및 물리 계산
# ---------------------------------------------------------
k_total = (
    INSULATION_MATERIALS[insul_mat_key]["k_mod"]
    * INNER_MATERIALS[inner_mat_key]["k_mod"]
    * OUTER_MATERIALS[outer_mat_key]["k_mod"]
)

if t_init > t_env and t_target < t_init and t_target > t_env:
    time_to_target = -math.log((t_target - t_env) / (t_init - t_env)) / k_total
    is_valid = True
else:
    time_to_target = 30.0
    is_valid = False
    st.error("❌ 입력한 온도가 올바르지 않습니다. (초기온도 > 목표온도 > 외부온도 규칙 필요)")

bg_theme = "summer" if t_env >= 28 else ("winter" if t_env <= 10 else "normal")
inner_color_hex = INNER_MATERIALS[inner_mat_key]["color"]
should_start = "true" if (start_btn and is_valid) else "false"

# ---------------------------------------------------------
# 5. 메인 UI 및 통합 3D WebGL 엔진
# ---------------------------------------------------------
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader("🎮 3D 커스텀 구조 반단면 텀블러")
    
    in_name = inner_mat_key.split(' (')[0]
    ins_name = insul_mat_key.split(' (')[0]
    out_name = outer_mat_key.split(' (')[0]
    caption_text = "선택한 조합: **{}** + **{}** + **{}**".format(in_name, ins_name, out_name)
    st.caption(caption_text)

    # 3D HTML / Three.js 완전 자체 포함 스트링
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; background-color: #111; font-family: sans-serif; }}
        #canvas-container {{ width: 100vw; height: 480px; position: relative; }}
        #temp-display {{
            position: absolute; top: 15px; left: 15px; color: #fff;
            background: rgba(0, 0, 0, 0.75); padding: 10px 16px; border-radius: 8px;
            font-size: 18px; font-weight: bold; border: 1px solid #444; z-index: 10;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="canvas-container">
        <div id="temp-display">🌡️ 실시간 온도: <span id="current-temp-val">{t_init_disp:.1f}</span> °C</div>
    </div>
    <script>
        window.onload = function() {{
            const container = document.getElementById("canvas-container");
            const tempValElem = document.getElementById("current-temp-val");

            const width = container.clientWidth || window.innerWidth || 600;
            const height = 480;

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

            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            camera.position.set(0, 0.8, 7.5);
            camera.lookAt(0, 0, 0);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
            container.appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
            dirLight.position.set(5, 10, 7);
            scene.add(dirLight);

            const grid = new THREE.GridHelper(10, 10, gridColor, 0x333333);
            grid.position.y = -2.2;
            scene.add(grid);

            const tumblerGroup = new THREE.Group();

            // 1. 불투명 외벽 (반쪽)
            const solidMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, 0, Math.PI),
                new THREE.MeshStandardMaterial({{ color: 0x333333, roughness: 0.4, side: THREE.DoubleSide }})
            );
            tumblerGroup.add(solidMesh);

            // 2. 투명 외벽 (반쪽)
            const glassMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.9, 0.75, 3.0, 32, 1, false, Math.PI, Math.PI),
                new THREE.MeshStandardMaterial({{ color: 0x888888, transparent: true, opacity: 0.3, side: THREE.DoubleSide }})
            );
            tumblerGroup.add(glassMesh);

            // 3. 내벽 레이어
            const innerMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.82, 0.68, 2.8, 32, 1, false, 0, Math.PI),
                new THREE.MeshStandardMaterial({{ color: {inner_color_hex}, metalness: 0.8, roughness: 0.2, side: THREE.DoubleSide }})
            );
            tumblerGroup.add(innerMesh);

            // 4. 뚜껑 & 스파우트
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

            // 6. 음료
            const liquid = new THREE.Mesh(
                new THREE.CylinderGeometry(0.78, 0.64, 2.5, 32),
                new THREE.MeshStandardMaterial({{ color: 0x5d3a1a, roughness: 0.2 }})
            );
            liquid.position.y = -0.15;
            tumblerGroup.add(liquid);

            // 7. 실시간 Glow 아우라
            const auraMat = new THREE.MeshBasicMaterial({{ color: 0xff2222, transparent: true, opacity: 0.35, side: THREE.BackSide }});
            const aura = new THREE.Mesh(
                new THREE.CylinderGeometry(1.1, 0.95, 3.2,
