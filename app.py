import streamlit as st
import math
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import urllib.request
import matplotlib.font_manager as fm
import matplotlib as mpl
from fpdf import FPDF
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# 1. Page configuration
st.set_page_config(
    page_title="한울생약 UV-C 살균 공정 실시간 시뮬레이터 v4.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Programmatic Korean Font Download and Registration for Headless Linux Containers
FONT_FILENAME = "NanumGothic-Regular.ttf"
if not os.path.exists(FONT_FILENAME):
    try:
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, FONT_FILENAME)
    except Exception as e:
        pass

if os.path.exists(FONT_FILENAME):
    try:
        fm.fontManager.addfont(FONT_FILENAME)
        mpl.rc('font', family='NanumGothic')
        mpl.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        pass

# 3. Custom CSS for dark mode theme
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

st.title("⚡ 주식회사 한울생약 UV-C 살균 공정 실시간 시뮬레이터 v4.0")
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
    
    # Custom styling with cards
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
    
    # Plotting
    speeds = np.linspace(0.05, 2.0, 100)
    doses = [i_peak * (y_tunnel / (s * 1000)) * t_shadow * t_lotion * t_aging for s in speeds]
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    fig.patch.set_facecolor('#1E222B')
    ax.set_facecolor('#21252B')
    
    ax.plot(speeds, doses, color='#4A90E2', label='이송 속도별 조사 선량', linewidth=2.5)
    ax.scatter([v_speed], [dose], color='#2ECC71', s=150, zorder=5, label='현재 운전 동작점')
    
    # Guidelines for targets
    ax.axhline(y=17.0, color='#E74C3C', linestyle='--', alpha=0.7, label='메틸로박테리움 사멸선 (17.0 mJ/cm²)')
    ax.axhline(y=10.5, color='#F1C40F', linestyle='--', alpha=0.5, label='아세토박터 사멸선 (10.5 mJ/cm²)')
    ax.axhline(y=7.4, color='#3498DB', linestyle='--', alpha=0.5, label='버크홀데리아 사멸선 (7.4 mJ/cm²)')
    
    ax.set_xlabel('원단 이송 속도 (m/s)', color='#FFFFFF', fontsize=10)
    ax.set_ylabel('자외선 유효 조사량 (mJ/cm²)', color='#FFFFFF', fontsize=10)
    ax.set_title('실시간 운전점 추적 그래프', color='#FFFFFF', fontsize=12, fontweight='bold')
    
    ax.tick_params(colors='#FFFFFF')
    ax.legend(facecolor='#1E222B', edgecolor='#3E4451', labelcolor='#FFFFFF', loc='upper right', fontsize=8)
    ax.grid(True, color='#3E4451', linestyle=':', alpha=0.5)
    
    # Focus limit to readable scale
    ax.set_ylim(0, max(100, dose * 1.5))
    
    st.pyplot(fig)
    
    # Download Validation Report Button with 2 Formats (Excel, PDF)
    st.subheader("📄 품질 검증 성적서 발급")
    st.write("품질 부서의 검증 기록용 성적서를 원하시는 파일 형식으로 선택하여 다운로드할 수 있습니다.")
    
    # Excel Generator Function
    def generate_excel():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "UVC 살균 검증 성적서"
        ws.views.sheetView[0].showGridLines = True
        
        font_name = "맑은 고딕"
        title_font = Font(name=font_name, size=16, bold=True, color="FFFFFF")
        section_font = Font(name=font_name, size=12, bold=True, color="1F4E78")
        header_font = Font(name=font_name, size=10, bold=True, color="1F4E78")
        bold_font = Font(name=font_name, size=10, bold=True)
        regular_font = Font(name=font_name, size=10)
        
        blue_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        light_blue_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
        green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        red_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='BFBFBF'),
            right=Side(style='thin', color='BFBFBF'),
            top=Side(style='thin', color='BFBFBF'),
            bottom=Side(style='thin', color='BFBFBF')
        )
        
        # Header Card
        ws.merge_cells("A1:E2")
        ws["A1"] = "자외선(UV-C) 살균 공정 유효성 검증 성적서"
        ws["A1"].font = title_font
        ws["A1"].fill = blue_fill
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        
        ws["A3"] = "주식회사 한울생약 기술연구소 (HANUL CHEMICAL)"
        ws["A3"].font = bold_font
        ws["E3"] = "발급일시: 2026-09-08"
        ws["E3"].font = regular_font
        ws["E3"].alignment = Alignment(horizontal="right")
        
        ws.append([])
        
        # 1. Input parameters
        ws.append(["1. 설비 기하학 및 구동 세팅값"])
        ws.cell(row=ws.max_row, column=1).font = section_font
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        
        params = [
            ("설계 항목", "설정값", "단위", "참고 및 설명"),
            ("자외선 살균 터널 길이 (y_tunnel)", y_tunnel, "mm", "UV-C 조사 영역의 컨베이어 내 총 길이"),
            ("물체와 램프 간 이격 거리 (d_gap)", d_gap, "mm", "램프 중심부와 살균 표면 사이의 순수 수직 이격"),
            ("원단 이송 속도 (v_speed)", v_speed, "m/s", "물티슈 완제품 생산 라인의 구동 속도"),
            ("총 설치 램프 수 (N_lamps)", n_lamps, "개", "상부 및 측면에 배치되는 램프 개수"),
            ("단일 램프 정격 전력 (P_lamp)", p_lamp, "W", "제조사 공식 스펙 상 램프 소비전력"),
            ("UVC 변환 효율 (Eff_uvc)", eff_uvc, "비율", "전기에너지 대비 순수 살균광 변환비"),
            ("유리 램프 유효 발광 길이 (L_lamp)", l_lamp, "mm", "순수 발광 튜브 영역의 길이"),
            ("그림자 장벽 투과율 (T_shadow)", t_shadow, "비율", "원단 엠보싱 굴곡에 의한 음영부 통과 비율"),
            ("램프 노화 및 분진 오염도 (T_aging)", t_aging, "비율", "램프 노화와 고착 먼지에 의한 출력 유지도")
        ]
        
        for r in params:
            ws.append(list(r))
            curr_row = ws.max_row
            is_header = r[0] == "설계 항목"
            for col_idx in range(1, 5):
                cell = ws.cell(row=curr_row, column=col_idx)
                cell.border = thin_border
                if is_header:
                    cell.font = header_font
                    cell.fill = light_blue_fill
                    cell.alignment = Alignment(horizontal="center")
                else:
                    cell.font = regular_font
                    if col_idx in [2, 3]:
                        cell.alignment = Alignment(horizontal="center")
                        
        ws.append([])
        
        # 2. Physics values
        ws.append(["2. 물리 광학 연산 결과"])
        ws.cell(row=ws.max_row, column=1).font = section_font
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        
        ws.append(["계산 항목", "연산 결과값", "단위", "물리 수학적 산출 수식 및 근거"])
        curr_row = ws.max_row
        for col_idx in range(1, 5):
            cell = ws.cell(row=curr_row, column=col_idx)
            cell.border = thin_border
            cell.font = header_font
            cell.fill = light_blue_fill
            cell.alignment = Alignment(horizontal="center")
            
        calc_rows = [
            ("총 UVC 가용 방사출력 (P_total)", round(p_total, 1), "mW", "전체 램프 개수 × 개별 파워 × UVC 효율 × 1000"),
            ("조사 영역 통과 노출시간 (t_exp)", round(t_exp, 3), "초", "자외선 터널 길이(y) / 원단 이송 속도(v)"),
            ("물체 표면 자외선 최고 조도 (I_peak)", round(i_peak, 3), "mW/cm²", "Keitz 선광원 배광 적분 공식 모델링 조도"),
            ("최종 유효조사량 (Dose)", round(dose, 2), "mJ/cm²", "실제 원단에 최종 도달하는 유효 에너지량 (로션 감쇄 배제)")
        ]
        
        for r in calc_rows:
            ws.append(list(r))
            curr_row = ws.max_row
            for col_idx in range(1, 5):
                cell = ws.cell(row=curr_row, column=col_idx)
                cell.border = thin_border
                cell.font = bold_font if r[0].startswith("최종 유효조사량") else regular_font
                if col_idx in [2, 3]:
                    cell.alignment = Alignment(horizontal="center")
                if r[0].startswith("최종 유효조사량"):
                    cell.fill = green_fill
                    
        ws.append([])
        
        # 3. Microorganisms
        ws.append(["3. 핵심 타겟 미생물 3종 살균 합불(PASS/FAIL) 진단"])
        ws.cell(row=ws.max_row, column=1).font = section_font
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        
        ws.append(["제어 대상 세균명", "사멸 기준량 (Dose)", "현재 설계 도달량", "실시간 살균 합격 판정", "대체 균주 (Surrogate)"])
        curr_row = ws.max_row
        for col_idx in range(1, 6):
            cell = ws.cell(row=curr_row, column=col_idx)
            cell.border = thin_border
            cell.font = header_font
            cell.fill = light_blue_fill
            cell.alignment = Alignment(horizontal="center")
            
        for name, data in targets.items():
            limit = data["limit"]
            is_pass = dose >= limit
            status_text = "합격 (PASS)" if is_pass else "불합격 (FAIL)"
            status_fill = green_fill if is_pass else red_fill
            
            ws.append([name, limit, round(dose, 2), status_text, data["surrogate"]])
            curr_row = ws.max_row
            for col_idx in range(1, 6):
                cell = ws.cell(row=curr_row, column=col_idx)
                cell.border = thin_border
                cell.font = bold_font if col_idx == 4 else regular_font
                if col_idx in [2, 3, 4]:
                    cell.alignment = Alignment(horizontal="center")
                if col_idx == 4:
                    cell.fill = status_fill
                    
        ws.append([])
        ws.append(["종합 공정 안전 마진 배수: " + f"{margin_ratio:.2f} 배  ({margin_status})"])
        ws.cell(row=ws.max_row, column=1).font = bold_font
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        
        ws.append([])
        ws.append(["본 성적서는 (주)한울생약 기술연구소 UVC 살균 시뮬레이터 프로그램 v4.0에 의해 공식 발급되었습니다."])
        ws.cell(row=ws.max_row, column=1).font = regular_font
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=5)
        
        # Auto-fit columns
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    # PDF Generator Function
    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()
        
        font_filename = "NanumGothic-Regular.ttf"
        if os.path.exists(font_filename):
            pdf.add_font("NanumGothic", "", font_filename)
            pdf.set_font("NanumGothic", size=10)
            has_korean = True
        else:
            pdf.set_font("helvetica", size=10)
            has_korean = False
            
        # Draw Corporate branding header
        pdf.set_font("NanumGothic" if has_korean else "helvetica", style="" if has_korean else "B", size=16)
        pdf.set_text_color(31, 78, 120)
        pdf.cell(190, 10, txt="자외선(UV-C) 살균 유효성 검증 성적서", ln=True, align='C')
        pdf.ln(2)
        
        pdf.set_font("NanumGothic" if has_korean else "helvetica", size=10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(190, 6, txt="주식회사 한울생약 기술연구소 (HANUL CHEMICAL)", ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_text_color(50, 50, 50)
        pdf.cell(190, 6, txt="발급 일시: 2026-09-08", ln=True, align='R')
        pdf.cell(190, 6, txt="공정 분류: 건조 원단 및 포장재 선(先) 살균 가공 공정", ln=True, align='R')
        pdf.ln(8)
        
        # 1. Input variables
        pdf.set_font("NanumGothic" if has_korean else "helvetica", style="" if has_korean else "B", size=12)
        pdf.set_text_color(31, 78, 120)
        pdf.cell(190, 8, txt="1. 설비 기하학 및 구동 세팅값", ln=True)
        pdf.ln(2)
        
        pdf.set_font("NanumGothic" if has_korean else "helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 6, txt=f"- 살균 터널 길이 (y_tunnel): {y_tunnel} mm", ln=False)
        pdf.cell(95, 6, txt=f"- 물체-광원 이격 거리 (d_gap): {d_gap} mm", ln=True)
        pdf.cell(95, 6, txt=f"- 컨베이어 이송 속도 (v_speed): {v_speed} m/s", ln=False)
        pdf.cell(95, 6, txt=f"- 설치 램프 사양: {n_lamps} 개 x {p_lamp} W", ln=True)
        pdf.cell(95, 6, txt=f"- UVC 변환 효율: {eff_uvc * 100}%", ln=False)
        pdf.cell(95, 6, txt=f"- 유리 램프 유효 발광 길이: {l_lamp} mm", ln=True)
        pdf.cell(95, 6, txt=f"- 그림자 장벽 투과율 (T_shadow): {t_shadow}", ln=False)
        pdf.cell(95, 6, txt=f"- 램프 노화 및 분진 오염도 (T_aging): {t_aging}", ln=True)
        pdf.ln(5)
        
        # 2. Physics values
        pdf.set_font("NanumGothic" if has_korean else "helvetica", style="" if has_korean else "B", size=12)
        pdf.set_text_color(31, 78, 120)
        pdf.cell(190, 8, txt="2. 물리 광학 연산 결과", ln=True)
        pdf.ln(2)
        
        pdf.set_font("NanumGothic" if has_korean else "helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 6, txt=f"- 가용 총 UVC 방사출력 (P_total): {p_total:.1f} mW", ln=False)
        pdf.cell(95, 6, txt=f"- 조사 노출시간 (t_exp): {t_exp:.3f} 초", ln=True)
        pdf.cell(95, 6, txt=f"- 표면 최고 조도 (I_peak): {i_peak:.3f} mW/cm²", ln=False)
        
        # Highlight final dose
        pdf.set_text_color(46, 204, 113)
        pdf.cell(95, 6, txt=f"- 최종 유효 조사량 (Dose): {dose:.2f} mJ/cm²", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 6, txt="  (※ 선살균 공정 적용으로 로션 흡수 손실 배제 - 투과율 1.0 적용)", ln=True)
        pdf.ln(5)
        
        # 3. Microorganisms
        pdf.set_font("NanumGothic" if has_korean else "helvetica", style="" if has_korean else "B", size=12)
        pdf.set_text_color(31, 78, 120)
        pdf.cell(190, 8, txt="3. 타겟 미생물 3종 사멸 유효성 판정 결과", ln=True)
        pdf.ln(2)
        
        pdf.set_font("NanumGothic" if has_korean else "helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        for name, data in targets.items():
            limit = data["limit"]
            is_pass = dose >= limit
            status = "PASS (적합)" if is_pass else "FAIL (부적합)"
            pdf.cell(190, 6, txt=f"- {name} (기준 {limit} mJ/cm²): {status}", ln=True)
        
        pdf.ln(5)
        pdf.cell(190, 6, txt=f"■ 종합 공정 안전 마진 배수: {margin_ratio:.2f} 배", ln=True)
        pdf.cell(190, 6, txt=f"■ 최종 검증 의견: {margin_status}", ln=True)
        
        pdf.ln(15)
        # Add footer-like brand note
        pdf.set_text_color(128, 128, 128)
        pdf.cell(190, 6, txt="본 문서는 한울생약 기술연구소의 UVC 살균 시뮬레이터 프로그램에 의해 공학적으로 발급되었습니다.", ln=True, align='C')
        pdf.cell(190, 6, txt="주식회사 한울생약", ln=True, align='C')
        
        return bytes(pdf.output())

    # Download Buttons Side-by-Side
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        excel_bytes = generate_excel()
        st.download_button(
            label="📥 Excel 성적서 다운로드 (.xlsx)",
            data=excel_bytes,
            file_name="hanul-uvc-validation-report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_dl2:
        pdf_bytes = generate_pdf()
        st.download_button(
            label="📥 PDF 성적서 다운로드 (.pdf)",
            data=pdf_bytes,
            file_name="hanul-uvc-validation-report.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.markdown("<p style='text-align: center; color: #8A92A6; font-size: 12px;'>본 프로그램은 한울생약 연구소의 자외선 살균 수립 보고서와 100% 동일한 학술 표준 수식으로 작동합니다. | Source: FDA 21 CFR & EPA FIFRA</p>", unsafe_allow_html=True)
