"""
gui_utils.py – Hilfsfunktionen für die Streamlit-Oberfläche

Dieses Modul unterstützt die grafische Benutzeroberfläche (GUI) durch
Hilfsfunktionen wie das Laden und Darstellen von Reportdaten.

Hauptfunktion:
- zeige_mini_report(): Visualisiert den zuletzt erzeugten Report im Streamlit-Dashboard.
"""

# ========== 📦 Standard- und Drittanbieter-Module ==========
import os                # Für Pfadprüfung
import pandas as pd      # Für Tabellenanzeige
import streamlit as st   # GUI-Framework

from backend import lade_report_sheets  # Funktion zum Laden von Report-Sheets


def zeige_mini_report(report_path: str) -> None:
    """
    Zeigt den Mini-Report in der Streamlit-Oberfläche an.

    Diese Funktion wird nach erfolgreicher Verarbeitung aufgerufen, um den erzeugten Excel-Report
    visuell in der Benutzeroberfläche darzustellen. Dabei werden:
    - zentrale KPIs wie Anzahl Ersetzungen, Fehler und offene IDs als Metriken gezeigt,
    - vier Tabs mit den einzelnen Sheets des Excel-Reports angezeigt:
      "Mini-Report", "Änderungen", "Fehler" und "Nicht gefunden".

    Args:
        report_path (str): Absoluter Pfad zur zuletzt erzeugten Excel-Auswertungsdatei.

    Returns:
        None
    """

    # === ❗Existenzprüfung ===
    if not os.path.isfile(report_path):
        st.warning("⚠️ Kein gültiger Report gefunden.")
        return

    # === 📥 Excel-Reportdatei laden (liefert 4 vorbereitete DataFrames) ===
    sheets = lade_report_sheets(report_path)
    if not sheets or "Mini-Report" not in sheets:
        st.warning("⚠️ Auswertung konnte nicht geladen werden.")
        return

    # === 📊 Sektion mit drei kompakten Kennzahlen (Metriken) ===
    st.markdown("## 📊 Überblick")
    col1, col2, col3 = st.columns(3)

    #mini = sheets["Mini-Report"]
    #col1.metric("✅ Ersetzungen", int(mini["Ersetzungen"].sum()))
    #col2.metric("❌ Fehler", mini["Verarbeitung OK"].tolist().count("❌"))
    #col3.metric("📦 Offene Order-IDs", int(mini["Offene Order-IDs"].sum()))
    mini = sheets.get("Mini-Report", pd.DataFrame())

    if "Ersetzungen" in mini.columns and "Offene Order-IDs" in mini.columns and "Verarbeitung OK" in mini.columns:
        col1.metric("✅ Ersetzungen", int(mini["Ersetzungen"].sum()))
        col2.metric("❌ Fehler", mini["Verarbeitung OK"].tolist().count("❌"))
        col3.metric("📦 Offene Order-IDs", int(mini["Offene Order-IDs"].sum()))
    else:
        col1.warning("Keine Auswertung verfügbar.")
        col2.warning("Kein Fehler-Status.")
        col3.warning("Keine offenen IDs.")


    # === 📁 Tabs für alle vier Report-Sheets ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧾 Mini-Report",
        "✏️ Änderungen",
        "⚠️ Fehler",
        "❓ Nicht gefunden"
    ])

    # === 🔎 Tab: Mini-Report (Kompaktübersicht je Datei) ===
    with tab1:
        df = sheets.get("Mini-Report", pd.DataFrame())
        st.dataframe(df) if not df.empty else st.info("Kein Mini-Report vorhanden.")

    # === 📝 Tab: Änderungen (Alle Ersetzungen im Detail) ===
    with tab2:
        df = sheets.get("Änderungen", pd.DataFrame())
        st.dataframe(df) if not df.empty else st.info("Keine Änderungen vorgenommen.")

    # === ⚠️ Tab: Fehlerprotokoll ===
    with tab3:
        df = sheets.get("Fehler", pd.DataFrame())
        st.dataframe(df) if not df.empty else st.success("Keine Fehler 🎉")

    # === ❓ Tab: Nicht gefundene Amazon-Order-IDs ===
    with tab4:
        df = sheets.get("Nicht gefunden", pd.DataFrame())
        st.dataframe(df) if not df.empty else st.success("Alle Order-IDs konnten zugeordnet werden ✅")

def upload_file() -> str | None:
    """
    Zeigt ein Upload-Feld für CSV- oder ZIP-Dateien und speichert die Datei im Eingangsordner.

    Diese Funktion stellt ein `st.file_uploader`-Element bereit, mit dem Benutzer Dateien
    direkt über die Streamlit-Oberfläche hochladen können. Die Datei wird im konfigurierten
    Eingangsverzeichnis (`ORDNER_EINGANG`) gespeichert.

    Returns:
        Optional[str]: Pfad zur gespeicherten Datei, oder None, wenn keine Datei hochgeladen wurde.
    """
    from config import ORDNER_EINGANG


    uploaded_file = st.file_uploader("Wähle eine Datei aus", type=["csv", "zip"], key="upload")

    if uploaded_file:
        # Zielpfad im Eingangsordner
        save_path = os.path.join(ORDNER_EINGANG, uploaded_file.name)

        # Dateiinhalt speichern
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return save_path

    return None
