# 🤖 AI Project Guide: TEMU Integration

**Datum der Erstellung:** 6. Februar 2026
**Zweck:** Dieser Leitfaden bietet der AI einen initialen Überblick über das TEMU-Integrationsprojekt und legt grundlegende Arbeitsprinzipien fest. Er soll zu Beginn jeder Arbeitssitzung gelesen werden, um den Kontext zu aktualisieren.

---

## 1. Projekt-Übersicht

Das TEMU-Integrationsprojekt ist ein System zur Synchronisation von Bestellungen, Inventar und Dokumenten zwischen der TEMU-Marktplatz-API und einem JTL ERP-System (SQL Server). Es besteht aus einem FastAPI-Backend mit geplanten Jobs, einem PWA-Frontend mit Echtzeit-WebSocket-Updates und PDF/CSV-Verarbeitungsfunktionen. Das Projekt wurde zu einer Monorepo-Struktur migriert, um die Modularität und Wartbarkeit zu verbessern.

---

## 2. Wichtige Dokumentations-Einstiegspunkte

Um den aktuellen Projektkontext zu verstehen, beginne immer mit diesen Dokumenten:

*   **[docs/README.md](docs/README.md)**: Der zentrale Index für alle Dokumentationen.
*   **[docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)**: Der aktuelle Status des Projekts, abgeschlossene Meilensteine (inkl. CSS Consolidation, Central Navigation) und der Fortschritt der CSV-Verarbeiter-Migration.
*   **[docs/TODO_LIST.md](docs/TODO_LIST.md)**: Eine konsolidierte Liste aller ausstehenden Aufgaben, bekannten Probleme und zukünftigen Erweiterungen.
*   **[docs/FIXES/OVERVIEW.md](docs/FIXES/OVERVIEW.md)**: Eine Zusammenfassung wichtiger behobener Fehler und daraus abgeleiteter Best Practices.

Für tiefere Einblicke in spezifische Architekturbereiche, siehe die Unterverzeichnisse in `docs/`:

*   [ARCHITECTURE/](docs/ARCHITECTURE/): Code-Struktur, Module, Datenflüsse.
*   [FRONTEND/](docs/FRONTEND/): PWA, WebSocket, Caching, CSS Architecture (Kapitel 14-15), Central Navigation.
*   [DATABASE/](docs/DATABASE/): Datenbank-Layer, Connections, Repositories.
*   [API/](docs/API/): FastAPI Server, REST Endpoints, WebSocket.
*   [WORKFLOWS/](docs/WORKFLOWS/): Job Orchestrierung, Scheduler, PM2.
*   [DEPLOYMENT/](docs/DEPLOYMENT/): Remote Setup, PM2 Commands.
*   [PERFORMANCE/](docs/PERFORMANCE/): Benchmarks, Optimierung.

---

## 3. Grundlegende Arbeitsprinzipien für die AI

Um eine sichere, effiziente und nachvollziehbare Entwicklung zu gewährleisten, halte dich strikt an die folgenden Prinzipien:

1.  **Dokumentation ist Teil des Codes – halte sie AKTUELL:**
    *   **Jede Code-Änderung, die die Architektur, Funktionalität oder das Verständnis des Systems beeinflusst, MUSS in den relevanten Dokumentationsdateien (im `docs/`-Verzeichnis) widergespiegelt werden.** Dies gilt insbesondere für Architektur-Dokumente, Status-Updates und die TODO-Liste.
    *   **Aktualisiere das Datum:** Bei jeder Änderung einer Dokumentationsdatei MUSS das im Header oder Footer angegebene Datum auf den aktuellen Tag aktualisiert werden.

2.  **Commit-Verpflichtung:**
    *   **Nach JEDER erfolgreichen Implementierung oder einem Satz logisch zusammenhängender Änderungen MUSS ein Git Commit durchgeführt werden.** Die Commit-Nachricht sollte klar, prägnant und aussagekräftig sein und dem Conventional Commits-Standard folgen (`<type>(<scope>): <subject>`).

3.  **Konsistenz und Konventionen:**
    *   Analysiere stets den umgebenden Code, Tests und Konfigurationen, um bestehende Projektkonventionen (Formatierung, Benennung, Architekturmuster, Bibliotheksverwendung) zu übernehmen und einzuhalten.
    *   Verwende keine neuen Bibliotheken oder Frameworks, es sei denn, deren Nutzung ist im Projekt bereits etabliert oder wurde explizit genehmigt.

4.  **Verifizierung ist entscheidend:**
    *   Nach Code-Änderungen (Fixes, Features) MÜSSEN, wenn anwendbar und umsetzbar, Tests durchgeführt werden, um die Korrektheit der Änderungen zu verifizieren. Identifiziere und nutze die projektspezifischen Testbefehle.
    *   Führe die projektspezifischen Build-, Linting- und Type-Checking-Befehle aus (z.B. `black`, `flake8`, `mypy`), um die Codequalität sicherzustellen.

5.  **Frage bei Unsicherheit:**
    *   Nimm keine signifikanten Aktionen über den klaren Umfang der Anfrage hinaus vor, ohne dies vorher mit dem Benutzer zu bestätigen.

---

## 4. Wie dieser Leitfaden verwendet werden soll

Zu Beginn jeder neuen Entwicklungssitzung sollte die AI angewiesen werden, diesen `AI_GUIDE.md` zu lesen. Dies stellt sicher, dass die AI über den aktuellsten Projektkontext und die geltenden Arbeitsprinzipien informiert ist. Beispiel-Prompt: "Lies dir die Datei `AI_GUIDE.md` durch und befolge die dort enthaltenen Anweisungen, um dich mit dem Projekt vertraut zu machen." 

---

**Ende des AI Project Guide**
