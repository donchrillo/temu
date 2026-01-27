# 📚 TEMU Integration – Dokumentation

**Willkommen in der zentralen Dokumentations-Datenbank!**

Alle technischen Dokumentationen der TEMU-Integration sind hier organisiert. Diese Docs sind **Teil des Codes** und sollten bei Änderungen aktualisiert werden.

---

## 📂 Struktur

### [ARCHITECTURE/](./ARCHITECTURE/)
Code-Struktur, Module, Data Flows

- **[code_structure.md](./ARCHITECTURE/code_structure.md)** – Projektbaum & Modul-Übersicht
  - Projektstruktur (welche Datei macht was)
  - Kern-Module (API, DB, Connectors, Services, Workflows)
  - Data Flow Diagramme
  - Wichtige Patterns (DI, Context Manager, Batch Queries)
  - SQL Queries (Stock Lookup, Tracking, Job Status)
  - Performance Notes & Testing/Debugging

### [FRONTEND/](./FRONTEND/)
PWA (Progressive Web App), WebSocket, HTTPS/WSS

- **[architecture.md](./FRONTEND/architecture.md)** – Frontend & PWA Integration
  - PWA Übersicht (Offline, Installation, Caching)
  - Automatische Protokoll-Erkennung (HTTP ↔ HTTPS)
  - WebSocket Integration (Live Job-Updates)
  - manifest.json (PWA Metadaten & Icons)
  - Service Worker (Offline-Caching, Lifecycle)
  - Backend Icon-Route & Icon-Erstellung
  - Installation auf Android/iOS
  - Debugging & Deployment Checklist

### 📂 Struktur (Technische Layer)

### [DATABASE/](./DATABASE/)
Datenbank-Layer, Connections, Repositories

- **[architecture.md](./DATABASE/architecture.md)** – Komplette DB-Architektur (SQLAlchemy, Connection Pooling, Best Practices, Troubleshooting)
  - Konfiguration & Engine Setup
  - Context Manager Pattern
  - Repository Pattern Integration
  - Batch-Query Optimierungen (2100-Parameter Problem)
  - Error Handling & Debugging
  - Performance Best Practices

### [API/](./API/)
FastAPI Server, REST Endpoints, WebSocket Integration

- **[architecture.md](./API/architecture.md)** – Komplette API-Architektur (FastAPI, Endpoints, WebSocket, Security, Performance)
  - Server Setup & Konfiguration
  - REST Endpoints Pattern & Design
  - WebSocket Integration (Live Logging)
  - Error Handling & HTTP Status Codes
  - Authentication & CORS Security
  - Request/Response Validation (Pydantic)
  - Performance Optimization (Async, Connection Management, Caching)
  - API Dokumentation & Testing (OpenAPI/Swagger)
  - Deployment Checklist

### [WORKFLOWS/](./WORKFLOWS/)
Job Orchestrierung, APScheduler, PM2 Integration

- **[architecture.md](./WORKFLOWS/architecture.md)** – Komplette Workflow-Architektur (APScheduler, PM2, Job Management, Retry Logic)
  - Job System Übersicht & State Machine
  - APScheduler Integration (Cron Scheduling)
  - PM2 Integration (Process Management, Auto-Restart)
  - Job Models & State Management
  - Worker Service Pattern
  - Workflow Orchestrierung (Praktische Beispiele)
  - Error Handling & Retry Logic
  - Monitoring & Health Checks
  - Scaling & High Availability
  - Production Deployment Checklist

### [DEPLOYMENT/](./DEPLOYMENT/)
Remote SSH Setup, PM2 Commands, Environment Variables

- **[architecture.md](./DEPLOYMENT/architecture.md)** – Remote-Setup & PM2 Basics
  - VSCode Remote SSH Configuration
  - PM2 Quick Reference (start, logs, restart, status)
  - Environment Variables & Secrets
  - Deployment Workflow & Health Checks
  - Troubleshooting & Maintenance

### [PERFORMANCE/](./PERFORMANCE/)
Benchmarks, Optimization Guides, Monitoring

- **[architecture.md](./PERFORMANCE/architecture.md)** – Performance & Optimization Guide
  - Baseline Benchmarks (Queries, API, Jobs)
  - Real-Time Monitoring (PM2, API, Connection Pool)
  - Key Performance Indicators (KPIs)
  - Optimization Checklist
  - Performance Tuning (Memory, CPU, Queries)
  - Monitoring Tools & Health Checks

---

## 🎯 Wie man Docs nutzt

### Für neue Entwickler
1. Starten: [ARCHITECTURE/code_structure.md](./ARCHITECTURE/code_structure.md) – Was macht welche Datei?
2. Vertiefen: [DATABASE/architecture.md](./DATABASE/architecture.md) – Datenbank-Patterns
3. APIs: [API/architecture.md](./API/architecture.md) – REST Endpoints & WebSocket
4. Frontend: [FRONTEND/architecture.md](./FRONTEND/architecture.md) – PWA & HTTPS
5. Workflows: [WORKFLOWS/architecture.md](./WORKFLOWS/architecture.md) – Job Orchestrierung
6. Deployment: [DEPLOYMENT/architecture.md](./DEPLOYMENT/architecture.md) – SSH & PM2
7. Code: Mit Best Practices in `src/` anfangen

### Für Code-Reviews
- Überprüfen: Befolgt die Dokumentation alle Patterns?
- Updaten: Neue Patterns sofort dokumentieren
- Verlinken: Im Code Referenzen zu Docs hinzufügen

### Für Troubleshooting
- [DATABASE/architecture.md – Kapitel 7](./DATABASE/architecture.md#7-error-handling--debugging) – Häufige Fehler & Lösungen
- [PERFORMANCE/architecture.md – Kapitel 5](./PERFORMANCE/architecture.md#5-performance-tuning) – Query Lags, Memory Leaks, CPU Spikes

---

## 📝 Best Practices für diese Docs

1. **Aktuell halten:** Bei jedem größeren Code-Change die Docs updaten
2. **Praktische Beispiele:** Code-Snippets sind wichtiger als Theorie
3. **Links verwenden:** Zwischen verwandten Dokumenten verlinken
4. **Fehlgeschlagene Patterns dokumentieren:** Auch "was NICHT funktioniert"
5. **Performance-Messungen beilegen:** Mit echten Zahlen, nicht Schätzungen

---

## 🔥 Quick Links

- [Code-Struktur & Module](./ARCHITECTURE/code_structure.md)
- [Frontend PWA & WebSocket](./FRONTEND/architecture.md)
- [Datenbank-Architektur](./DATABASE/architecture.md)
- [API-Architektur](./API/architecture.md)
- [Workflows & Job Orchestrierung](./WORKFLOWS/architecture.md)
- [Remote SSH & PM2 Setup](./DEPLOYMENT/architecture.md)
- [Performance Benchmarks](./PERFORMANCE/architecture.md)
- [Projektbaum](./ARCHITECTURE/code_structure.md#1-projektbaum)
- [Order & Inventory Workflows](./ARCHITECTURE/code_structure.md#3-data-flow-diagramme)
- [SQL-Server 2100-Parameter Workaround](./DATABASE/architecture.md#6-batch-query-optimierungen)
- [WebSocket Integration](./FRONTEND/architecture.md#4-websocket-integration)
- [PWA Installation auf Android](./FRONTEND/architecture.md#9-installation-auf-geräten)
- [APScheduler Cron Scheduling](./WORKFLOWS/architecture.md#2-apscheduler-integration)
- [PM2 Process Management](./WORKFLOWS/architecture.md#3-pm2-integration)
- [Health Check Script](./PERFORMANCE/architecture.md#8-production-health-check-täglich)
- [Retry Logic & Error Handling](./WORKFLOWS/architecture.md#7-error-handling--retry-logic)
- [Performance Best Practices](./DATABASE/architecture.md#8-performance-best-practices)
- [Production Deployment](./WORKFLOWS/architecture.md#10-production-deployment-checklist)

---

**Zuletzt aktualisiert:** 27. Januar 2026  
**Wartbar:** Ja ✅
