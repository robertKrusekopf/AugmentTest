# Spieler Form-System

Das Form-System fügt eine dynamische Komponente zur Spielerleistung hinzu, die deren Performance während Spielen beeinflusst. Spieler können sich in unterschiedlichen Phasen befinden, die ihre Grundstärke temporär modifizieren.

## Übersicht

Das Form-System besteht aus drei verschiedenen Arten von Formmodifikatoren:

### 1. Kurzfristige Form (Short-term Form)
- **Bereich**: -20 bis +20 Punkte
- **Dauer**: 1-3 Spieltage
- **Wahrscheinlichkeit**: 15% pro Spieltag
- **Beschreibung**: Repräsentiert tagesaktuelle Verfassung, Motivation oder kleine Verletzungen

### 2. Mittelfristige Form (Medium-term Form)
- **Bereich**: -15 bis +15 Punkte
- **Dauer**: 4-8 Spieltage
- **Wahrscheinlichkeit**: 8% pro Spieltag
- **Beschreibung**: Repräsentiert wöchentliche Trends, Trainingseffekte oder leichte Formkrisen

### 3. Langfristige Form (Long-term Form)
- **Bereich**: -10 bis +10 Punkte
- **Dauer**: 10-20 Spieltage
- **Wahrscheinlichkeit**: 4% pro Spieltag
- **Beschreibung**: Repräsentiert saisonale Entwicklung, Alterung oder langfristige Verletzungen

## Funktionsweise

### Form-Generierung
- Formmodifikatoren werden zufällig generiert basierend auf Wahrscheinlichkeiten
- Jeder Modifikator hat eine bestimmte Dauer in Spieltagen
- Mehrere Formmodifikatoren können gleichzeitig aktiv sein

### Form-Updates
- Bei jedem Spieltag werden die verbleibenden Tage aller aktiven Formmodifikatoren reduziert
- Abgelaufene Formmodifikatoren werden auf 0 zurückgesetzt
- Neue Formmodifikatoren können mit den angegebenen Wahrscheinlichkeiten generiert werden

### Anwendung auf Spielerstärke
- Die Gesamtform wird als Summe aller aktiven Formmodifikatoren berechnet
- Die effektive Spielerstärke = Grundstärke + Gesamtform
- Die effektive Stärke wird auf den Bereich 1-99 begrenzt

## Datenbank-Schema

Das Form-System fügt folgende Felder zur `Player`-Tabelle hinzu:

```sql
-- Form-Modifikatoren
form_short_term REAL DEFAULT 0.0
form_medium_term REAL DEFAULT 0.0  
form_long_term REAL DEFAULT 0.0

-- Verbleibende Tage
form_short_remaining_days INTEGER DEFAULT 0
form_medium_remaining_days INTEGER DEFAULT 0
form_long_remaining_days INTEGER DEFAULT 0
```

## API-Integration

### Backend (models.py)
- Neue Felder im `Player`-Model
- Erweiterte `to_dict()`-Methode für API-Ausgabe

### Backend (app.py)
- Erweiterte `update_player()`-Funktion für Cheat-Modus
- Unterstützung für Form-Feld-Updates

### Frontend (PlayerDetail.jsx)
- Neue Form-Felder im Cheat-Menü
- Anzeige aller Form-Modifikatoren und verbleibenden Tage

## Simulation-Integration

### Spieler-Rating
- Die `player_rating()`-Funktion berücksichtigt jetzt die effektive Stärke (inklusive Form)
- Bessere Spielerauswahl basierend auf aktueller Form

### Match-Simulation
- Form-Modifikatoren werden bei der Berechnung der Spielerleistung angewendet
- Sowohl Heim- als auch Auswärtsspieler profitieren/leiden von ihrer aktuellen Form

### Spieltag-Simulation
- Form-Updates werden automatisch am Anfang jedes Spieltags durchgeführt
- Alle Spieler erhalten potentielle Form-Änderungen

## Verwendung

### Migration ausführen
```bash
cd kegelmanager/backend
python migrate_form_system.py
```

### Tests ausführen
```bash
cd kegelmanager/backend
python test_form_system.py
```

### Form-System zurücksetzen
```python
from form_system import reset_all_player_forms
reset_count = reset_all_player_forms()
print(f"Form für {reset_count} Spieler zurückgesetzt")
```

### Manuelle Form-Initialisierung
```python
from form_system import initialize_random_form_for_player
from models import Player

player = Player.query.get(player_id)
initialize_random_form_for_player(player)
db.session.commit()
```

## Cheat-Modus

Im Cheat-Menü der Spielerdetailseite können alle Form-Attribute manuell bearbeitet werden:

- **Kurzfristige Form**: -20 bis +20
- **Mittelfristige Form**: -15 bis +15  
- **Langfristige Form**: -10 bis +10
- **Verbleibende Tage**: Für jeden Form-Typ separat einstellbar

## Form-Status-Anzeige

Das System generiert automatisch lesbare Form-Zusammenfassungen:

- **Ausgezeichnet**: Gesamtmodifikator > +10
- **Sehr gut**: Gesamtmodifikator > +5
- **Gut**: Gesamtmodifikator > 0
- **Normal**: Gesamtmodifikator = 0
- **Schwach**: Gesamtmodifikator > -5
- **Schlecht**: Gesamtmodifikator > -10
- **Sehr schlecht**: Gesamtmodifikator ≤ -10

## Technische Details

### Performance-Optimierungen
- Bulk-Updates für alle Spieler gleichzeitig
- Effiziente Datenbankabfragen
- Minimale Auswirkung auf Simulationsgeschwindigkeit

### Sicherheit
- Form-Modifikatoren sind nur im Cheat-Modus sichtbar
- Automatische Validierung der Wertebereiche
- Sichere Datenbankoperationen mit Rollback-Unterstützung

### Erweiterbarkeit
- Modularer Aufbau für einfache Anpassungen
- Konfigurierbare Wahrscheinlichkeiten und Bereiche
- Einfache Integration neuer Form-Typen möglich
