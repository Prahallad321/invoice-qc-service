import json
from pathlib import Path
from typing import Dict, Any, List

import requests
import streamlit as st
import pandas as pd

BACKEND_URL = "http://127.0.0.1:8000"

PDF_SAVE_DIR = Path("pdfs")
PDF_SAVE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Invoice QC Console", layout="wide")
st.title("Invoice QC Console")

# ---------------- Sidebar ----------------
st.sidebar.header("Backend")
backend_url = st.sidebar.text_input("FastAPI URL", BACKEND_URL)

st.sidebar.write("Health:")
try:
    health = requests.get(f"{backend_url}/health", timeout=3).json()
    st.sidebar.success("OK")
except Exception:
    st.sidebar.error("Not reachable")


# ---------------- Upload ----------------
uploaded_files = st.file_uploader(
    "Upload invoice PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:

    saved_paths = []

    # ✅ SAVE PDFs LOCALLY so CLI can see them
    for f in uploaded_files:
        save_path = PDF_SAVE_DIR / f.name
        with open(save_path, "wb") as out:
            out.write(f.getbuffer())
        saved_paths.append(str(save_path))

    st.success("✅ PDFs saved to local folder:")
    st.code("\n".join(saved_paths))


# ---------------- Run QC ----------------
if uploaded_files and st.button("Run QC on uploaded PDFs"):

    with st.spinner("Uploading to backend + processing..."):

        files = [
            ("files", (f.name, f.getvalue(), "application/pdf"))
            for f in uploaded_files
        ]

        resp = requests.post(
            f"{backend_url}/extract-and-validate-pdfs",
            files=files
        )

        data = resp.json()

    st.success("✅ Done.")

    extracted: List[Dict[str, Any]] = data.get("extracted", [])
    validation: Dict[str, Any] = data.get("validation", {})

    # ---------------- Summary ----------------
    summary = validation.get("summary", {})
    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total invoices", summary.get("total_invoices", 0))
    col2.metric("Valid invoices", summary.get("valid_invoices", 0))
    col3.metric("Invalid invoices", summary.get("invalid_invoices", 0))


    # ---------------- Per-invoice table ----------------
    results = validation.get("results", [])
    df = pd.DataFrame(results)

    if not df.empty:
        df["errors_str"] = df["errors"].apply(lambda x: "\n".join(x) if x else "")
        st.subheader("Invoices")
        st.dataframe(
            df[["invoice_id", "is_valid", "errors_str"]],
            use_container_width=True,
            hide_index=True,
        )


    # ---------------- Download PDFs ----------------
    st.subheader("Download PDF Reports")

    status_map = {r["invoice_id"]: r["is_valid"] for r in results}

    for inv in extracted:
        invoice_id = inv.get("invoice_number") or inv.get("source_pdf") or "UNKNOWN"
        is_valid = status_map.get(invoice_id)

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(
                f"**{invoice_id}** | Buyer: {inv.get('buyer_name') or '-'} | "
                f"Seller: {inv.get('seller_name') or '-'}"
            )

        with col2:
            try:
                resp = requests.post(
                    f"{backend_url}/generate-report-pdf",
                    json=inv,
                    params={"is_valid": json.dumps(is_valid)},
                )

                pdf_hex = resp.json()["pdf_hex"]
                pdf_bytes = bytes.fromhex(pdf_hex)

                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"{invoice_id}.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"PDF generation error: {e}")
