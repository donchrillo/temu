"""Streamlit user interface for PDF document processing."""

import shutil
from typing import List
import streamlit as st

from config import (
    ORDNER_EINGANG_RECHNUNGEN,
    ORDNER_EINGANG_WERBUNG,
    TMP_ORDNER,
    ORDNER_LOG,
    ORDNER_AUSGANG,
)
from rechnungen_read import process_rechnungen
from werbung_read import process_ad_pdfs
from werbung_extrahiere_seiten import extract_and_save_first_page


def save_uploaded_files(uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile], target_dir) -> None:
    """Speichert hochgeladene Dateien im Zielverzeichnis."""
    for uploaded_file in uploaded_files:
        destination = target_dir / uploaded_file.name
        with open(destination, "wb") as f:
            f.write(uploaded_file.getbuffer())


def show_log(log_name: str) -> None:
    """Zeigt eine Log-Datei im Streamlit Interface an."""
    log_path = ORDNER_LOG / log_name
    if log_path.exists():
        st.subheader(f"Log: {log_path.name}")
        st.text(log_path.read_text(encoding="utf-8"))
    else:
        st.warning(f"Keine Logdatei gefunden: {log_name}")


def clear_directory(path) -> None:
    """Leert alle Dateien in einem gegebenen Verzeichnis."""
    for item in path.glob("*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def check_for_existing_files() -> None:
    """Gibt Warnung aus, wenn Upload- oder TMP-Verzeichnisse bereits Dateien enthalten."""
    warn_paths = [
        (ORDNER_EINGANG_RECHNUNGEN, "Rechnungen"),
        (ORDNER_EINGANG_WERBUNG, "Werbung"),
        (TMP_ORDNER, "Temporäre Werbung"),
    ]
    for path, name in warn_paths:
        if any(path.iterdir()):
            st.warning(f"⚠️ Das Verzeichnis für '{name}' enthält bereits Dateien. Bitte ggf. leeren.")


# ---------------------------------------------------------------------------
# Streamlit interface
# ---------------------------------------------------------------------------
st.title("📁 PDF Dokumentenverarbeitung")

check_for_existing_files()

# --------------------------- Rechnungen ------------------------------------
st.header("📄 Rechnungen hochladen")
invoice_files = st.file_uploader(
    "PDF-Rechnungen hochladen",
    type="pdf",
    accept_multiple_files=True,
    key="invoices"
)
if invoice_files:
    save_uploaded_files(invoice_files, ORDNER_EINGANG_RECHNUNGEN)
    st.success("Rechnungen gespeichert.")

if st.button("📊 Rechnungen verarbeiten"):
    rechnungen_excel = ORDNER_AUSGANG / "rechnungen.xlsx"
    df = process_rechnungen(directory=ORDNER_EINGANG_RECHNUNGEN, output_excel=rechnungen_excel)
    show_log("rechnung_read.log")
    if rechnungen_excel.exists():
        with open(rechnungen_excel, "rb") as f:
            st.download_button("Rechnungen Excel herunterladen", data=f, file_name="rechnungen.xlsx")

# ------------------------ Werbung ------------------------------------------
st.header("📢 Werbedokumente hochladen")
ad_files = st.file_uploader(
    "PDF-Werbung hochladen",
    type="pdf",
    accept_multiple_files=True,
    key="ads"
)
if ad_files:
    save_uploaded_files(ad_files, ORDNER_EINGANG_WERBUNG)
    st.success("Werbedokumente gespeichert.")

if st.button("📄 Werbung: Seiten extrahieren"):
    extract_and_save_first_page(input_dir=ORDNER_EINGANG_WERBUNG, output_dir=TMP_ORDNER)
    show_log("werbung_extraction.log")

if st.button("📊 Werbung verarbeiten"):
    werbung_excel = ORDNER_AUSGANG / "werbung.xlsx"
    df = process_ad_pdfs(directory=TMP_ORDNER, output_excel=werbung_excel)
    show_log("werbung_read.log")
    if werbung_excel.exists():
        with open(werbung_excel, "rb") as f:
            st.download_button("Werbung Excel herunterladen", data=f, file_name="werbung.xlsx")

# --------------------------- Aufräumen -------------------------------------
st.header("🧹 Verzeichnisse leeren")
if st.button("Alle Upload-Verzeichnisse leeren"):
    clear_directory(ORDNER_EINGANG_RECHNUNGEN)
    clear_directory(ORDNER_EINGANG_WERBUNG)
    clear_directory(TMP_ORDNER)
    st.success("Alle Verzeichnisse wurden geleert.")

# --------------------------- Link zum Dashboard -------------------------------------

if st.button("⬅️ Zurück zum Dashboard"):
    st.markdown('<meta http-equiv="refresh" content="0; URL=http://raspi-server:8500" />', unsafe_allow_html=True)

