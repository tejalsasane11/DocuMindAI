"""Streamlit application for intelligent document analysis and verification."""

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
.main-header {font-size: 2.35rem; font-weight: 750; color: #123B63; margin: 0 0 0.15rem 0; letter-spacing: -0.02em;}
.sub-header {color: #526071; margin-bottom: 1.4rem; font-size: 1.02rem;}
section[data-testid="stSidebar"] {border-right: 1px solid #DDE6F0;}
.status-valid {background:#DCFCE7;color:#166534;padding:14px;border-radius:10px;font-weight:800;text-align:center;border:1px solid #86EFAC;}
.status-warning {background:#FEF3C7;color:#92400E;padding:14px;border-radius:10px;font-weight:800;text-align:center;border:1px solid #FCD34D;}
.status-error {background:#FEE2E2;color:#991B1B;padding:14px;border-radius:10px;font-weight:800;text-align:center;border:1px solid #FCA5A5;}
[data-testid="stMetric"] {background:#F8FAFC;padding:16px;border-radius:10px;border:1px solid #DDE6F0;box-shadow:0 1px 3px rgba(15,23,42,.05);}
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
div[data-testid="stDataFrame"] {border:1px solid #DDE6F0;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("DocuMind AI")
st.sidebar.caption("Intelligent Document Analysis and Verification")
page = st.sidebar.radio("Navigation", ["Dashboard", "Upload & Analysis", "Verification", "Reports"])

st.markdown('<div class="main-header">Multimodal AI for Intelligent Document Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload documents for OCR, structured information extraction, and explainable rule-based checks.</div>', unsafe_allow_html=True)

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


def status_card(status: str) -> str:
    status_name = status.lower()
    css_class = "status-valid" if status_name == "valid" else "status-warning" if status_name == "warning" else "status-error"
    return f'<div class="{css_class}">{status.upper()}</div>'


if uploaded_file:
    preview = load_document_preview(uploaded_file)
    file_info = get_file_info(uploaded_file)

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

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

    result = st.session_state.analysis_result

    if page == "Dashboard":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Document", file_info["file_name"])
        with col2:
            st.metric("Detected Type", result["analysis"]["document_type"])
        with col3:
            st.metric("Valid Checks", result["verification"]["valid_count"])
        with col4:
            st.metric("Issues", len(result["analysis"]["detected_issues"]))

        st.markdown("### Document Preview")
        pages = result["preview"]["pages"]
        for page_number, bgr_image, png_bytes in pages:
            if result["preview"]["document_type"] == "PDF":
                st.image(png_bytes, caption=f"Page {page_number}", use_container_width=True)
            else:
                st.image(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB), caption=f"Page {page_number}", use_container_width=True)

    elif page == "Upload & Analysis":
        st.markdown("### Extracted Text")
        st.text_area("OCR result", result["extracted_text"] or "No readable text was detected.", height=320)

        st.markdown("### Extracted Information")
        display_fields = {
            name: value
            for name, value in result["fields"].items()
            if name not in {"All Emails", "All Phones", "All Dates", "Keywords"}
        }
        field_frame = pd.DataFrame(
            [{"Field": name, "Extracted Value": str(value)} for name, value in display_fields.items()]
        )
        st.dataframe(field_frame, use_container_width=True, hide_index=True)

        st.markdown("### Preprocessing Preview")
        if result["preview"]["document_type"] == "IMAGE":
            original = result["preview"]["pages"][0][1]
            preprocessing = preprocess_document(original)
            left, right = st.columns(2)
            with left:
                st.image(cv2.cvtColor(preprocessing["original"], cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
            with right:
                st.image(preprocessing["ocr_ready"], caption="OCR-ready", use_container_width=True)

        st.caption(result["extraction_message"])

    elif page == "Verification":
        status = result["verification"]["overall_status"]
        st.markdown(status_card(status), unsafe_allow_html=True)

        metric1, metric2, metric3 = st.columns(3)
        metric1.metric("Valid", result["verification"]["valid_count"])
        metric2.metric("Warnings", result["verification"]["warning_count"])
        metric3.metric("Errors", result["verification"]["error_count"])

        counts = [result["verification"]["valid_count"], result["verification"]["warning_count"], result["verification"]["error_count"]]
        chart = go.Figure(go.Bar(
            x=["Valid", "Warning", "Error"],
            y=counts,
            marker_color=["#2E8B57", "#D97706", "#DC2626"],
        ))
        chart.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Number of checks")
        st.plotly_chart(chart, use_container_width=True)

        st.markdown("### Verification Details")
        check_frame = pd.DataFrame(result["verification"]["checks"])
        st.dataframe(check_frame, use_container_width=True, hide_index=True)

        st.markdown("### Missing Fields")
        st.write(result["analysis"]["missing_fields"] or ["None"])

        st.markdown("### Detected Issues")
        st.write(result["analysis"]["detected_issues"] or ["No automatic issues detected."])

        st.info(result["verification"]["disclaimer"])

    elif page == "Reports":
        st.markdown("### Download Results")

        txt_bytes = generate_txt_report(
            file_info["file_name"],
            result["extracted_text"],
        )
        st.download_button(
            "Download extracted text (.txt)",
            data=txt_bytes,
            file_name=f"{Path(file_info['file_name']).stem}_extracted.txt",
            mime="text/plain",
        )

        csv_bytes = generate_csv_report(result["fields"])
        st.download_button(
            "Download extracted information (.csv)",
            data=csv_bytes,
            file_name=f"{Path(file_info['file_name']).stem}_information.csv",
            mime="text/csv",
        )

        pdf_bytes = generate_pdf_report(
            file_info["file_name"],
            result["fields"],
            result["analysis"],
            result["verification"],
        )
        st.download_button(
            "Download verification report (.pdf)",
            data=pdf_bytes,
            file_name=f"{Path(file_info['file_name']).stem}_report.pdf",
            mime="application/pdf",
        )

else:
    st.info("Upload a PDF, JPG, JPEG, or PNG document using the sidebar to begin.")
