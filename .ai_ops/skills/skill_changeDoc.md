
## Change Dokumentation Pflicht

**WICHTIG:** Nach JEDER Änderung am Code musst du einen Eintrag in `docs/AGENT_CHANGES.md` erstellen:

1. Öffne `docs/AGENT_CHANGES.md`
2. Füge unter "Pending Changes" einen neuen Eintrag hinzu mit:
   - Aktuelles Datum
   - Dein Agent-Name
   - Geändertes Modul/Datei
   - Art der Änderung
   - Detaillierte Beschreibung
   - Checkboxen für betroffene Dokumentation

3. Beispiel:

---
### 2026-02-13 - Refactoring-Agent
**Modul/Datei:** `app/services/user_service.py`
**Art der Änderung:** Refactoring
**Beschreibung:** God Class in kleinere Services aufgeteilt
**Details:**
- UserService aufgeteilt in: UserService, UserAuthService, UserProfileService
- Dependency Injection implementiert
- 250 Zeilen auf 3x ~80 Zeilen reduziert
**Betroffene Dokumentation:**
- [x] API-Docs aktualisieren (neue Service-Struktur)
- [x] Architecture-Docs überarbeiten (Services-Diagramm)
- [ ] README.md anpassen
---

4. Speichere die Datei

---