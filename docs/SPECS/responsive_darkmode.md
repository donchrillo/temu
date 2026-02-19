# SPEC.md - Responsive Design & Dark Mode

## Projekt
**TEMU/TOCI ERP - Frontend React**  
**Version:** 1.0  
**Datum:** 19.02.2026  
**Status:** Spezifikation für Implementierung

---

## 1. Zielsetzung

Das Dashboard soll vollständig responsive werden mit:
1. **Einklappbare Sidebar** (Desktop) - Toggle-Button zum Einklappen
2. **Burger-Menü** (Mobile/Tablet) - Sidebar komplett ausblenden
3. **Dark Mode Toggle** - In der Header-Leiste oben rechts

---

## 2. Aktuelle Struktur (Zustand VOR Implementierung)

### Dateien
```
frontend-react/
├── src/
│   ├── components/layout/
│   │   ├── app-shell.tsx    # Haupt-Layout (flex container)
│   │   ├── sidebar.tsx      # Navigation links (w-60固定)
│   │   └── header.tsx       # Header oben (Icons: Search, Bell)
│   ├── App.tsx              # Router-Konfiguration
│   ├── index.css            # Tailwind base
│   └── lib/utils.ts         # Utility-Funktionen
├── tailwind.config.js       # Farben & Theme
└── index.html               # Entry-Point
```

### Probleme
- Sidebar hat feste Breite `w-60` (240px) - nicht einklappbar
- Keine Responsive Breakpoints für Mobile/Tablet
- Kein Dark Mode implementiert
- Kein Burger-Menü

---

## 3. Funktionale Anforderungen

### 3.1 Sidebar - Einklappbar (Desktop)

**Verhalten:**
- Sidebar hat Toggle-Button (Chevron oder X-Icon)
- Im "eingeklappten" Zustand: schmal (`w-16` = 64px) oder komplett ausgeblendet
- **Empfehlung:** Einklappen auf Icons-only (`w-16`), nicht komplett ausblenden
- Animation: `transition-all duration-300 ease-in-out`
- Sidebar-Zustand in localStorage speichern (Persistenz)

**UI-Elemente:**
- Toggle-Button im Header der Sidebar (oben rechts)
- Beim Einklappen: Nur Icons sichtbar, Labels ausblenden
- Tooltips beim Hover über Icons (Label anzeigen)

**Technische Umsetzung:**
- React State: `const [sidebarCollapsed, setSidebarCollapsed] = useState(false)`
- Tailwind: `w-60` → `w-16` (conditional mit `sidebarCollapsed ? 'w-16' : 'w-60'`)
- Übergang: `transition-all duration-300`

### 3.2 Burger-Menü (Mobile/Tablet)

**Breakpoints:**
- Mobile: `< 640px` (sm)
- Tablet: `640px - 1024px` (md)
- Desktop: `> 1024px` (lg)

**Verhalten:**
- **< lg (Desktop):** Sidebar ausgeblendet, Burger-Button im Header
- Burger-Button öffnet Overlay-Modal mit Sidebar-Inhalten
- Overlay schließt bei: Klick außerhalb, Navigation zu neuer Seite, oder Schließen-Button
- **>= lg (Desktop):** Sidebar immer sichtbar

**UI-Elemente:**
- Burger-Button im Header (links, vor dem Titel)
- Icon: 3 horizontale Linien (lucide: `Menu`)
- Overlay: halbtransparenter Hintergrund (`bg-black/50`), Seitenleiste von links eingliedern (`translate-x-0`)

### 3.3 Dark Mode Toggle

**UI-Elements:**
- Toggle-Button in Header (rechts, neben Notifications)
- Icon: Sun/Moon (lucide: `Sun`, `Moon` oder `SunMoon`)
- Klick wechselt zwischen Light/Dark

**Verhalten:**
- Theme in localStorage speichern (`theme: 'light' | 'dark'`)
- Beim Laden: System-Präferenz bevorzugen (`prefers-color-scheme`)
- Tailwind Dark Mode: `class` strategy (nicht `media`)

**Farben für Dark Mode:**
Die Tailwind-Farben müssen für Dark Mode angepasst werden:
```javascript
// tailwind.config.js - darkMode: 'class'
colors: {
  background: { DEFAULT: '#F2F2F7', dark: '#1C1C1E' },
  card: { DEFAULT: '#FFFFFF', dark: '#2C2C2E' },
  text: { DEFAULT: '#1C1C1E', dark: '#F2F2F7' },
  // usw.
}
```

### 3.4 App-Shell Anpassungen

**State Management:**
```typescript
// Neuer State in App.tsx oder AppShell
interface LayoutState {
  sidebarCollapsed: boolean;  // Desktop: eingeklappt?
  mobileMenuOpen: boolean;    // Mobile: Overlay sichtbar?
  theme: 'light' | 'dark';     // Aktuelles Theme
}
```

**Option A: Context API (empfohlen)**
- Neues `ThemeContext` für Dark Mode
- Neues `LayoutContext` für Sidebar-Zustand

**Option B: Props drilling (einfacher, aber weniger sauber)**
- State in App.tsx, durch AppShell an children

---

## 4. Technische Implementierung

### 4.1 Tailwind Config Anpassung

```javascript
// tailwind.config.js
export default {
  darkMode: 'class',  // NICHT 'media' - wir steuern manuell
  // ... restliche config
}
```

### 4.2 Breakpoints (Tailwind defaults)

| Breakpoint | Breite | Sidebar |
|------------|--------|---------|
| sm | < 640px | Hidden, Burger |
| md | 640-1024px | Hidden, Burger |
| lg | 1024-1280px | Visible (w-60) |
| xl | > 1280px | Visible (w-60) |

### 4.3 Benötigte Lucide Icons

- `Menu` - Burger-Button
- `X` - Schließen-Button (Overlay)
- `ChevronLeft` - Sidebar einklappen
- `ChevronRight` - Sidebar ausklappen
- `Sun` - Light Mode
- `Moon` - Dark Mode
- `SunMoon` - Toggle (alternativ)

### 4.4 Neue/Geänderte Dateien

1. **`tailwind.config.js`** - darkMode: 'class' hinzufügen
2. **`src/index.css`** - Dark Mode base styles
3. **`src/contexts/LayoutContext.tsx`** (NEU) - Sidebar + Theme State
4. **`src/contexts/ThemeContext.tsx`** (NEU) - Dark Mode Logic
5. **`src/components/layout/app-shell.tsx`** - Responsive + Context
6. **`src/components/layout/sidebar.tsx`** - Collapsible + Mobile Overlay
7. **`src/components/layout/header.tsx`** - Burger + Dark Toggle

---

## 5. Akzeptanzkriterien

### 5.1 Responsive
- [ ] **Desktop (>= 1024px):** Sidebar sichtbar, Toggle zum Einklappen vorhanden
- [ ] **Tablet (640-1024px):** Burger-Button sichtbar, Sidebar im Overlay
- [ ] **Mobile (< 640px):** Burger-Button sichtbar, Sidebar im Overlay, optimierte Touch-Targets

### 5.2 Sidebar Einklappen
- [ ] Klick auf Toggle-Button klappt Sidebar ein/aus
- [ ] Übergang ist smooth (300ms Animation)
- [ ] Nur Icons sichtbar wenn eingeklappt
- [ ] Zustand bleibt nach Page-Reload erhalten (localStorage)

### 5.3 Dark Mode
- [ ] Toggle-Button sichtbar in Header
- [ ] Klick wechselt Theme
- [ ] Farben wechseln korrekt (Background, Card, Text, Border)
- [ ] System-Präferenz wird beim ersten Besuch erkannt
- [ ] Zustand bleibt nach Page-Reload erhalten (localStorage)

### 5.4 Burger-Menü (Mobile)
- [ ] Klick öffnet Overlay mit Sidebar-Inhalten
- [ ] Klick außerhalb schließt Overlay
- [ ] Navigation zu neuer Seite schließt Overlay
- [ ] Overlay hat korrekte Animation (slide-in von links)

---

## 6. Abhängigkeiten

- **lucide-react:** Icons (bereits installiert)
- **tailwindcss:** CSS-Framework (bereits installiert)
- **tailwindcss-animate:** Animationen (bereits installiert)
- **react-router-dom:** Navigation (bereits installiert)
- **@tanstack/react-query:** Data Fetching (bereits installiert)

Keine neuen Dependencies nötig!

---

## 7. Offene Fragen

1. **Soll die Sidebar beim Einklappen komplett verschwinden oder Icons-only zeigen?**  
   → Empfehlung: Icons-only (`w-16`) für bessere UX

2. **Welche Breakpoints sollen verwendet werden?**  
   → Tailwind Defaults: sm=640px, md=768px, lg=1024px, xl=1280px

3. **Soll das Theme auch in einer Settings-Seite umgeschaltet werden können?**  
   → Aktuell nur Header-Toggle; später erweiterbar

4. **Sollen die Farben komplett invertiert werden oder angepasst (Apple-Dark)?**  
   → Apple-Dark: #1C1C1E (Background), #2C2C2E (Card)

---

## 8. Vorschlag zur Umsetzung

### Phase 1: Dark Mode (einfacher, isoliert)
1. `tailwind.config.js` anpassen
2. CSS Variables für Dark Mode
3. `ThemeContext` erstellen
4. Toggle in Header einbauen
5. Testen

### Phase 2: Responsive Sidebar
1. `LayoutContext` erstellen
2. Sidebar mit Breakpoints (lg: sichtbar, <lg: overlay)
3. Burger-Button in Header
4. Toggle für Einklappen (nur Desktop)

### Phase 3: Polish
1. localStorage Persistenz
2. Animationen verfeinern
3. Mobile Touch-Optimierung
4. Tooltips für eingeklappte Sidebar

---

*Ende der Spezifikation*
