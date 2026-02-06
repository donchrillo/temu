# Zentrale Navigation System

## Überblick

Alle Seiten (Dashboard, TEMU, PDF, CSV) nutzen jetzt eine **zentrale Navigation-Komponente**, die automatisch geladen wird.

## Komponenten

### 1. Navigation HTML
**Datei:** `frontend/components/navigation.html`
- Enthält das Burger-Menü mit allen Links
- Alle Menüpunkte werden hier zentral gepflegt

### 2. Navigation Loader
**Datei:** `frontend/components/nav-loader.js`
- Lädt die Navigation dynamisch
- Funktionen: `toggleMenu()`, `setActiveMenuItem()`, `setNavTitle()`

### 3. Progress Helper
**Datei:** `frontend/components/progress-helper.js`
- Funktionen für animierte Progress-Anzeige
- `showProgress(text, percent)` - Zeigt Progress-Overlay
- `updateProgress(percent)` - Update Prozent (0-100)
- `updateProgressText(text)` - Update Text
- `hideProgress()` - Versteckt Overlay

## Integration in neue Seiten

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Meine Seite</title>
    <link rel="stylesheet" href="/static/meine-seite.css">
</head>
<body>
    <!-- Navigation wird automatisch geladen -->
    <script src="/components/nav-loader.js"></script>
    <script>loadNavigation('page-key', '🎯 Titel der Seite');</script>

    <div class="container">
        <!-- Dein Content -->
    </div>

    <!-- Optional: Progress-Overlay -->
    <div id="progress-overlay" class="progress-overlay">
        <div class="progress-container">
            <div class="progress-icon">⚙️</div>
            <div class="progress-text" id="progress-text">Verarbeite...</div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div class="progress-percent" id="progress-percent">0%</div>
        </div>
    </div>

    <!-- Optional: Progress Helper -->
    <script src="/components/progress-helper.js"></script>
    <script src="/static/meine-seite.js"></script>
</body>
</html>
```

## CSS Requirements

Jedes Modul muss folgende CSS-Klassen definieren:

```css
/* Burger Menu Styles */
.mobile-nav { }
.mobile-nav-header { }
.burger-toggle { }
.mobile-menu { }
.menu-item { }

/* Progress Overlay (optional) */
.progress-overlay { }
.progress-container { }
.progress-icon { }
.progress-text { }
.progress-bar { }
.progress-fill { }
.progress-percent { }
```

Oder: Von TEMU/PDF CSS kopieren (bereits implementiert in allen Modulen).

## Burger-Menü auf allen Geräten

Das Burger-Menü ist jetzt **auf allen Geräten** aktiv (Desktop, Tablet, Mobile).

CSS Media Query:
```css
/* Desktop & Mobile: Burger immer anzeigen */
@media (min-width: 769px) {
    .burger-toggle {
        display: flex;
    }

    .mobile-menu {
        display: none;
    }

    .mobile-menu.active {
        display: flex;
    }
}
```

## Neue Seite zum Menü hinzufügen

1. **Navigation HTML bearbeiten:**
   - Öffne: `frontend/components/navigation.html`
   - Füge neuen Link hinzu:
   ```html
   <a href="/neue-seite" class="menu-item" data-page="neue-seite">🎯 Neue Seite</a>
   ```

2. **Route in main.py:**
   ```python
   @app.get("/neue-seite")
   async def neue_seite_ui():
       html = Path(__file__).parent / "modules" / "neue_seite" / "frontend" / "index.html"
       return FileResponse(str(html))
   ```

3. **Static Files (CSS/JS):**
   ```python
   # In main.py @app.get("/static/{filename}")
   if filename.startswith('neue-seite.'):
       file = base_dir / "modules" / "neue_seite" / "frontend" / filename.replace('neue-seite.', '', 1)
   ```

4. **HTML Integration:**
   ```html
   <script src="/components/nav-loader.js"></script>
   <script>loadNavigation('neue-seite', '🎯 Neue Seite');</script>
   ```

## Button Styles

### Standard Buttons
```html
<button class="btn-primary">📁 Primary Action</button>
<button class="btn-secondary">⚙️ Secondary Action</button>
<button class="btn-success">💾 Download / Save</button>
<button class="btn-danger">🗑️ Delete / Clean</button>
```

### CSS
```css
.btn-primary   { background: #007AFF; }  /* Blau */
.btn-secondary { background: #8E8E93; }  /* Grau */
.btn-success   { background: #34C759; }  /* Grün */
.btn-danger    { background: #FF3B30; }  /* Rot */
```

## Vorteile

✅ **Zentral:** Ein Menü für alle Seiten  
✅ **Einfach:** Neue Seiten in 1 Datei hinzufügen  
✅ **Konsistent:** Gleiches Look & Feel überall  
✅ **Wartbar:** Änderungen nur an einer Stelle  
✅ **Modern:** Burger-Menü auf allen Geräten  
✅ **Animiert:** Progress-Overlay für bessere UX
