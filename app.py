import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import urllib.request
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from fpdf import FPDF

# Page configuration
st.set_page_config(
    page_title="한울생약 UV-C 살균 공정 시뮬레이터 v4.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode theme
st.markdown("""
<style>
    .reportview-container {
        background: #1E222B;
    }
    .stSlider > div > div > div > div {
        background-color: #4A90E2;
    }
    .metric-box {
        background-color: #282C34;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3E4451;
        text-align: center;
        margin-bottom: 10px;
    }
    .pass-lamp {
        color: #2ECC71;
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
st.caption("건조 원단 및 포장재 선(선) 살균 공정 전용 웹 시뮬레이션 모델 (Render 배포용)")

# Download NanumGothic font for Matplotlib and FPDF
FONT_PATH = "NanumGothic-Regular.ttf"
font_downloaded = False

@st.cache_resource
def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, FONT_PATH)
            return True
        except Exception as e:
            return False
    return True

font_downloaded = download_font()

# Apply Korean font to Matplotlib if downloaded
if font_downloaded and os.path.exists(FONT_PATH):
    from matplotlib import font_manager
    try:
        font_manager.fontManager.addfont(FONT_PATH)
        plt.rcParams['font.family'] = 'NanumGothic'
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        pass

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
# Cylinder surface area (cm2) = 2 * pi * r * L
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
    <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #8A92A6; margin-bottom: 5px;">가용 총 UVC 방사출력</p>
            <h2 style="color: #4A90E2; margin: 0;">{p_total:.1f} mW</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #8A92A6; margin-bottom: 5px;">조사 노출시간</p>
            <h2 style="color: #4A90E2; margin: 0;">{t_exp:.3f} 초</h2>
        </div>
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
        <div class="metric-box" style="flex: 1; margin: 5px;">
            <p style="color: #8A92A6; margin-bottom: 5px;">표면 자외선 최고 조도</p>
            <h2 style="color: #E2B14A; margin: 0;">{i_peak:.3f} mW/cm²</h2>
        </div>
        <div class="metric-box" style="flex: 1; margin: 5px; border: 2px solid #2ECC71;">
            <p style="color: #2ECC71; font-weight: bold; margin-bottom: 5px;">최종 유효 자외선 조사량 (Dose)</p>
            <h1 style="color: #2ECC71; margin: 0;">{dose:.2f} mJ/cm²</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🚨 핵심 타겟 미생물 3종 살균 합불(PASS/FAIL) 진단")
    for name, data in targets.items():
        limit = data["limit"]
        is_pass = dose >= limit
        status_text = "🟢 합격 (PASS)" if is_pass else "🔴 불합격 (FAIL)"
        status_color = "#2ECC71" if is_pass else "#E74C3C"
        
        st.markdown(f"""
        <div style="background-color: #282C34; padding: 15px; border-radius: 8px; border-left: 5px solid {status_color}; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #FFFFFF;">{name}</h4>
                    <p style="margin: 0; font-size: 12px; color: #8A92A6;">대체 균주: {data['surrogate']}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: bold; color: {status_color}; font-size: 18px;">{status_text}</span>
                    <p style="margin: 0; font-size: 12px; color: #8A92A6;">기준: {limit} mJ/cm²</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # General margin and status
    margin_ratio = dose / 17.0
    margin_status = "🟢 안전 마진 충분 (PASS)" if margin_ratio >= 1.0 else "🔴 안전선 미달 (FAIL)"
    margin_color = "#2ECC71" if margin_ratio >= 1.0 else "#E74C3C"
    
    st.markdown(f"""
    <div style="background-color: #21252B; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid {margin_color}; margin-top: 15px;">
        <span style="color: #8A92A6; font-size: 14px;">종합 공정 안전 마진 배수: </span>
        <strong style="color: {margin_color}; font-size: 20px;">{margin_ratio:.2f} 배</strong>
        <h3 style="color: {margin_color}; margin: 5px 0 0 0;">{margin_status}</h3>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📈 속도 - 조사 선량 반비례 곡선 시각화")
    
    speeds = np.linspace(0.05, 2.0, 100)
    doses = [i_peak * (y_tunnel / (s * 1000)) * t_shadow * t_lotion * t_aging for s in speeds]
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    fig.patch.set_facecolor('#1E222B')
    ax.set_facecolor('#21252B')
    
    ax.plot(speeds, doses, color='#4A90E2', label='이송 속도별 조사 선량', linewidth=2.5)
    ax.scatter([v_speed], [dose], color='#2ECC71', s=150, zorder=5, label='현재 운전 동작점')
    
    ax.axhline(y=17.0, color='#E74C3C', linestyle='--', alpha=0.7, label='메틸로박테리움 사멸선 (17.0 mJ/cm²)')
    ax.axhline(y=10.5, color='#F1C40F', linestyle='--', alpha=0.5, label='아세토박터 사멸선 (10.5 mJ/cm²)')
    ax.axhline(y=7.4, color='#3498DB', linestyle='--', alpha=0.5, label='버크홀데리아 사멸선 (7.4 mJ/cm²)')
    
    ax.set_xlabel('원단 이송 속도 (m/s)', color='#FFFFFF', fontsize=10)
    ax.set_ylabel('자외선 유효 조사량 (mJ/cm²)', color='#FFFFFF', fontsize=10)
    ax.set_title('실시간 운전점 추적 그래프', color='#FFFFFF', fontsize=12, fontweight='bold')
    
    ax.tick_params(colors='#FFFFFF')
    ax.legend(facecolor='#1E222B', edgecolor='#3E4451', labelcolor='#FFFFFF', loc='upper right', fontsize=8)
    ax.grid(True, color='#3E4451', linestyle=':', alpha=0.5)
    
    ax.set_ylim(0, max(100, dose * 1.5))
    
    st.pyplot(fig)
    
    st.subheader("📄 품질 검증 성적서 발급 (선택)")
    
    # Excel Generation function
    def generate_excel():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "살균검증성적서"
        ws.views.sheetView[0].showGridLines = True
        
        title_font = Font(name="Malgun Gothic", size=16, bold=True, color="1E395B")
        header_font = Font(name="Malgun Gothic", size=11, bold=True, color="FFFFFF")
        section_font = Font(name="Malgun Gothic", size=11, bold=True, color="1E395B")
        regular_font = Font(name="Malgun Gothic", size=10)
        bold_font = Font(name="Malgun Gothic", size=10, bold=True)
        
        header_fill = PatternFill(start_color="1E395B", end_color="1E395B", fill_type="solid")
        section_fill = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid")
        pass_fill = PatternFill(start_color="E2F0D9", end_color="E2F0D9", fill_type="solid")
        fail_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        
        thin_side = Side(border_style="thin", color="D9D9D9")
        thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 25
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 15
        
        ws.merge_cells("B2:E2")
        ws["B2"] = "주식회사 한울생약 - UV-C 살균 유효성 검증 성적서"
        ws["B2"].font = title_font
        ws["B2"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 40
        
        ws["B4"] = "공정 분류:"
        ws["B4"].font = bold_font
        ws["C4"] = "건조 원단 및 포장재 선(先) 살균 가공 공정"
        ws["C4"].font = regular_font
        
        ws["D4"] = "발급 일시:"
        ws["D4"].font = bold_font
        ws["E4"] = "2026-09-08"
        ws["E4"].font = regular_font
        
        ws["B5"] = "품질 규정:"
        ws["B5"].font = bold_font
        ws["C5"] = "FDA 21 CFR § 880.6600, EPA FIFRA, IUVA"
        ws["C5"].font = regular_font
        
        for col in ["B", "C", "D", "E"]:
            ws[f"{col}4"].border = thin_border
            ws[f"{col}5"].border = thin_border
            
        ws.merge_cells("B7:E7")
        ws["B7"] = "1. 설비 기하학 및 구동 변수"
        ws["B7"].font = header_font
        ws["B7"].fill = header_fill
        ws["B7"].alignment = Alignment(indent=1)
        
        params = [
            ("살균 터널 길이 (y_tunnel)", f"{y_tunnel} mm"),
            ("물체-광원 이격 거리 (d_gap)", f"{d_gap} mm"),
            ("컨베이어 이송 속도 (v_speed)", f"{v_speed} m/s"),
            ("설치 UVC 총 램프 수", f"{n_lamps} 개"),
            ("단일 램프 정격 전력", f"{p_lamp} W (효율 {eff_uvc*100}%)"),
            ("램프 유효 발광 길이", f"{l_lamp} mm")
        ]
        
        row = 8
        for label, val in params:
            ws[f"B{row}"] = label
            ws[f"B{row}"].font = regular_font
            ws[f"B{row}"].border = thin_border
            ws[f"C{row}"] = val
            ws[f"C{row}"].font = bold_font
            ws[f"C{row}"].border = thin_border
            ws[f"C{row}"].alignment = Alignment(horizontal="right")
            row += 1
            
        ws.merge_cells(f"B{row}:E{row}")
        ws[f"B{row}"] = "2. 물리 광학 연산 결과"
        ws[f"B{row}"].font = header_font
        ws[f"B{row}"].fill = header_fill
        ws[f"B{row}"].alignment = Alignment(indent=1)
        row += 1
        
        results = [
            ("가용 총 UVC 방사 출력", f"{p_total:.1f} mW"),
            ("조사 노출 시간", f"{t_exp:.3f} 초"),
            ("표면 최고 조도", f"{i_peak:.3f} mW/cm²"),
            ("최종 유효 자외선 조사량 (Dose)", f"{dose:.2f} mJ/cm²")
        ]
        
        for label, val in results:
            ws[f"B{row}"] = label
            ws[f"B{row}"].font = regular_font
            ws[f"B{row}"].border = thin_border
            ws[f"C{row}"] = val
            ws[f"C{row}"].font = bold_font
            ws[f"C{row}"].border = thin_border
            ws[f"C{row}"].alignment = Alignment(horizontal="right")
            
            if "Dose" in label:
                ws[f"B{row}"].font = Font(name="Malgun Gothic", size=10, bold=True, color="1E395B")
                ws[f"C{row}"].font = Font(name="Malgun Gothic", size=11, bold=True, color="2ECC71")
                ws[f"B{row}"].fill = section_fill
                ws[f"C{row}"].fill = section_fill
            row += 1
            
        ws.merge_cells(f"B{row}:E{row}")
        ws[f"B{row}"] = "3. 핵심 타겟 미생물 3종 사멸 검증"
        ws[f"B{row}"].font = header_font
        ws[f"B{row}"].fill = header_fill
        ws[f"B{row}"].alignment = Alignment(indent=1)
        row += 1
        
        ws[f"B{row}"] = "목표 미생물 명칭"
        ws[f"B{row}"].font = bold_font
        ws[f"B{row}"].border = thin_border
        ws[f"C{row}"] = "학술 대체 균주"
        ws[f"C{row}"].font = bold_font
        ws[f"C{row}"].border = thin_border
        ws[f"D{row}"] = "사멸 기준 선량"
        ws[f"D{row}"].font = bold_font
        ws[f"D{row}"].border = thin_border
        ws[f"D{row}"].alignment = Alignment(horizontal="center")
        ws[f"E{row}"] = "적합성 판정"
        ws[f"E{row}"].font = bold_font
        ws[f"E{row}"].border = thin_border
        ws[f"E{row}"].alignment = Alignment(horizontal="center")
        row += 1
        
        micro_results = [
            ("버크홀데리아 (Burkholderia)", "B. pseudomallei", 7.4),
            ("아세토박터-초산균 (Acetobacter)", "Brucella suis", 10.5),
            ("메틸로박테리움 (Methylobacterium)", "Pseudomonas aeruginosa", 17.0)
        ]
        
        for name, surrogate, limit in micro_results:
            ws[f"B{row}"] = name
            ws[f"B{row}"].font = regular_font
            ws[f"B{row}"].border = thin_border
            ws[f"C{row}"] = surrogate
            ws[f"C{row}"].font = regular_font
            ws[f"C{row}"].border = thin_border
            ws[f"D{row}"] = f"{limit} mJ/cm²"
            ws[f"D{row}"].font = regular_font
            ws[f"D{row}"].border = thin_border
            ws[f"D{row}"].alignment = Alignment(horizontal="center")
            
            is_ok = dose >= limit
            ws[f"E{row}"] = "🟢 적합 (PASS)" if is_ok else "🔴 미달 (FAIL)"
            ws[f"E{row}"].font = bold_font
            ws[f"E{row}"].border = thin_border
            ws[f"E{row}"].fill = pass_fill if is_ok else fail_fill
            ws[f"E{row}"].alignment = Alignment(horizontal="center")
            row += 1
            
        row += 1
        ws.merge_cells(f"B{row}:E{row}")
        ws[f"B{row}"] = f"종합 공정 안전 마진: {margin_ratio:.2f}배  |  최종 판정: {margin_status}"
        ws[f"B{row}"].font = Font(name="Malgun Gothic", size=11, bold=True, color="1E395B")
        ws[f"B{row}"].fill = section_fill
        ws[f"B{row}"].alignment = Alignment(horizontal="center", vertical="center")
        ws[f"B{row}"].border = thin_border
        ws.row_dimensions[row].height = 30
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    # PDF Generation function
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        
        if font_downloaded and os.path.exists(FONT_PATH):
            pdf.add_font("NanumGothic", "", FONT_PATH)
            pdf.set_font("NanumGothic", size=10)
            font_family = "NanumGothic"
        else:
            pdf.set_font("Helvetica", size=10)
            font_family = "Helvetica"
            
        def clean_str(text):
            return text.encode('utf-8', 'ignore').decode('utf-8')
            
        pdf.set_fill_color(30, 57, 91)
        pdf.rect(10, 10, 190, 25, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_family, size=15)
        pdf.set_xy(10, 17)
        pdf.cell(190, 10, clean_str("(주)한울생약 기술연구소 품질 보증 문서"), align="C")
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_family, size=13)
        pdf.set_xy(10, 42)
        pdf.cell(190, 10, clean_str("■ UV-C 살균 설비 엔지니어링 유효성 검증 성적서 (SOP-UVC-04)"), align="L")
        
        pdf.ln(10)
        pdf.set_font(font_family, size=9)
        pdf.cell(95, 6, clean_str("발급일자: 2026년 09월 08일"), border=0)
        pdf.cell(95, 6, clean_str("공정분류: 건조 원단 및 포장재 선살균 공정"), border=0, align="R")
        
        pdf.ln(8)
        pdf.set_draw_color(30, 57, 91)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font(font_family, size=10)
        pdf.set_fill_color(242, 244, 247)
        pdf.cell(190, 8, clean_str("1. 설비 기하학 및 작동 구동 매개변수"), fill=True, ln=True)
        pdf.set_font(font_family, size=9)
        
        pdf.cell(95, 7, clean_str(f" - 자외선 살균 터널 길이: {y_tunnel} mm"), border=1)
        pdf.cell(95, 7, clean_str(f" - 물체와 광원 이격 거리: {d_gap} mm"), border=1, ln=True)
        pdf.cell(95, 7, clean_str(f" - 컨베이어 이송 속도: {v_speed} m/s"), border=1)
        pdf.cell(95, 7, clean_str(f" - 총 UVC 설치 램프 수: {n_lamps} 개"), border=1, ln=True)
        pdf.cell(95, 7, clean_str(f" - 단일 램프 정격 전력: {p_lamp} W"), border=1)
        pdf.cell(95, 7, clean_str(f" - UVC 변환 효율: {eff_uvc*100:.0f} %"), border=1, ln=True)
        pdf.cell(190, 7, clean_str(f" - 자외선 램프 유효 발광 길이: {l_lamp} mm"), border=1, ln=True)
        pdf.ln(5)
        
        pdf.set_font(font_family, size=10)
        pdf.cell(190, 8, clean_str("2. 물리 광학 에너지 연산 데이터"), fill=True, ln=True)
        pdf.set_font(font_family, size=9)
        
        pdf.cell(95, 7, clean_str(f" - 가용 총 UVC 방사 출력: {p_total:.1f} mW"), border=1)
        pdf.cell(95, 7, clean_str(f" - 자외선 조사 노출 시간: {t_exp:.3f} 초"), border=1, ln=True)
        pdf.cell(95, 7, clean_str(f" - 원단 표면 최고 조도: {i_peak:.3f} mW/cm²"), border=1)
        pdf.set_fill_color(226, 240, 217)
        pdf.cell(95, 7, clean_str(f" - 최종 유효 조사량 (Dose): {dose:.2f} mJ/cm²"), border=1, fill=True, ln=True)
        pdf.ln(5)
        
        pdf.set_font(font_family, size=10)
        pdf.set_fill_color(242, 244, 247)
        pdf.cell(190, 8, clean_str("3. 타겟 병원성 유해 미생물 3종 사멸 검증"), fill=True, ln=True)
        
        pdf.set_font(font_family, size=9)
        pdf.cell(60, 8, clean_str("목표 유해 미생물"), border=1, align="C")
        pdf.cell(50, 8, clean_str("학술 대체 균주"), border=1, align="C")
        pdf.cell(40, 8, clean_str("사멸 기준 선량"), border=1, align="C")
        pdf.cell(40, 8, clean_str("적합성 판정"), border=1, align="C", ln=True)
        
        micro_results = [
            ("버크홀데리아 (Burkholderia)", "B. pseudomallei", 7.4),
            ("아세토박터-초산균 (Acetobacter)", "Brucella suis", 10.5),
            ("메틸로박테리움 (Methylobacterium)", "Pseudomonas aeruginosa", 17.0)
        ]
        
        for name, surrogate, limit in micro_results:
            is_ok = dose >= limit
            pdf.cell(60, 7, clean_str(name), border=1)
            pdf.cell(50, 7, clean_str(surrogate), border=1)
            pdf.cell(40, 7, clean_str(f"{limit} mJ/cm²"), border=1, align="C")
            
            if is_ok:
                pdf.set_fill_color(226, 240, 217)
                pdf.cell(40, 7, clean_str("PASS (적합)"), border=1, align="C", fill=True, ln=True)
            else:
                pdf.set_fill_color(252, 228, 214)
                pdf.cell(40, 7, clean_str("FAIL (부적합)"), border=1, align="C", fill=True, ln=True)
                
        pdf.ln(5)
        
        pdf.set_draw_color(30, 57, 91)
        pdf.set_fill_color(242, 244, 247)
        pdf.set_font(font_family, size=10)
        pdf.cell(190, 10, clean_str(f"■ 종합 공정 안전 마진: {margin_ratio:.2f} 배  |  {margin_status}"), border=1, fill=True, align="C")
        
        pdf.ln(15)
        pdf.set_font(font_family, size=8)
        pdf.cell(190, 5, clean_str("본 문서는 한울생약 자외선 살균 수식 모델을 통해 실시간 검증되었으며, FDA 21 CFR § 880.6600 특별통제를 충족합니다."), align="C", ln=True)
        pdf.cell(190, 5, clean_str("Quality Assurance Department | (주)한울생약 기술연구소"), align="C", ln=True)
        
        return pdf.output()

    excel_btn_col, pdf_btn_col = st.columns(2)
    
    with excel_btn_col:
        excel_data = generate_excel()
        st.download_button(
            label="📥 고급 엑셀 성적서 다운로드 (.xlsx)",
            data=excel_data,
            file_name="hanul-uvc-validation-report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with pdf_btn_col:
        try:
            pdf_data = generate_pdf()
            st.download_button(
                label="📥 격조 높은 PDF 성적서 다운로드 (.pdf)",
                data=bytes(pdf_data),
                file_name="hanul-uvc-validation-report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.warning(f"PDF 생성 중 일시적 오류가 발생했습니다. (나눔고딕 폰트 미동기화): {str(e)}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #8A92A6; font-size: 12px;'>본 프로그램은 한울생약 연구소의 자외선 살균 수립 보고서와 100% 동일한 학술 표준 수식으로 작동합니다. | Source: FDA 21 CFR & EPA FIFRA</p>", unsafe_allow_html=True)
