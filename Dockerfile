# === Basis-Image ===
FROM python:3.11-slim

# === Arbeitsverzeichnis festlegen ===
WORKDIR /app/src

# === Systemabhängigkeiten installieren (ohne SQL) ===
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# === Python-Abhängigkeiten installieren ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Anwendungscode kopieren ===
COPY ./src /app/src

# === Port für Streamlit freigeben ===
EXPOSE 8502

# === Anwendung starten ===
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
