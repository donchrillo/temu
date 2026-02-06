# === Basis-Image ===
FROM python:3.11-slim

# === Arbeitsverzeichnis festlegen ===
WORKDIR /app/src

# === Systemabhängigkeiten installieren (ODBC-Treiber etc.) ===
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# === Python-Abhängigkeiten installieren ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# === Anwendungscode kopieren ===
COPY ./src /app/src

# === Port für Streamlit freigeben ===
EXPOSE 8501

# === Anwendung starten ===
CMD ["streamlit", "run", "gui.py", "--server.port=8501", "--server.address=0.0.0.0"]
