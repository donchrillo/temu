Das ist ein hervorragender Plan! In der KI-Welt nennen wir das einen **"Context-Dump"**. Es sorgt dafür, dass wir morgen keine Zeit mit "Erinnerst du dich noch...?" verschwenden, sondern sofort die Ärmel hochkrempeln können.

Ich habe dir hier eine strukturierte Zusammenfassung erstellt. Kopiere diesen Text einfach in eine Datei namens `SESSION_HANDOVER.md`. Morgen lädst du diese Datei in die neue Session hoch (oder kopierst den Inhalt in den ersten Prompt) und sagst: **"Lies das Handover und lass uns mit der Umsetzung der 6 Agenten-Updates starten."**

---

# 📑 Session Handover: TEMU ERP Migration (14. Feb 2026)

## 1. Projekt-Status & Kontext

* **System:** TEMU ERP Integration (FastAPI Backend, Vanilla JS Frontend, MSSQL).
* **Strategie:** "JTL-Independence". JTL wird sukzessive abgelöst. Fokus liegt aktuell auf der TEMU-API (Bestellungen, Bestände, Tracking).
* **Nächster Meilenstein:** Migration des Frontends von Vanilla JS zu **React 19 (SPA)** mit TypeScript.
* **Sicherheits-Standard:** JWT-Authentifizierung via HttpOnly-Cookies (erfolgreich im PoC getestet).

## 2. Vorliegende Dokumente & Blueprints

* **`AI_GUIDE.md`:** Das bestehende Handbuch für die KI-Agenten.
* **`VISION_2026.md`:** (Entwurf fertig) Der strategische Fahrplan vom TEMU-Tool zum vollwertigen OMS/WMS.
* **`Refactoring Plan (13. Feb)`:** Analyse der Agenten zur Verschlankung der `main.py` und Einführung von Pydantic & Error-Decorators.

## 3. Die 6 Agenten (Custom Instructions für Copilot)

Wir haben ein Set von 6 spezialisierten Agenten, die hybrid (altes Expertenwissen + neues strategisches Ziel) aufgebaut werden:

1. **Backend Review:** Security & Logic (SQLi, Resource Leaks).
2. **Backend Refactoring:** Pydantic, Repository-Pattern, Router-Extraktion.
3. **Frontend Migration (React):** Kern-Agent für den Umzug von Vanilla zu React 19.
4. **Frontend Review:** React-Performance & Accessibility.
5. **Documentation Agent:** Synchronisation via `AGENT_CHANGES.md`.
6. **Logging Agent:** DB-basiertes Tracking mit `job_id`.

## 4. Offene Punkte für morgen

* [ ] **Hybrid-Prompts finalisieren:** Die bestehenden langen Agenten-Prompts mit den neuen "Strategic Headers" kombinieren.
* [ ] **Frontend-Regeln trennen:** Sicherstellen, dass der Frontend-Refactoring-Agent präzise zwischen "Legacy Vanilla" und "Modern React" unterscheidet.
* [ ] **Start der Migration:** Einrichten der `frontend-react/` Struktur und Umzug der Auth-Logik (Login-Page).

---

### Ein kleiner Tipp für dich zum Feierabend:

Genieß den freien Kopf! Wir haben heute das komplette Fundament für die nächsten Monate Arbeit gelegt. Das System steht architektonisch auf extrem sicheren Beinen.

**Wir sehen uns morgen in der neuen Session! Ich freue mich drauf, das System mit dir live gehen zu sehen. Hab einen schönen Abend!**