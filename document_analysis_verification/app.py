"""Streamlit application for intelligent document analysis and verification."""

from datetime import datetime
from pathlib import Path

import cv2
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.document_upload import (
    get_file_info,
    load_document_preview,
    validate_uploaded_file,
)
from modules.image_preprocessing import preprocess_document
from modules.ocr_extraction import extract_text_from_image, extract_text_from_pdf
from modules.information_extraction import extract_structured_information
from modules.document_analysis import analyze_document
from modules.document_verification import verify_document
from modules.report_generation import (
    generate_csv_report,
    generate_pdf_report,
    generate_txt_report,
)


st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
html, body, [class*="css"] {font-family: 'Inter', 'Segoe UI', sans-serif !important;}
.stApp {background: #0B1220; color: #F1F5F9;}
section[data-testid="stSidebar"] {background: #111C2E; border-right: 1px solid #2B3B50; min-width: 268px;}
section[data-testid="stSidebar"] * {color: #F1F5F9;}
section[data-testid="stSidebar"] .stRadio label {padding: 9px 11px; border-radius: 8px; margin: 2px 0;}
section[data-testid="stSidebar"] .stRadio label:hover {background: #172438;}
section[data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] {background: rgba(32,197,181,.14); border: 1px solid rgba(32,197,181,.35);}
.block-container {max-width: 1420px; padding: 1.7rem 2.1rem 3rem 2.1rem;}
.main-header {font-size: 2.05rem; line-height: 1.15; font-weight: 780; color: #F1F5F9; margin: 0; letter-spacing: -.025em;}
.sub-header {color: #A7B4C7; margin: .35rem 0 1.35rem 0; font-size: .98rem;}
.top-status {display:flex;gap:10px;align-items:center;color:#A7B4C7;font-size:.86rem;margin-top:.35rem;}
.status-pill {display:inline-flex;align-items:center;gap:7px;border-radius:999px;padding:6px 10px;font-size:.78rem;font-weight:800;letter-spacing:.03em;border:1px solid #2B3B50;background:#172438;color:#F1F5F9;}
.status-valid {border-color:rgba(52,211,153,.45)!important;color:#34D399!important;background:rgba(52,211,153,.10)!important;}
.status-warning {border-color:rgba(251,191,36,.45)!important;color:#FBBF24!important;background:rgba(251,191,36,.10)!important;}
.status-error {border-color:rgba(248,113,113,.45)!important;color:#F87171!important;background:rgba(248,113,113,.10)!important;}
.metric-card {height:118px;background:#172438;border:1px solid #2B3B50;border-radius:14px;padding:18px 18px 14px 18px;box-shadow:0 10px 24px rgba(0,0,0,.10);}
.metric-card-top {display:flex;justify-content:space-between;align-items:center;color:#A7B4C7;font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.055em;}
.metric-icon {width:34px;height:34px;border-radius:9px;display:grid;place-items:center;font-size:16px;}
.metric-number {font-size:2rem;line-height:1;margin-top:13px;font-weight:800;color:#F1F5F9;}
.icon-teal {background:rgba(32,197,181,.13);color:#20C5B5}.icon-blue {background:rgba(96,165,250,.13);color:#60A5FA}.icon-green {background:rgba(52,211,153,.13);color:#34D399}.icon-amber {background:rgba(251,191,36,.13);color:#FBBF24}.icon-red {background:rgba(248,113,113,.13);color:#F87171}
.surface {background:#172438;border:1px solid #2B3B50;border-radius:14px;padding:18px;box-shadow:0 10px 24px rgba(0,0,0,.08);}
.section-title {color:#F1F5F9;font-size:1.12rem;font-weight:750;margin:0 0 12px 0;}
.muted {color:#A7B4C7;font-size:.88rem;}.caption-muted {color:#A7B4C7!important;font-size:.82rem!important;}
[data-testid="stMetric"] {background:#172438;border:1px solid #2B3B50;border-radius:12px;padding:14px;}.stMetric label {color:#A7B4C7!important}.stMetric [data-testid="stMetricValue"] {color:#F1F5F9!important}
div[data-testid="stDataFrame"] {background:#172438;border:1px solid #2B3B50;border-radius:10px;}
.stTextArea textarea {background:#111C2E!important;color:#F1F5F9!important;border:1px solid #2B3B50!important;border-radius:10px!important;}
.stDownloadButton button, .stButton button {background:#20C5B5!important;color:#07131A!important;border:none!important;border-radius:9px!important;font-weight:800!important;padding:.55rem .9rem!important;}
.stDownloadButton button:hover, .stButton button:hover {background:#38D9C8!important;color:#07131A!important;}
[data-testid="stFileUploader"] {background:#172438;border:1px dashed #3A506A;border-radius:12px;padding:12px;}
hr {border-color:#2B3B50!important;}
.badge {display:inline-flex;align-items:center;padding:5px 9px;border-radius:999px;font-size:.76rem;font-weight:800;margin:3px 5px 3px 0;border:1px solid #2B3B50;background:#1D2D43;color:#F1F5F9;}
.badge-warning {color:#FBBF24;border-color:rgba(251,191,36,.38);background:rgba(251,191,36,.09);}.badge-valid {color:#34D399;border-color:rgba(52,211,153,.38);background:rgba(52,211,153,.09);}.badge-error {color:#F87171;border-color:rgba(248,113,113,.38);background:rgba(248,113,113,.09);}
.issue-box {background:#1D2D43;border-left:3px solid #60A5FA;border-radius:8px;padding:10px 12px;margin:6px 0;color:#DCE6F2;}.success-box {background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.25);border-radius:9px;padding:12px;color:#34D399;}.info-box {background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.22);border-radius:9px;padding:12px;color:#C9D7EA;}
.stTabs [data-baseweb="tab-list"] {gap:8px}.stTabs [data-baseweb="tab"] {background:#172438;border:1px solid #2B3B50;border-radius:8px 8px 0 0;padding:8px 14px;}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
  <div style="width:38px;height:38px;border-radius:10px;background:#20C5B5;color:#07131A;display:grid;place-items:center;font-size:20px;font-weight:900;">D</div>
  <div><div style="font-size:1.15rem;font-weight:800;color:#F1F5F9;line-height:1.1;">DocuMind AI</div><div style="font-size:.68rem;color:#A7B4C7;margin-top:4px;">DOCUMENT INTELLIGENCE</div></div>
</div>
""", unsafe_allow_html=True)
st.sidebar.caption("Intelligent Document Analysis and Verification")
st.sidebar.markdown("<div style='height:1px;background:#2B3B50;margin:12px 0 14px 0'></div>", unsafe_allow_html=True)
page = st.sidebar.radio("Workspace", ["Dashboard", "Upload & Analysis", "Verification", "Reports"], label_visibility="collapsed")
st.sidebar.markdown("<div style='height:1px;background:#2B3B50;margin:14px 0'></div>", unsafe_allow_html=True)
st.sidebar.markdown("**Document upload**")

uploaded_file = st.sidebar.file_uploader(
    "Upload document",
    type=["pdf", "jpg", "jpeg", "png"],
    help="Supported formats: PDF, JPG, JPEG, PNG (maximum 25 MB)",
)

if uploaded_file:
    valid, validation_message = validate_uploaded_file(uploaded_file)
else:
    valid, validation_message = False, "No document uploaded."

if uploaded_file and not valid:
    st.error(validation_message)
    st.stop()


def metric_card(icon: str, icon_class: str, label: str, value: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-card-top"><span>{label}</span><span class="metric-icon {icon_class}">{icon}</span></div><div class="metric-number">{value}</div></div>',
        unsafe_allow_html=True,
    )


def status_card(status: str) -> str:
    status_name = status.lower()
    css_class = "status-valid" if status_name == "valid" else "status-warning" if status_name == "warning" else "status-error"
    return f'<div class="status-pill {css_class}" style="display:flex;justify-content:center;width:180px;margin:0 auto 18px auto;">{status.upper()}</div>'


if uploaded_file:
    preview = load_document_preview(uploaded_file)
    file_info = get_file_info(uploaded_file)

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    if "processed_documents" not in st.session_state:
        st.session_state.processed_documents = []

    with st.spinner("Analyzing document..."):
        page_text_results = []

        if preview["document_type"] == "PDF":
            pdf_result = extract_text_from_pdf(preview["file_bytes"])
            extracted_text = pdf_result["text"]
            extraction_message = pdf_result["message"]
        else:
            first_image = preview["pages"][0][1]
            preprocessing = preprocess_document(first_image)
            ocr_result = extract_text_from_image(preprocessing["ocr_ready"])
            extracted_text = ocr_result["text"]
            extraction_message = ocr_result["message"]

        extracted_fields = extract_structured_information(extracted_text)
        analysis_result = analyze_document(extracted_text, extracted_fields)
        verification_result = verify_document(extracted_fields, analysis_result)

        st.session_state.analysis_result = {
            "preview": preview,
            "file_info": file_info,
            "extracted_text": extracted_text,
            "extraction_message": extraction_message,
            "fields": extracted_fields,
            "analysis": analysis_result,
            "verification": verification_result,
        }

        document_key = f"{file_info['file_name']}:{len(extracted_text)}"
        if document_key not in st.session_state.processed_documents:
            st.session_state.processed_documents.append(document_key)
            metric_key = "valid_documents" if verification_result["overall_status"] == "Valid" else "warning_documents" if verification_result["overall_status"] == "Warning" else "error_documents"
            if metric_key not in st.session_state:
                st.session_state[metric_key] = 0
            st.session_state[metric_key] += 1

        st.session_state.setdefault("valid_documents", 0)
        st.session_state.setdefault("warning_documents", 0)
        st.session_state.setdefault("error_documents", 0)

    result = st.session_state.analysis_result

    if page == "Dashboard":
        st.markdown(
            f'<div class="top-status"><span class="status-pill">📄 {file_info["file_name"]}</span><span class="status-pill">{result["analysis"]["document_type"]}</span><span class="status-pill {"status-valid" if result["verification"]["overall_status"] == "Valid" else "status-warning" if result["verification"]["overall_status"] == "Warning" else "status-error"}">● {result["verification"]["overall_status"].upper()}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("▦", "icon-teal", "Documents processed", str(len(st.session_state.processed_documents)))
        with c2:
            metric_card("✓", "icon-green", "Valid documents", str(st.session_state.valid_documents))
        with c3:
            metric_card("!", "icon-amber", "Warnings", str(st.session_state.warning_documents))
        with c4:
            metric_card("×", "icon-red", "Errors", str(st.session_state.error_documents))

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        left, right = st.columns([1.55, 1], gap="large")
        with left:
            st.markdown('<div class="surface"><div class="section-title">Document preview</div>', unsafe_allow_html=True)
            for page_number, bgr_image, png_bytes in result["preview"]["pages"]:
                if result["preview"]["document_type"] == "PDF":
                    st.image(png_bytes, caption=f"Page {page_number}", use_container_width=True)
                else:
                    st.image(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB), caption=f"Page {page_number}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="surface"><div class="section-title">Analysis snapshot</div>', unsafe_allow_html=True)
            st.metric("Detected type", result["analysis"]["document_type"])
            st.metric("Successful checks", result["verification"]["valid_count"])
            st.metric("Missing fields", len(result["analysis"]["missing_fields"]))
            st.metric("Detected issues", len(result["analysis"]["detected_issues"]))
            st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Upload & Analysis":
        tabs = st.tabs(["Extracted text", "Structured fields", "Preprocessed preview"])

        with tabs[0]:
            st.markdown('<div class="surface"><div class="section-title">OCR text</div>', unsafe_allow_html=True)
            st.text_area("Extracted document text", result["extracted_text"] or "No readable text was detected.", height=330, label_visibility="collapsed")
            st.caption(result["extraction_message"], help="Text extraction method and status")
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[1]:
            st.markdown('<div class="surface"><div class="section-title">Extracted information</div>', unsafe_allow_html=True)
            display_fields = {
                name: value
                for name, value in result["fields"].items()
                if name not in {"All Emails", "All Phones", "All Dates", "Keywords", "Numerical Information"}
            }
            rows = []
            for name, value in display_fields.items():
                if isinstance(value, (list, tuple, set)):
                    text_value = ", ".join(str(item) for item in value) if value else "Not Found"
                else:
                    text_value = str(value)
                extraction_status = "Not Found" if text_value.strip().lower() == "not found" or not text_value.strip() else "Extracted"
                rows.append({"Field": name, "Extracted value": text_value, "Status": extraction_status})

            field_frame = pd.DataFrame(rows)
            st.dataframe(field_frame, use_container_width=True, hide_index=True, height=min(520, 46 * (len(rows) + 1)))
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[2]:
            st.markdown('<div class="surface"><div class="section-title">Image preprocessing</div>', unsafe_allow_html=True)
            if result["preview"]["document_type"] == "IMAGE":
                original = result["preview"]["pages"][0][1]
                preprocessing = preprocess_document(original)
                left, right = st.columns(2)
                with left:
                    st.image(cv2.cvtColor(preprocessing["original"], cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
                with right:
                    st.image(preprocessing["ocr_ready"], caption="OCR-ready", use_container_width=True)
            else:
                st.markdown('<div class="info-box">Image preprocessing is applied to scanned PDF pages when OCR fallback is required. Digital PDF text was extracted directly when readable.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif page == "Verification":
        status = result["verification"]["overall_status"]
        st.markdown(status_card(status), unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("✓", "icon-green", "Successful checks", str(result["verification"]["valid_count"]))
        with c2:
            metric_card("!", "icon-amber", "Warnings", str(result["verification"]["warning_count"]))
        with c3:
            metric_card("×", "icon-red", "Errors", str(result["verification"]["error_count"]))

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        left, right = st.columns([1.35, 1], gap="large")
        with left:
            st.markdown('<div class="surface"><div class="section-title">Verification results</div>', unsafe_allow_html=True)
            check_frame = pd.DataFrame(result["verification"]["checks"])
            st.dataframe(check_frame, use_container_width=True, hide_index=True, height=min(430, 42 * (len(check_frame) + 1)))
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="surface"><div class="section-title">Check distribution</div>', unsafe_allow_html=True)
            counts = [result["verification"]["valid_count"], result["verification"]["warning_count"], result["verification"]["error_count"]]
            chart = go.Figure(go.Bar(x=["Valid", "Warning", "Error"], y=counts, marker_color=["#34D399", "#FBBF24", "#F87171"], text=counts, textposition="outside"))
            chart.update_layout(paper_bgcolor="#172438", plot_bgcolor="#172438", height=285, margin=dict(l=20, r=20, t=25, b=20), bargap=.42, font=dict(color="#A7B4C7"), showlegend=False, yaxis=dict(gridcolor="#2B3B50", zeroline=False), xaxis=dict(tickfont=dict(color="#F1F5F9")))
            st.plotly_chart(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        missing, issues = st.columns(2, gap="large")
        with missing:
            st.markdown('<div class="surface"><div class="section-title">Missing fields</div>', unsafe_allow_html=True)
            missing_fields = result["analysis"]["missing_fields"]
            if missing_fields:
                for field in missing_fields:
                    st.markdown(f'<span class="badge badge-warning">! {field}</span>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">✓ No missing fields detected.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with issues:
            st.markdown('<div class="surface"><div class="section-title">Detected issues</div>', unsafe_allow_html=True)
            detected_issues = result["analysis"]["detected_issues"]
            if detected_issues:
                for issue in detected_issues:
                    st.markdown(f'<div class="issue-box">{issue}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-box">✓ No issues detected in the implemented checks.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-box" style="margin-top:16px;">This status reports implemented rule-based checks only and does not confirm legal authenticity.</div>', unsafe_allow_html=True)

    elif page == "Reports":
        st.markdown('<div class="surface"><div class="section-title">Report manager</div>', unsafe_allow_html=True)
        status = result["verification"]["overall_status"]
        status_class = "badge-valid" if status == "Valid" else "badge-warning" if status == "Warning" else "badge-error"

        st.markdown(
            f'<div style="display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:12px;margin-bottom:16px;"><div><span class="muted">Document</span><br><strong>{file_info["file_name"]}</strong></div><div><span class="muted">Document type</span><br><strong>{result["analysis"]["document_type"]}</strong></div><div><span class="muted">Generated</span><br><strong>{datetime.now().strftime("%d %b %Y")}</strong></div><div><span class="muted">Status</span><br><span class="badge {status_class}">{status.upper()}</span></div></div>',
            unsafe_allow_html=True,
        )

        txt_bytes = generate_txt_report(file_info["file_name"], result["extracted_text"])
        csv_bytes = generate_csv_report(result["fields"])
        pdf_bytes = generate_pdf_report(file_info["file_name"], result["fields"], result["analysis"], result["verification"])

        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown('<div class="surface"><div class="section-title">Extracted text</div><div class="muted">Plain-text OCR output</div></div>', unsafe_allow_html=True)
            st.download_button("↓ Download TXT", data=txt_bytes, file_name=f"{Path(file_info['file_name']).stem}_extracted.txt", mime="text/plain", use_container_width=True)
        with r2:
            st.markdown('<div class="surface"><div class="section-title">Extracted fields</div><div class="muted">Structured CSV data</div></div>', unsafe_allow_html=True)
            st.download_button("↓ Download CSV", data=csv_bytes, file_name=f"{Path(file_info['file_name']).stem}_information.csv", mime="text/csv", use_container_width=True)
        with r3:
            st.markdown('<div class="surface"><div class="section-title">Verification report</div><div class="muted">Complete PDF summary</div></div>', unsafe_allow_html=True)
            st.download_button("↓ Download PDF", data=pdf_bytes, file_name=f"{Path(file_info['file_name']).stem}_report.pdf", mime="application/pdf", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="surface"><div class="section-title">Ready for document analysis</div><div class="muted">Use the sidebar to upload a PDF, JPG, JPEG, or PNG document. Maximum file size: 25 MB.</div></div>', unsafe_allow_html=True)

if uploaded_file:
    st.markdown('<div class="main-header">Document Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Review extraction, verification, and document analysis results.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="main-header">Document Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload a document to begin OCR, extraction, and verification.</div>', unsafe_allow_html=True)
