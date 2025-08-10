# Datenbank-Erweiterung für Kegelmanager

Diese Dokumentation beschreibt die neue Funktionalität zur Erweiterung bestehender Datenbanken.

## Übersicht

Zusätzlich zur bestehenden Methode, eine komplett neue Datenbank mit `neue_DB.py` zu erstellen, gibt es jetzt eine zweite Variante:

**Erweiterung bestehender Datenbanken** - Sie können eine bereits existierende .db-Datei als Grundlage verwenden und fehlende Daten automatisch ergänzen lassen.

## Neue Dateien

### `extend_existing_db.py`
Hauptdatei für die Datenbank-Erweiterung. Kopiert eine bestehende Datenbank und ergänzt fehlende Daten.

**Funktionen:**
- `extend_existing_database()` - Hauptfunktion zur Datenbank-Erweiterung
- `analyze_existing_database()` - Analysiert vorhandene Daten
- `supplement_missing_data()` - Ergänzt fehlende Daten
- Hilfsfunktionen für Spielergenerierung (aus `init_db.py` übernommen)

### `create_test_db.py`
Erstellt eine Test-Datenbank mit nur Vereinen und Teams (ohne Spieler) zum Testen der Erweiterungsfunktion.

## Verwendung

### 1. Kommandozeile

```bash
# Erweitere eine bestehende Datenbank
python extend_existing_db.py <quell_db_pfad> <ziel_db_name>

# Beispiel:
python extend_existing_db.py "C:/path/to/existing.db" "meine_erweiterte_db"
```

### 2. API-Endpunkt

```http
POST /api/databases/extend
Content-Type: application/json

{
    "source_db_path": "C:/path/to/existing.db",
    "target_db_name": "meine_erweiterte_db"
}
```

### 3. Test-Datenbank erstellen

```bash
# Erstelle eine Test-Datenbank ohne Spieler
python create_test_db.py test_base

# Erweitere die Test-Datenbank
python extend_existing_db.py instance/test_base.db test_extended
```

## Was wird ergänzt?

Die Erweiterungsfunktion analysiert die bestehende Datenbank und ergänzt automatisch:

### 1. Saison
- Falls keine Saison vorhanden ist, wird eine neue erstellt
- Name: "Season 2025"
- Zeitraum: August 2025 - Mai 2026

### 2. Spieler
- **Für Teams ohne Spieler** werden automatisch Spieler generiert
- **Für bestehende Spieler mit unvollständigen Attributen** werden fehlende Werte ergänzt
- Anzahl basiert auf Liga-Level:
  - Level 1-4: 8-10 Spieler
  - Level 5-8: 7-9 Spieler
  - Level 9+: 7-8 Spieler
- Spielerstärke basiert auf Team-Stärke und Liga-Level
- Namen werden aus Excel-Dateien geladen (Fallback bei Fehlern)

#### Ergänzung unvollständiger Spielerattribute (NEU!)
Das System erkennt automatisch Spieler mit fehlenden oder leeren Attributen und ergänzt:
- **Grundattribute**: Alter (20-35), Talent (1-10), Position (Kegler/Allrounder/Spezialist), Gehalt, Vertragsende
- **Kegel-Attribute**: Ausdauer, Konstanz, Drucksicherheit, Volle, Räumer, Sicherheit, Auswärts, Start, Mitte, Schluss
- **Berechnung**: Alle Kegel-Attribute werden basierend auf der bestehenden Spielerstärke berechnet (±10 Punkte Variation)
- **Liga-abhängig**: Gehalt wird basierend auf Spielerstärke und Liga-Level berechnet

### 3. Finanzen
- Für Vereine ohne Finanzdaten werden Startfinanzen erstellt
- Zufällige Werte für Kontostand, Einnahmen und Ausgaben

### 4. Bahnqualität
- Aktualisierung der Bahnqualität basierend auf dem besten Team des Vereins
- Höhere Ligen = bessere Bahnqualität

## Vorhandene Daten

**Werden NICHT überschrieben:**
- Bestehende Spieler
- Bestehende Finanzdaten
- Bestehende Saisons
- Bestehende Vereine und Teams

**Werden nur ergänzt:**
- Fehlende Spieler für Teams
- Fehlende Attribute für bestehende Spieler
- Fehlende Finanzdaten für Vereine
- Fehlende Saison (falls keine vorhanden)

## Analyse-Funktion

Die `analyze_existing_database()` Funktion gibt detaillierte Informationen über die Datenbank:

```python
{
    "has_season": True/False,
    "has_leagues": True/False,
    "has_clubs": True/False,
    "has_teams": True/False,
    "has_players": True/False,
    "has_finances": True/False,
    "season_count": 1,
    "league_count": 5,
    "club_count": 8,
    "team_count": 12,
    "player_count": 0,
    "teams_without_players": [1, 2, 3, ...],
    "clubs_without_finances": [1, 2, ...],
    "clubs_without_teams": [],
    "players_with_incomplete_attributes": [
        {
            "player_id": 1,
            "player_name": "Max Mustermann",
            "club_id": 1,
            "missing_attributes": ["age", "talent", "position", ...]
        }
    ]
}
```

## Integration in bestehende Struktur

### API-Erweiterung
- Neue Route: `/api/databases/extend`
- Import in `app.py`: `import extend_existing_db`
- Neue Funktion in `db_manager.py`: `extend_existing_database()`

### Fehlerbehandlung
- Überprüfung der Quell-Datenbank
- Überprüfung auf bereits existierende Ziel-Datenbank
- Automatisches Löschen bei Fehlern
- Detaillierte Fehlermeldungen

## Anwendungsfälle

1. **Bestehende Datenbank ohne Spieler** - Sie haben Vereine und Teams, aber keine Spieler
2. **Unvollständige Datenbank** - Einige Teams haben Spieler, andere nicht
3. **Spieler mit unvollständigen Attributen** - Spieler haben nur Name, Stärke und Verein (wie in RealeDB)
4. **Migration** - Übertragung von Daten aus anderen Systemen
5. **Test-Szenarien** - Schnelle Erstellung von Test-Datenbanken

### Beispiel: RealeDB erweitern

```bash
# Analysiere die RealeDB
python test_extend_db.py

# Erweitere die RealeDB mit vollständigen Spielerattributen
python extend_existing_db.py Datenbanken/RealeDB.db RealeDB_Extended
```

Die RealeDB enthält 93 Spieler mit nur Name, Stärke und Vereinszugehörigkeit. Nach der Erweiterung haben alle Spieler vollständige Attribute für das Bowling-Spiel.

## Abhängigkeiten

- Alle bestehenden Abhängigkeiten von `init_db.py`
- Excel-Dateien für Namen (optional, Fallback vorhanden):
  - `Vornamen.xls`
  - `Nachnamen.xls`
- SQLAlchemy Models
- Flask für Datenbank-Kontext
