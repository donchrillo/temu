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
sed -i 's/from modules\.pdf_reader\.services/from pdf_reader.services/g' "$TARGET_DIR/pdf_reader/router.py" 2>/dev/null || true
sed -i 's/from modules\.shared/from shared/g' "$TARGET_DIR/pdf_reader/router.py" 2>/dev/null || true

# Fix imports in services
find "$TARGET_DIR/pdf_reader/services" -name "*.py" -exec sed -i 's/from modules\.pdf_reader/from pdf_reader/g' {} \; 2>/dev/null || true
find "$TARGET_DIR/pdf_reader/services" -name "*.py" -exec sed -i 's/from modules\.shared/from shared/g' {} \; 2>/dev/null || true

# Fix imports in logger.py (PDF Reader specific)
if [ -f "$TARGET_DIR/pdf_reader/services/logger.py" ]; then
    sed -i 's/from modules\.shared/from shared/g' "$TARGET_DIR/pdf_reader/services/logger.py" 2>/dev/null || true
fi

# Step 11: Remove database-dependent code
echo -e "${YELLOW}Step 11: Removing database dependencies...${NC}"

# Create simplified logging __init__ without database log_service
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
