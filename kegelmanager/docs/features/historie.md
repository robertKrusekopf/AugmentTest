# Liga-Historie Feature

Dieses Feature fügt einen neuen "Historie" Tab zu den Liga-Seiten hinzu, der die Endtabellen vergangener Saisons anzeigt.

## Implementierte Änderungen

### 1. Datenmodell (Backend)

**Neue Tabelle: `LeagueHistory`**
- Speichert die Endtabellen aller Ligen für jede abgeschlossene Saison
- Enthält alle relevanten Statistiken (Position, Spiele, Siege, Unentschieden, Niederlagen, Punkte, etc.)
- Verknüpft mit Saison-Daten für einfache Abfragen

**Datei:** `kegelmanager/backend/models.py`
- Neue Klasse `LeagueHistory` hinzugefügt
- Vollständige Tabellenstruktur mit allen Bowling-relevanten Statistiken

### 2. Saisonwechsel-Logik (Backend)

**Automatische Speicherung der Endtabellen**
- Beim Saisonwechsel werden automatisch die finalen Tabellenstände gespeichert
- Neue Funktion `save_league_history()` in `simulation.py`
- Integration in den bestehenden `process_end_of_season()` Workflow

**Dateien:**
- `kegelmanager/backend/simulation.py` - Erweiterte Saisonwechsel-Logik

### 3. API-Endpunkte (Backend)

**Neue REST-Endpunkte:**
- `GET /api/leagues/<id>/history` - Alle historischen Daten einer Liga
- `GET /api/leagues/<id>/history/<season_id>` - Spezifische Saison einer Liga

**Datei:** `kegelmanager/backend/app.py`
- Zwei neue API-Endpunkte für Liga-Historie

### 4. Frontend-Services

**Erweiterte API-Services:**
- `getLeagueHistory(id)` - Lädt alle historischen Daten
- `getLeagueHistorySeason(leagueId, seasonId)` - Lädt spezifische Saison

**Datei:** `kegelmanager/frontend/src/services/api.js`

### 5. Frontend-Komponenten

**Liga-Seiten mit Historie-Tab:**
- Neuer "Historie" Tab neben Tabelle, Spielplan, Statistiken, Teams
- Dropdown-Menü zur Saisonauswahl
- Vollständige Endtabellen-Anzeige mit allen Statistiken
- Responsive Design für mobile Geräte

**Dateien:**
- `kegelmanager/frontend/src/pages/Leagues.jsx` - Hauptseite erweitert
- `kegelmanager/frontend/src/pages/LeagueDetail.jsx` - Detailseite erweitert
- `kegelmanager/frontend/src/pages/Leagues.css` - Styling hinzugefügt
- `kegelmanager/frontend/src/pages/LeagueDetail.css` - Styling hinzugefügt

## Installation und Setup

### 1. Datenbank-Migration

Für bestehende Datenbanken muss die neue Tabelle erstellt werden:

```bash
cd kegelmanager/backend
python migrate_league_history.py
```

### 2. Backend-Neustart

Nach den Änderungen sollte das Backend neu gestartet werden:

```bash
cd kegelmanager/backend
python app.py
```

### 3. Frontend-Neustart

Das Frontend sollte automatisch die Änderungen erkennen:

```bash
cd kegelmanager/frontend
npm start
```

## Funktionsweise

### Automatische Datenspeicherung

1. **Während der Saison:** Normale Spielsimulation ohne Änderungen
2. **Saisonende:** Beim Klick auf "Saisonwechsel" werden automatisch die Endtabellen gespeichert
3. **Neue Saison:** Die gespeicherten Daten sind sofort im Historie-Tab verfügbar

### Benutzeroberfläche

1. **Liga auswählen:** Normale Liga-Auswahl über Dropdown
2. **Historie-Tab:** Neuer Tab neben den bestehenden Tabs
3. **Saison auswählen:** Dropdown-Menü mit allen verfügbaren Saisons
4. **Tabelle anzeigen:** Vollständige Endtabelle mit allen Statistiken

### Datenstruktur

Die Historie-Daten enthalten:
- **Grunddaten:** Liga-Name, Level, Saison
- **Team-Info:** Name, Verein, Wappen
- **Tabellenplatz:** Finale Position
- **Spielstatistiken:** Spiele, Siege, Unentschieden, Niederlagen
- **Punkte:** Tabellenpunkte, Mannschaftspunkte
- **Bowling-Statistiken:** Holz für/gegen, Heim-/Auswärtsschnitt

## Technische Details

### Datenbank-Schema

```sql
CREATE TABLE league_history (
    id INTEGER PRIMARY KEY,
    league_name VARCHAR(100) NOT NULL,
    league_level INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    season_name VARCHAR(100) NOT NULL,
    team_id INTEGER NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    club_name VARCHAR(100),
    club_id INTEGER,
    verein_id INTEGER,
    position INTEGER NOT NULL,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    table_points INTEGER DEFAULT 0,
    match_points_for INTEGER DEFAULT 0,
    match_points_against INTEGER DEFAULT 0,
    pins_for INTEGER DEFAULT 0,
    pins_against INTEGER DEFAULT 0,
    avg_home_score FLOAT DEFAULT 0.0,
    avg_away_score FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### API-Antwortformat

```json
{
  "league_name": "Bundesliga Nord",
  "league_level": 1,
  "seasons": [
    {
      "season_id": 2,
      "season_name": "Season 2",
      "standings": [
        {
          "position": 1,
          "team_name": "Team A",
          "club_name": "Verein A",
          "emblem_url": "/api/club-emblem/123",
          "games_played": 22,
          "wins": 18,
          "draws": 2,
          "losses": 2,
          "table_points": 56,
          "avg_home_score": 650.5,
          "avg_away_score": 620.3
        }
      ]
    }
  ]
}
```

## Zukünftige Erweiterungen

- **Statistik-Vergleiche:** Vergleich zwischen verschiedenen Saisons
- **Export-Funktionen:** CSV/PDF-Export der historischen Tabellen
- **Grafische Darstellung:** Charts für Entwicklung über mehrere Saisons
- **Erweiterte Filter:** Filter nach Zeiträumen, Teams, etc.
