"""
gui.py – Streamlit-Oberfläche zur CSV-/ZIP-Verarbeitung mit Logging, Reports & Export

Dieses Modul ist die zentrale Benutzeroberfläche des Projekts.
Hierüber wählt der Benutzer zu verarbeitende Dateien, startet die Verarbeitung,
zeigt Reports an und exportiert ZIP-Dateien mit Beilagen.

Die Geschäftslogik ist ausgelagert in:
- backend.py (Verarbeitung, Export)
- gui_utils.py (Anzeige des Excel-Reports)
- log_helper.py (Initialisierung des Logging)
"""

# ========== 📦 IMPORTS ==========
import os
import logging
import streamlit as st

from config import ORDNER_EINGANG, ORDNER_AUSGANG, ORDNER_LOG, TMP_ORDNER,ORDNER_EINGANG_ARCHIV,ORDNER_AUSGANG_ARCHIV
from backend import verarbeite_auswahl, erstelle_zip_mit_beilagen
from log_helper import init_logger
from gui_utils import zeige_mini_report, upload_file


# ========== 🪵 Logging initialisieren ==========
# Nur einmal initialisieren
#if "log_initialized" not in st.session_state:
#    logdatei = init_logger()
#    st.session_state.log_initialized = True




# ========== 🗂️ Session-State Initialisierung ==========
if "report_visible" not in st.session_state:
    st.session_state.report_visible = False

if "latest_report_path" not in st.session_state:
    st.session_state.latest_report_path = None


# ========== 🎛️ Seitenaufbau ==========
st.set_page_config(page_title="📦 JTL2Datev CSV-Verarbeiter", layout="wide")
st.title("📦 JTL2Datev CSV-Verarbeiter")




# --------------------------------------
# 📂 Bereich: Vorbereitung / Verarbeitung
# --------------------------------------
st.markdown("---")
st.subheader("📤 Datei-Upload (CSV oder ZIP)")

uploaded_path = upload_file()
if uploaded_path:
    try:
        st.info(f"✅ Datei hochgeladen: `{os.path.basename(uploaded_path)}`")
  
        logdatei = init_logger(force=True)
        logging.info(f"🚀 Automatische Verarbeitung gestartet für: {os.path.basename(uploaded_path)}")

        # Direktverarbeitung nach Upload
        verarbeite_auswahl([os.path.basename(uploaded_path)])

        st.success("✅ Datei wurde erfolgreich verarbeitet.")

    except Exception as e:
        st.error(f"❌ Fehler bei der Verarbeitung: {str(e)}")




# --------------------------------------
# 📊 Bereich: Mini-Report anzeigen
# --------------------------------------
if st.session_state.report_visible and st.session_state.latest_report_path:
    zeige_mini_report(st.session_state.latest_report_path)

# Hinweis zur letzten Reportdatei
if st.session_state.latest_report_path:
    st.info(f"📄 Letzter Report: `{os.path.basename(st.session_state.latest_report_path)}`")




# --------------------------------------
# 📦 Bereich: Nachbereitung / Export
# --------------------------------------
st.markdown("---")
st.subheader("📦 Nachbereitung / Export")

# Verfügbare Ausgabedateien
csvs = sorted([
    f for f in os.listdir(ORDNER_AUSGANG)
    if f.lower().endswith(".csv")
])

if not csvs:
    st.info("Keine exportierbaren CSV-Dateien im Ausgangsordner gefunden.")
else:
    export_auswahl = st.multiselect("Wähle CSV-Dateien für den Export (ZIP):", csvs)


    zip_name = st.text_input("ZIP-Dateiname (ohne .zip):", value="export_DE_2024")
    include_report = st.checkbox("📑 Mini-Report beilegen", value=True)
    include_log = st.checkbox("📝 Letztes Logfile beilegen", value=True)

    if st.button("📦 ZIP-Datei erstellen"):
        if not export_auswahl:
            st.warning("Bitte CSV-Dateien auswählen.")
        elif not zip_name.strip():
            st.warning("Bitte gültigen Dateinamen eingeben.")
        else:
            with st.spinner("ZIP wird erstellt..."):
                try:
                    erfolg, info = erstelle_zip_mit_beilagen(
                        export_auswahl,
                        zip_name,
                        include_report=include_report,
                        include_log=include_log,
                        report_path=st.session_state.get("latest_report_path")
                    )
                    if erfolg:
                        st.success(f"ZIP erfolgreich erstellt: `{info}`")
                        st.info("CSV-Dateien wurden archiviert.")

                            # Download-Link
                        zip_path = os.path.join(ORDNER_AUSGANG, info)
                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="📥 ZIP-Datei herunterladen",
                                data=f,
                                file_name=info,
                                mime="application/zip"
        )
                    else:
                        st.error(f"❌ ZIP konnte nicht erstellt werden: {info}")
                finally:
                    logging.shutdown()  # 📌 Hier sauber beenden!



# --------------------------------------
# 📜 Bereich: Letztes Logfile anzeigen
# --------------------------------------
st.markdown("---")
logs = sorted([f for f in os.listdir(ORDNER_LOG) if f.startswith("log_")], reverse=True)

if logs:
    letzter_log = logs[0]
    st.subheader("📝 Letztes Logfile")
    with st.expander(f"📋 {letzter_log} anzeigen"):
        with open(os.path.join(ORDNER_LOG, letzter_log), "r", encoding="utf-8") as f:
            st.text(f.read())

# --------------------------------------
# 🧹 Bereich: Verzeichnisse aufräumen
# --------------------------------------
from backend import leere_verzeichnisse

if st.button("🧹 Alle Verzeichnisse leeren"):
    aufraeum_verzeichnisse = [
        ORDNER_EINGANG,
        ORDNER_AUSGANG,
        ORDNER_LOG,
        TMP_ORDNER,
        ORDNER_EINGANG_ARCHIV,
        ORDNER_AUSGANG_ARCHIV
    ]

    fehler = leere_verzeichnisse(aufraeum_verzeichnisse)

    if fehler:
        st.warning("Einige Dateien konnten nicht gelöscht werden:")
        for pfad, msg in fehler:
            st.text(f"{pfad}: {msg}")
    else:
        st.success("✅ Alle Verzeichnisse wurden erfolgreich geleert.")

        # WICHTIG: Session-Status zurücksetzen → sonst wird beim Reload wieder verarbeitet!
        for key in ["uploaded_path", "latest_report_path", "report_visible", "uploaded_processed", "upload"]:
            st.session_state.pop(key, None)

  
        # st.subheader("🧾 Debug: Session-State-Inhalt")

        # if st.session_state:
        #     for key, value in st.session_state.items():
        #         st.text(f"{key} = {value}")
        # else:
        #     st.info("🔍 Der Session-State ist aktuell leer.")

        # time.sleep(10)    
        st.rerun()