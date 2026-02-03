# PDF Reader Standalone Export Guide

> **Created:** 3. Februar 2026
> **Purpose:** Export PDF Reader from Monorepo to Standalone FastAPI Application
> **Target Repo:** `pdf-reader-fastapi` (separate GitHub repository)

---

## 1. Overview

### Problem
- PDF Reader ist Teil des TOCI Tools Monorepo
- Einige Nutzer brauchen nur PDF Reader (ohne TEMU, CSV-Verarbeiter, etc.)
- Alte Standalone-Versionen (Streamlit-basiert) sind veraltet
- Neue Features werden nur im Monorepo entwickelt

### Solution
- **Haupt-Entwicklung:** Bleibt im Monorepo (`/home/chx/temu`)
- **Export-Script:** Generiert automatisch Standalone-Version
- **Separates Repository:** `pdf-reader-fastapi` für Distribution
- **Single Source of Truth:** Monorepo ist die einzige Quelle

### Benefits
- ✅ Keine Code-Duplikation während Entwicklung
- ✅ Automatischer Export (kein manuelles Kopieren)
- ✅ Standalone ist vollständig unabhängig
- ✅ Einfache Distribution an Nutzer ohne Monorepo-Komplexität
- ✅ Klare Trennung von Features

---

## 2. Standalone Architecture

### Directory Structure

```
pdf-reader-fastapi/                    # Standalone Repository
├── README.md                          # Standalone-spezifische Dokumentation
├── LICENSE                            # MIT/GPL (je nach Wahl)
├── .gitignore
├── .env.example                       # Beispiel-Konfiguration
│
├── main.py                            # Standalone Gateway (nur PDF Router)
├── requirements.txt                   # Minimale Dependencies
├── ecosystem.config.js                # PM2 Config für Standalone
│
├── pdf_reader/                        # PDF Reader Modul
│   ├── __init__.py
│   ├── router.py                      # FastAPI Router
│   ├── frontend/
│   │   ├── pdf.html
│   │   └── static/
│   │       ├── pdf.css
│   │       └── pdf.js
│   └── services/
│       ├── __init__.py
│       ├── logger.py
│       ├── werbung_service.py
│       └── rechnung_service.py
│
├── shared/                            # Minimale Shared-Infrastruktur
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                # .env Loader
│   │   └── .env                       # Runtime config (not in git)
│   └── logging/
│       ├── __init__.py
│       └── logger.py                  # Logger Factory
│
├── data/                              # Runtime Data
│   ├── werbung/
│   │   ├── input/
│   │   ├── output/
│   │   └── tmp/
│   └── rechnungen/
│       ├── input/
│       ├── output/
│       └── tmp/
│
├── logs/                              # Log Files
│   └── pdf_reader/
│       ├── pdf_reader.log
│       ├── werbung_read.log
│       └── rechnung_read.log
│
└── docs/                              # Standalone Documentation
    ├── installation.md
    ├── api.md
    └── troubleshooting.md
```

### Key Differences from Monorepo

| Monorepo | Standalone |
|----------|------------|
| `modules/pdf_reader/` | `pdf_reader/` |
| `modules/shared/` (full) | `shared/` (minimal) |
| `main.py` (all routes) | `main.py` (only PDF) |
| `requirements.txt` (all deps) | `requirements.txt` (minimal) |
| Database repositories (TEMU, JTL, etc.) | ❌ No database (file-based only) |
| APScheduler workers | ❌ No scheduled jobs |
| WebSocket for jobs | ❌ No WebSocket (optional: add for progress) |

### Included Features

**✅ Werbungsrechnungen (Ad Invoices):**
- Upload ZIP files
- Extract first pages
- Parse amounts (currency-aware)
- Generate Excel reports
- Preserve original filenames

**✅ Rechnungen (Regular Invoices):**
- Upload ZIP files
- Extract first pages
- Generate reports

**❌ Not Included:**
- TEMU marketplace integration
- JTL ERP integration
- CSV processing
- Database operations (TOCI, eazybusiness)
- Scheduled jobs (APScheduler)

---

## 3. Export Script Implementation

### Script Location
```
/home/chx/temu/scripts/export_pdf_reader.sh
```

### Script Content

```bash
#!/bin/bash
#
# PDF Reader Standalone Export Script
# Exports PDF Reader module from monorepo to standalone repository
#
# Usage: ./scripts/export_pdf_reader.sh [target_directory]
#
# Example:
#   ./scripts/export_pdf_reader.sh ~/projects/pdf-reader-fastapi
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONOREPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-../pdf-reader-fastapi}"
SCRIPT_DIR="$MONOREPO_ROOT/scripts"

echo -e "${GREEN}PDF Reader Standalone Export Script${NC}"
echo "=================================================="
echo "Monorepo: $MONOREPO_ROOT"
echo "Target:   $TARGET_DIR"
echo ""

# Step 1: Create target directory structure
echo -e "${YELLOW}Step 1: Creating directory structure...${NC}"
mkdir -p "$TARGET_DIR"/{pdf_reader/{frontend/static,services},shared/{config,logging},data/{werbung/{input,output,tmp},rechnungen/{input,output,tmp}},logs/pdf_reader,docs}

# Step 2: Copy PDF Reader module
echo -e "${YELLOW}Step 2: Copying PDF Reader module...${NC}"
cp -r "$MONOREPO_ROOT/modules/pdf_reader/router.py" "$TARGET_DIR/pdf_reader/"
cp -r "$MONOREPO_ROOT/modules/pdf_reader/frontend/"* "$TARGET_DIR/pdf_reader/frontend/"
cp -r "$MONOREPO_ROOT/modules/pdf_reader/services/"* "$TARGET_DIR/pdf_reader/services/"
cp "$MONOREPO_ROOT/modules/pdf_reader/__init__.py" "$TARGET_DIR/pdf_reader/"

# Step 3: Copy minimal shared infrastructure
echo -e "${YELLOW}Step 3: Copying shared infrastructure...${NC}"

# Config
cp "$MONOREPO_ROOT/modules/shared/config/__init__.py" "$TARGET_DIR/shared/config/"
cp "$MONOREPO_ROOT/modules/shared/config/settings.py" "$TARGET_DIR/shared/config/"

# Logging (only logger, not log_service with database)
cp "$MONOREPO_ROOT/modules/shared/logging/__init__.py" "$TARGET_DIR/shared/logging/"
cp "$MONOREPO_ROOT/modules/shared/logging/logger.py" "$TARGET_DIR/shared/logging/"

# Step 4: Create standalone main.py
echo -e "${YELLOW}Step 4: Creating standalone main.py...${NC}"
cat > "$TARGET_DIR/main.py" << 'EOF'
"""
PDF Reader - Standalone FastAPI Application
Extracts first pages from PDF invoices and generates Excel reports
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from pdf_reader.router import router as pdf_router

# Create FastAPI app
app = FastAPI(
    title="PDF Reader",
    description="Extract first pages from PDF invoices and generate Excel reports",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="pdf_reader/frontend/static"), name="static")

# Include PDF Reader router
app.include_router(pdf_router, prefix="/api/pdf", tags=["PDF Reader"])

# Serve frontend
@app.get("/")
async def root():
    """Serve PDF Reader frontend"""
    return FileResponse("pdf_reader/frontend/pdf.html")

@app.get("/pdf")
async def pdf_page():
    """Serve PDF Reader frontend (alternative route)"""
    return FileResponse("pdf_reader/frontend/pdf.html")

# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "pdf-reader", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Step 5: Create minimal requirements.txt
echo -e "${YELLOW}Step 5: Creating requirements.txt...${NC}"
cat > "$TARGET_DIR/requirements.txt" << 'EOF'
# PDF Reader Standalone - Minimal Dependencies
# Python 3.11+

# FastAPI
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20

# PDF Processing
PyMuPDF==1.25.2
pillow==11.2.1

# Excel Export
openpyxl==3.1.5
pandas==2.2.3

# Configuration
python-dotenv==1.1.0

# Utilities
python-dateutil==2.9.0.post0
EOF

# Step 6: Create .env.example
echo -e "${YELLOW}Step 6: Creating .env.example...${NC}"
cat > "$TARGET_DIR/.env.example" << 'EOF'
# PDF Reader Configuration

# Server
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO

# Data Directories (relative to project root)
DATA_DIR=./data
LOGS_DIR=./logs
EOF

# Step 7: Create ecosystem.config.js for PM2
echo -e "${YELLOW}Step 7: Creating PM2 config...${NC}"
cat > "$TARGET_DIR/ecosystem.config.js" << 'EOF'
module.exports = {
  apps: [{
    name: 'pdf-reader',
    script: 'main.py',
    interpreter: '.venv/bin/python',
    args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true
  }]
};
EOF

# Step 8: Create README.md
echo -e "${YELLOW}Step 8: Creating README.md...${NC}"
cat > "$TARGET_DIR/README.md" << 'EOF'
# PDF Reader - FastAPI

Professional PDF invoice processing tool built with FastAPI. Extracts first pages from PDF invoices and generates Excel reports.

## Features

- **Werbungsrechnungen (Ad Invoices)**: Extract, parse, and report
- **Rechnungen (Regular Invoices)**: Extract and organize
- **Excel Export**: Automatic report generation
- **File Management**: Organize input/output/temp files
- **Currency-Aware**: Handles GBP, EUR, USD, SEK, PLN
- **Original Filenames**: Preserves original file names in reports

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-name/pdf-reader-fastapi.git
cd pdf-reader-fastapi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### Run

**Development:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production (PM2):**
```bash
pm2 start ecosystem.config.js
pm2 logs pdf-reader
```

### Access

Open browser: `http://localhost:8000`

## API Endpoints

- `GET /` - Frontend UI
- `POST /api/pdf/upload/werbung` - Upload ad invoices (ZIP)
- `POST /api/pdf/upload/rechnungen` - Upload regular invoices (ZIP)
- `GET /api/pdf/download/{filename}` - Download results
- `GET /api/health` - Health check

## Directory Structure

```
pdf-reader-fastapi/
├── pdf_reader/         # PDF processing module
├── shared/             # Configuration and logging
├── data/               # Input/output files
├── logs/               # Log files
└── main.py             # Application entry point
```

## Documentation

See `docs/` directory for detailed documentation:
- `installation.md` - Installation guide
- `api.md` - API documentation
- `troubleshooting.md` - Common issues

## Requirements

- Python 3.11+
- 100MB disk space
- No database required (file-based)

## License

MIT License (or your choice)

## Support

Issues: https://github.com/your-name/pdf-reader-fastapi/issues
EOF

# Step 9: Create .gitignore
echo -e "${YELLOW}Step 9: Creating .gitignore...${NC}"
cat > "$TARGET_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Environment
.env
.env.local

# Data (runtime)
data/*/input/*
data/*/output/*
data/*/tmp/*
!data/*/.gitkeep

# Logs
logs/*.log
logs/pdf_reader/*.log
*.log

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# PM2
.pm2/
EOF

# Step 10: Fix import paths (modules.pdf_reader → pdf_reader)
echo -e "${YELLOW}Step 10: Fixing import paths...${NC}"

# Fix imports in router.py
sed -i 's/from modules\.pdf_reader\.services/from pdf_reader.services/g' "$TARGET_DIR/pdf_reader/router.py"
sed -i 's/from modules\.shared/from shared/g' "$TARGET_DIR/pdf_reader/router.py"

# Fix imports in services
find "$TARGET_DIR/pdf_reader/services" -name "*.py" -exec sed -i 's/from modules\.pdf_reader/from pdf_reader/g' {} \;
find "$TARGET_DIR/pdf_reader/services" -name "*.py" -exec sed -i 's/from modules\.shared/from shared/g' {} \;

# Fix imports in logger.py (PDF Reader specific)
if [ -f "$TARGET_DIR/pdf_reader/services/logger.py" ]; then
    sed -i 's/from modules\.shared/from shared/g' "$TARGET_DIR/pdf_reader/services/logger.py"
fi

# Step 11: Remove database-dependent code
echo -e "${YELLOW}Step 11: Removing database dependencies...${NC}"

# Create simplified logger without database log_service
cat > "$TARGET_DIR/shared/logging/__init__.py" << 'EOF'
"""Shared Logging Module - Standalone Version"""
from .logger import create_module_logger

__all__ = ['create_module_logger']
EOF

# Step 12: Create .gitkeep files
echo -e "${YELLOW}Step 12: Creating .gitkeep files...${NC}"
touch "$TARGET_DIR/data/werbung/input/.gitkeep"
touch "$TARGET_DIR/data/werbung/output/.gitkeep"
touch "$TARGET_DIR/data/werbung/tmp/.gitkeep"
touch "$TARGET_DIR/data/rechnungen/input/.gitkeep"
touch "$TARGET_DIR/data/rechnungen/output/.gitkeep"
touch "$TARGET_DIR/data/rechnungen/tmp/.gitkeep"
touch "$TARGET_DIR/logs/pdf_reader/.gitkeep"

# Step 13: Create __init__.py files
echo -e "${YELLOW}Step 13: Creating __init__.py files...${NC}"
touch "$TARGET_DIR/shared/__init__.py"

# Step 14: Summary
echo ""
echo -e "${GREEN}✅ Export completed successfully!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. python -m venv .venv"
echo "3. source .venv/bin/activate"
echo "4. pip install -r requirements.txt"
echo "5. cp .env.example .env"
echo "6. uvicorn main:app --reload"
echo ""
echo "Test with: curl http://localhost:8000/api/health"
echo ""
echo -e "${YELLOW}Note: Review and test before pushing to GitHub!${NC}"
```

### Make Script Executable

```bash
chmod +x /home/chx/temu/scripts/export_pdf_reader.sh
```

---

## 4. Step-by-Step Usage Guide

### Initial Setup (One-Time)

**Step 1: Create Standalone Repository**
```bash
# On GitHub: Create new repository 'pdf-reader-fastapi'

# Locally: Clone the empty repo
cd ~/projects
git clone https://github.com/your-name/pdf-reader-fastapi.git
```

**Step 2: Run Export Script**
```bash
cd /home/chx/temu
./scripts/export_pdf_reader.sh ~/projects/pdf-reader-fastapi
```

**Step 3: Initialize Standalone Repo**
```bash
cd ~/projects/pdf-reader-fastapi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
```

**Step 4: Test Locally**
```bash
# Start server
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Test in browser
# http://127.0.0.1:8001

# Test API
curl http://127.0.0.1:8001/api/health
# Expected: {"status":"ok","service":"pdf-reader","version":"1.0.0"}
```

**Step 5: Commit and Push**
```bash
git add .
git commit -m "Initial commit: PDF Reader Standalone v1.0.0"
git push origin main
```

---

### Regular Update Workflow

Wenn du PDF Reader im Monorepo weiterentwickelst:

**Step 1: Develop in Monorepo**
```bash
cd /home/chx/temu

# Make changes to modules/pdf_reader/
# ... development ...

# Test in monorepo
pm2 restart temu-api

# Commit changes
git add modules/pdf_reader/
git commit -m "feat(pdf): New feature XYZ"
git push
```

**Step 2: Export to Standalone**
```bash
# Run export script
./scripts/export_pdf_reader.sh ~/projects/pdf-reader-fastapi
```

**Step 3: Test Standalone**
```bash
cd ~/projects/pdf-reader-fastapi

# Activate venv
source .venv/bin/activate

# Test
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Verify new feature works
# ... manual testing ...
```

**Step 4: Update Standalone Repo**
```bash
# Check changes
git status
git diff

# Commit
git add .
git commit -m "Update from monorepo: New feature XYZ"

# Tag release (optional)
git tag v1.1.0
git push origin main --tags
```

---

## 5. Testing Checklist

### Before Pushing to Standalone Repo

- [ ] **Import Check:** No `modules.*` imports left
  ```bash
  grep -r "from modules\." .
  # Should return nothing
  ```

- [ ] **Syntax Check:** All Python files valid
  ```bash
  find . -name "*.py" -exec python -m py_compile {} \;
  ```

- [ ] **Server Start:** Application starts without errors
  ```bash
  uvicorn main:app --host 127.0.0.1 --port 8001
  ```

- [ ] **Health Check:** API responds
  ```bash
  curl http://127.0.0.1:8001/api/health
  ```

- [ ] **Frontend:** UI loads correctly
  - Open `http://127.0.0.1:8001` in browser
  - Verify upload forms visible
  - Verify no JavaScript errors in console

- [ ] **File Upload:** Can upload ZIP files
  - Upload test ZIP to Werbung
  - Upload test ZIP to Rechnungen
  - Verify files appear in `data/*/output/`

- [ ] **Excel Export:** Reports generate correctly
  - Check `data/*/output/` for Excel files
  - Open Excel, verify data correct
  - Verify original filenames preserved (Werbung)

- [ ] **Logs:** Log files created
  - Check `logs/pdf_reader/*.log` exist
  - Verify logs contain expected entries

---

## 6. Troubleshooting

### Common Issues

**Issue 1: Import Error - "No module named 'modules'"**

```bash
# Cause: Import paths not updated
# Fix: Run Step 10 of export script manually
find pdf_reader/ -name "*.py" -exec sed -i 's/from modules\./from /g' {} \;
```

**Issue 2: Missing Dependencies**

```bash
# Cause: requirements.txt incomplete
# Fix: Add missing package
pip install <package-name>
# Update requirements.txt:
pip freeze | grep <package-name> >> requirements.txt
```

**Issue 3: Data Directories Missing**

```bash
# Cause: Export script failed to create directories
# Fix: Create manually
mkdir -p data/{werbung,rechnungen}/{input,output,tmp}
mkdir -p logs/pdf_reader
```

**Issue 4: Frontend Not Loading**

```bash
# Cause: Static files path incorrect
# Fix: Verify main.py has correct mount
# Should be: app.mount("/static", StaticFiles(directory="pdf_reader/frontend/static"), ...)
```

**Issue 5: Permission Denied on Script**

```bash
# Cause: Script not executable
# Fix:
chmod +x scripts/export_pdf_reader.sh
```

---

## 7. Maintenance

### When to Re-Export

Re-export when:
- ✅ New features added to PDF Reader in monorepo
- ✅ Bug fixes in PDF Reader services
- ✅ Frontend updates (HTML/CSS/JS)
- ✅ Dependency updates

No re-export needed when:
- ❌ TEMU module changes
- ❌ CSV-Verarbeiter module changes
- ❌ Database schema changes
- ❌ Worker/scheduler changes

### Versioning Strategy

**Semantic Versioning:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (e.g., API changes, removed features)
- **MINOR:** New features (backward-compatible)
- **PATCH:** Bug fixes (backward-compatible)

**Example:**
```bash
# Bug fix
git tag v1.0.1

# New feature
git tag v1.1.0

# Breaking change
git tag v2.0.0

# Push tags
git push origin --tags
```

### Release Process

1. **Test in Monorepo:** Ensure all tests pass
2. **Export to Standalone:** Run export script
3. **Test Standalone:** Full test suite
4. **Update CHANGELOG:** Document changes
5. **Tag Release:** Create git tag
6. **Push:** Push to GitHub
7. **Create GitHub Release:** Add release notes

---

## 8. Docker Deployment (Optional)

### Dockerfile

Create `Dockerfile` in standalone repo:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/{werbung,rechnungen}/{input,output,tmp} logs/pdf_reader

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  pdf-reader:
    build: .
    container_name: pdf-reader
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Usage

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 9. Distribution

### GitHub Release

1. Create release on GitHub
2. Attach `requirements.txt`
3. Add installation instructions
4. Link to documentation

### PyPI Package (Advanced)

Convert to pip-installable package:

```bash
# Create setup.py
# Upload to PyPI
# Users can install with: pip install pdf-reader-fastapi
```

### Docker Hub

```bash
# Build and tag
docker build -t your-name/pdf-reader:latest .

# Push to Docker Hub
docker push your-name/pdf-reader:latest

# Users can run with:
docker run -p 8000:8000 -v ./data:/app/data your-name/pdf-reader:latest
```

---

## 10. Future Enhancements

### Optional Features to Add

**WebSocket Support:**
- Add progress updates during PDF processing
- Real-time status in frontend

**Authentication:**
- Add basic auth or JWT tokens
- Multi-user support

**Database (Optional):**
- SQLite for local job history
- No external database needed

**Batch Processing:**
- Queue system for large uploads
- Background task processing

**API Key Management:**
- Allow API access with keys
- Rate limiting

---

## Summary Checklist

Before each export:
- [ ] Test PDF Reader in monorepo
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Commit monorepo changes

After export:
- [ ] Run export script
- [ ] Test standalone locally
- [ ] Check import paths
- [ ] Verify all features work
- [ ] Update version number
- [ ] Commit to standalone repo
- [ ] Tag release
- [ ] Create GitHub release

---

**Last Updated:** 3. Februar 2026
**Script Location:** `/home/chx/temu/scripts/export_pdf_reader.sh`
**Standalone Repo:** `pdf-reader-fastapi` (GitHub)
