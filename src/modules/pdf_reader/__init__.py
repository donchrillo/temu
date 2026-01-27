"""PDF Reader module: services for processing invoices and ads PDFs.

This package provides pure services (no UI) to:
- extract first pages from advertising PDFs with normalized filenames
- parse invoice PDFs and export structured Excel files
- parse advertising PDFs and export structured Excel files

Later these services can be wired to FastAPI endpoints and the PWA.
"""
