import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np

# Page configuration
st.set_page_config(
    page_title="한울생약 UV-C 살균 공정 시뮬레이터 v6.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Theme (Clean White Background) - Force White everywhere
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    .main .block-container {
        padding-top: 2rem !important;
        background-color: #FFFFFF !important;
    }
    /* Metric Cards */
    .metric-box {
        background-color: #F8FAFC !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        text-align: center !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
    }
    .metric-box p {
        color: #475569 !important;
        margin-bottom: 5px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .metric-box h2 {
        color: #1D4ED8 !important;
        margin: 0 !important;
        font-weight: 700 !important;
        font-size: 26px !important;
    }
    .metric-box h1 {
        margin: 0 !important;
        font-weight: 800 !important;
        font-size: 32px !important;
    }
    /* Status card */
    .status-card {
        padding: 16px !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ 한울생약 UV-C 살균 공정 실시간 시뮬레이터 v6.0")
st.caption("건조 원단 및 포장재 선(先) 살균 가공 공정 전용 웹 시뮬레이션 모델 (Clean Light Mode)")

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
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-around; margin-bottom: 15px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p>가용 총 UVC 방사출력</p>
            <h2>{p_total:.1f} mW</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p>조사 노출시간</p>
            <h2>{t_exp:.3f} 초</h2>
        </div>
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p>표면 자외선 최고 조도</p>
            <h2 style="color: #D97706 !important;">{i_peak:.3f} mW/cm²</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px; border: 2px solid #16A34A !important; background-color: #F0FDF4 !important;">
            <p style="color: #15803D !important;">최종 유효 자외선 조사량 (Dose)</p>
            <h1 style="color: #15803D !important;">{dose:.2f} mJ/cm²</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🚨 핵심 타겟 미생물 3종 살균 합불(PASS/FAIL) 진단")
    for name, data in targets.items():
        limit = data["limit"]
        is_pass = dose >= limit
        status_text = "🟢 적합 (PASS)" if is_pass else "🔴 부적합 (FAIL)"
        status_color = "#16A34A" if is_pass else "#DC2626"
        bg_color = "#F0FDF4" if is_pass else "#FEF2F2"
        border_color = "#BBF7D0" if is_pass else "#FECACA"
        
        st.markdown(f"""
        <div class="status-card" style="background-color: {bg_color} !important; border-left: 6px solid {status_color} !important; border-top: 1px solid {border_color} !important; border-right: 1px solid {border_color} !important; border-bottom: 1px solid {border_color} !important;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #0F172A !important; font-weight: 700;">{name}</h4>
                    <p style="margin: 3px 0 0 0; font-size: 13px; color: #475569 !important;">대체 균주: {data['surrogate']}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: 800; color: {status_color} !important; font-size: 20px;">{status_text}</span>
                    <p style="margin: 3px 0 0 0; font-size: 13px; color: #475569 !important;">기준: {limit} mJ/cm²</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # General margin and status
    margin_ratio = dose / 17.0
    margin_status = "🟢 안전 마진 충분 (PASS)" if margin_ratio >= 1.0 else "🔴 안전선 미달 (FAIL)"
    margin_color = "#16A34A" if margin_ratio >= 1.0 else "#DC2626"
    margin_bg = "#F0FDF4" if margin_ratio >= 1.0 else "#FEF2F2"
    
    st.markdown(f"""
    <div style="background-color: {margin_bg} !important; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid {margin_color} !important; margin-top: 15px;">
        <span style="color: #334155 !important; font-size: 15px; font-weight: 600;">종합 공정 안전 마진 배수: </span>
        <strong style="color: {margin_color} !important; font-size: 22px;">{margin_ratio:.2f} 배</strong>
        <h3 style="color: {margin_color} !important; margin: 5px 0 0 0; font-size: 22px;">{margin_status}</h3>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📈 속도 - 조사 선량 반비례 곡선 시각화")
    
    speeds = np.linspace(0.05, 2.0, 100)
    doses = [i_peak * (y_tunnel / (s * 1000)) * t_shadow * t_lotion * t_aging for s in speeds]
    
    fig, ax = plt.subplots(figsize=(6, 4.3))
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F8FAFC')
    
    ax.plot(speeds, doses, color='#1D4ED8', label='이송 속도별 조사 선량', linewidth=2.5)
    ax.scatter([v_speed], [dose], color='#16A34A', s=140, zorder=5, label='현재 운전 동작점')
    
    ax.axhline(y=17.0, color='#DC2626', linestyle='--', alpha=0.8, label='메틸로박테리움 사멸선 (17.0 mJ/cm²)')
    ax.axhline(y=10.5, color='#D97706', linestyle='--', alpha=0.7, label='아세토박터 사멸선 (10.5 mJ/cm²)')
    ax.axhline(y=7.4, color='#2563EB', linestyle='--', alpha=0.7, label='버크홀데리아 사멸선 (7.4 mJ/cm²)')
    
    ax.set_xlabel('원단 이송 속도 (m/s)', color='#0F172A', fontsize=10, fontweight='bold')
    ax.set_ylabel('자외선 유효 조사량 (mJ/cm²)', color='#0F172A', fontsize=10, fontweight='bold')
    ax.set_title('실시간 운전점 추적 그래프', color='#0F172A', fontsize=12, fontweight='bold')
    
    ax.tick_params(colors='#334155')
    ax.legend(facecolor='#FFFFFF', edgecolor='#CBD5E1', labelcolor='#0F172A', loc='upper right', fontsize=8)
    ax.grid(True, color='#E2E8F0', linestyle=':', alpha=0.8)
    ax.set_ylim(0, max(100, dose * 1.5))
    
    st.pyplot(fig)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px;'>본 프로그램은 한울생약 연구소의 자외선 살균 수립 보고서와 동일한 물리적 연산 수식으로 작동합니다. | Source: FDA 21 CFR & EPA FIFRA</p>", unsafe_allow_html=True)
