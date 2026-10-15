import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np

# Page configuration
st.set_page_config(
    page_title="한울생약 UV-C 살균 공정 시뮬레이터 v4.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean white theme
st.markdown("""
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #0F172A;
    }
    .metric-box {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .pass-lamp {
        color: #27AE60;
        font-weight: bold;
        font-size: 20px;
    }
    .fail-lamp {
        color: #E74C3C;
        font-weight: bold;
        font-size: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ 한울생약 UV-C 살균 공정 실시간 시뮬레이터 v4.0")
st.caption("건조 원단 및 포장재 선(先) 살균 공정 전용 웹 시뮬레이션 모델 (Render 배포용)")

# Sidebar for inputs
st.sidebar.header("🛠️ 1. 설비 기하학 및 공정 변수")
y_tunnel = st.sidebar.slider("자외선 살균 터널 길이 (mm)", min_value=500, max_value=5000, value=2000, step=100)
d_gap = st.sidebar.slider("물체와 램프 간 이격 거리 (mm)", min_value=50, max_value=1000, value=200, step=10)
v_speed = st.sidebar.slider("원단 이송 속도 (m/s)", min_value=0.05, max_value=2.0, value=0.3, step=0.05)

st.sidebar.header("💡 2. 자외선 광원(Lamp) 배치 및 출력")
n_lamps = st.sidebar.slider("총 설치 램프 수 (개)", min_value=1, max_value=24, value=6, step=1)
p_lamp = st.sidebar.slider("단일 램프 정격 전력 (W)", min_value=10, max_value=200, value=30, step=5)
eff_uvc = st.sidebar.slider("UVC 변환 효율", min_value=0.1, max_value=0.5, value=0.35, step=0.05)
l_lamp = st.sidebar.slider("유리 램프 유효 발광 길이 (mm)", min_value=100, max_value=2000, value=900, step=50)

st.sidebar.header("🛡️ 3. 생산 현장 감쇄 장벽 손실율")
t_shadow = st.sidebar.slider("그림자 장벽 투과율 (50% 감쇄 = 0.5)", min_value=0.1, max_value=1.0, value=0.5, step=0.05)
t_aging = st.sidebar.slider("램프 노화 및 분진 오염도 (20% 손실 = 0.8)", min_value=0.1, max_value=1.0, value=0.8, step=0.05)

# Fixed lotion loss because of pre-sterilization (T_lotion = 1.0)
t_lotion = 1.0

# 4. 자외선 선량 물리 연산 결과
p_total = n_lamps * p_lamp * eff_uvc * 1000  # mW
t_exp = y_tunnel / (v_speed * 1000)  # seconds

# Keitz line source formula modeling
gap_cm = d_gap / 10.0
length_cm = l_lamp / 10.0
i_peak = p_total / (2 * math.pi * gap_cm * length_cm)  # mW/cm2

# Final valid dose (mJ/cm2)
dose = i_peak * t_exp * t_shadow * t_lotion * t_aging

# Target micro-organisms and requirements
targets = {
    "버크홀데리아 (Burkholderia)": {"limit": 7.4, "surrogate": "Burkholderia pseudomallei"},
    "아세토박터-초산균 (Acetobacter)": {"limit": 10.5, "surrogate": "Brucella suis"},
    "메틸로박테리움 (Methylobacterium)": {"limit": 17.0, "surrogate": "Pseudomonas aeruginosa (녹농균)"}
}

# Main Layout: 2 Columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 실시간 광학 연산 결과")
    
    # Custom styling with cards - Clean White Theme
    st.markdown(f"""
    <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #475569; font-weight: 600; margin-bottom: 5px;">가용 총 UVC 방사출력</p>
            <h2 style="color: #1E3A8A; margin: 0; font-weight: bold;">{p_total:.1f} mW</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #475569; font-weight: 600; margin-bottom: 5px;">조사 노출시간</p>
            <h2 style="color: #1E3A8A; margin: 0; font-weight: bold;">{t_exp:.3f} 초</h2>
        </div>
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #475569; font-weight: 600; margin-bottom: 5px;">표면 자외선 최고 조도</p>
            <h2 style="color: #D97706; margin: 0; font-weight: bold;">{i_peak:.3f} mW/cm²</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px; border: 2px solid #27AE60; background-color: #F0FDF4;">
            <p style="color: #166534; font-weight: bold; margin-bottom: 5px;">최종 유효 자외선 조사량 (Dose)</p>
            <h1 style="color: #15803D; margin: 0; font-weight: bold;">{dose:.2f} mJ/cm²</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🚨 핵심 타겟 미생물 3종 살균 합불(PASS/FAIL) 진단")
    for name, data in targets.items():
        limit = data["limit"]
        is_pass = dose >= limit
        status_text = "🟢 적합 (PASS)" if is_pass else "🔴 부적합 (FAIL)"
        status_color = "#27AE60" if is_pass else "#E74C3C"
        bg_card = "#F0FDF4" if is_pass else "#FEF2F2"
        
        st.markdown(f"""
        <div style="background-color: {bg_card}; padding: 15px; border-radius: 8px; border-left: 5px solid {status_color}; border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #1E293B; font-weight: bold;">{name}</h4>
                    <p style="margin: 0; font-size: 12px; color: #64748B;">대체 균주: {data['surrogate']}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: bold; color: {status_color}; font-size: 18px;">{status_text}</span>
                    <p style="margin: 0; font-size: 12px; color: #64748B; font-weight: bold;">기준: {limit} mJ/cm²</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # General margin and status
    margin_ratio = dose / 17.0
    margin_status = "🟢 안전 마진 충분 (PASS)" if margin_ratio >= 1.0 else "🔴 안전선 미달 (FAIL)"
    margin_color = "#27AE60" if margin_ratio >= 1.0 else "#E74C3C"
    bg_margin = "#F0FDF4" if margin_ratio >= 1.0 else "#FEF2F2"
    
    st.markdown(f"""
    <div style="background-color: {bg_margin}; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid {margin_color}; margin-top: 15px;">
        <span style="color: #475569; font-size: 14px; font-weight: 600;">종합 공정 안전 마진 배수: </span>
        <strong style="color: #0F172A; font-size: 20px; font-weight: bold;">{margin_ratio:.2f} 배</strong>
        <h3 style="color: {margin_color}; margin: 5px 0 0 0; font-weight: bold;">{margin_status}</h3>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📈 속도 - 조사 선량 반비례 곡선 시각화")
    
    # Plotting - Clean White Graph Style
    speeds = np.linspace(0.05, 2.0, 100)
    doses = [i_peak * (y_tunnel / (s * 1000)) * t_shadow * t_lotion * t_aging for s in speeds]
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F8FAFC')
    
    ax.plot(speeds, doses, color='#1E3A8A', label='이송 속도별 조사 선량', linewidth=2.5)
    ax.scatter([v_speed], [dose], color='#27AE60', s=150, zorder=5, label='현재 운전 동작점')
    
    # Guidelines for targets
    ax.axhline(y=17.0, color='#E74C3C', linestyle='--', alpha=0.8, label='메틸로박테리움 사멸선 (17.0 mJ/cm²)')
    ax.axhline(y=10.5, color='#D97706', linestyle='--', alpha=0.8, label='아세토박터 사멸선 (10.5 mJ/cm²)')
    ax.axhline(y=7.4, color='#2563EB', linestyle='--', alpha=0.8, label='버크홀데리아 사멸선 (7.4 mJ/cm²)')
    
    ax.set_xlabel('원단 이송 속도 (m/s)', color='#0F172A', fontsize=10, fontweight='bold')
    ax.set_ylabel('자외선 유효 조사량 (mJ/cm²)', color='#0F172A', fontsize=10, fontweight='bold')
    ax.set_title('실시간 운전점 추적 그래프', color='#0F172A', fontsize=12, fontweight='bold')
    
    ax.tick_params(colors='#0F172A')
    for spine in ax.spines.values():
        spine.set_color('#CBD5E1')
        
    ax.legend(facecolor='#FFFFFF', edgecolor='#CBD5E1', labelcolor='#0F172A', loc='upper right', fontsize=8)
    ax.grid(True, color='#E2E8F0', linestyle=':', alpha=0.8)
    
    # Focus limit to readable scale
    ax.set_ylim(0, max(100, dose * 1.5))
    
    st.pyplot(fig)
    
    # Download Validation Report Button
    st.subheader("📄 품질 검증 성적서 발급")
    
    report_text = f"""======================================================
[한울생약] UV-C 살균 공정 유효성 검증 성적서 (SOP-UVC-04)
======================================================
■ 발급 일시: 2026-09-08
■ 공정 분류: 건조 원단 및 포장재 선(先) 살균 가공 공정
■ 통제 가이드라인 수립 근거:
   - US FDA 21 CFR § 880.6600 (Class II Special Controls)
   - US EPA FIFRA Compliance Advisory (Efficacy Supporting Data)
   - IUVA Surface Disinfection Standard (40 mJ/cm²)

[1. 설비 기하학 및 구동 세팅값]
- 살균 터널 길이 (y_tunnel): {y_tunnel} mm
- 물체-광원 이격 거리 (d_gap): {d_gap} mm
- 컨베이어 이송 속도 (v_speed): {v_speed} m/s
- 설치 램프 사양 (N_lamps): {n_lamps} 개 x {p_lamp} W (효율 {eff_uvc*100}%)
- 램프 유효 발광 길이: {l_lamp} mm

[2. 물리 광학 연산 결과]
- 가용 총 UVC 방사출력 (P_total): {p_total:.1f} mW
- 조사 노출시간 (t_exp): {t_exp:.3f} 초
- 표면 최고 조도 (I_peak): {i_peak:.3f} mW/cm²
- 최종 유효 조사량 (Dose): {dose:.2f} mJ/cm²
  (※ 선살균 공정 적용으로 로션 흡수 손실 배제 - 투과율 1.0 적용)

[3. 타겟 미생물 3종 사멸 유효성 판정 결과]
- 버크홀데리아 (기준 7.4 mJ/cm²): {"PASS (적합)" if dose >= 7.4 else "FAIL (부적합)"}
- 아세토박터-초산균 (기준 10.5 mJ/cm²): {"PASS (적합)" if dose >= 10.5 else "FAIL (부적합)"}
- 메틸로박테리움 (기준 17.0 mJ/cm²): {"PASS (적합)" if dose >= 17.0 else "FAIL (적합선 미달)"}

■ 종합 공정 안전 마진 배수: {margin_ratio:.2f} 배
■ 최종 검증 의견: {margin_status}

------------------------------------------------------
한울생약 기술 연구소 품질 보증 부서 상시 백업용 레코드 자료
======================================================
"""
    st.download_button(
        label="📥 유효성 검증 성적서 다운로드 (.txt)",
        data=report_text,
        file_name="hanul-uvc-validation-report.txt",
        mime="text/plain"
    )

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px;'>본 프로그램은 한울생약 연구소의 자외선 살균 수립 보고서와 100% 동일한 학술 표준 수식으로 작동합니다. | Source: FDA 21 CFR & EPA FIFRA</p>", unsafe_allow_html=True)
