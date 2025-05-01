# Kegelmanager - Simulationsspiel

Ein Simulationsspiel ähnlich dem Football Manager, aber für Kegeln. Vereine haben mehrere Mannschaften, die in verschiedenen Ligen spielen. Die Ergebnisse der Spiele werden simuliert. Nach einer Saison steigen Vereine auf und ab.

## Funktionen

- Verwaltung von Vereinen mit mehreren Mannschaften
- Spielersystem mit Attributen wie Alter, Stärke (1-99) und Talent (1-10)
- Spielsimulation basierend auf Spielerstärken
- Jugendentwicklung und Talentförderung
- Transfersystem für Spieler
- Finanzmanagement
- Umfangreiche Statistiken

## Technologien

- **Backend**: Python mit Flask und SQLAlchemy
- **Frontend**: React mit Vite
- **Datenbank**: SQLite

## Installation und Start

### Voraussetzungen

- Python 3.8 oder höher
- Node.js 14 oder höher
- npm oder yarn

### Backend

```bash
# Wechseln ins Backend-Verzeichnis
cd kegelmanager/backend

# Virtuelle Umgebung erstellen (optional, aber empfohlen)
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank initialisieren mit Beispieldaten
python init_db.py --sample

# Server starten
python app.py
```

Der Backend-Server läuft dann auf http://localhost:5000.

### Frontend

```bash
# Wechseln ins Frontend-Verzeichnis
cd kegelmanager/frontend

# Abhängigkeiten installieren
npm install

# Entwicklungsserver starten
npm run dev
```

Das Frontend ist dann unter http://localhost:5173 erreichbar.

### Schnellstart

Alternativ kann das gesamte Projekt mit einem Befehl gestartet werden:

```bash
# Im Hauptverzeichnis des Projekts
python start.py
```

## Projektstruktur

```
kegelmanager/
├── backend/
│   ├── app.py              # Flask-Anwendung und API-Endpunkte
│   ├── models.py           # Datenbankmodelle
│   ├── simulation.py       # Spielsimulation und Logik
│   ├── init_db.py          # Datenbankinitialisierung
│   └── requirements.txt    # Python-Abhängigkeiten
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Wiederverwendbare UI-Komponenten
│   │   ├── pages/          # Seitenkomponenten
│   │   ├── services/       # API-Dienste
│   │   ├── assets/         # Bilder und andere Assets
│   │   ├── App.jsx         # Hauptanwendungskomponente
│   │   └── main.jsx        # Einstiegspunkt
│   ├── index.html
│   └── package.json
│
└── start.py                # Skript zum Starten des gesamten Projekts
```

## Spielmechanik

- **Spielerstärke**: Bestimmt, wie gut ein Spieler in einem Spiel ist (1-99)
- **Spielertalent**: Bestimmt, wie schnell ein Spieler durch Training und Spielzeit besser wird (1-10)
- **Spielsimulation**: Basiert auf der durchschnittlichen Stärke der Mannschaft mit Zufallsfaktoren
- **Spielerentwicklung**: Jüngere Spieler entwickeln sich schneller, besonders talentierte Spieler haben ein höheres Potenzial
- **Auf-/Abstieg**: Nach jeder Saison steigen die besten Teams auf und die schlechtesten ab

## Hauptfunktionen

### Dashboard
Übersicht über den aktuellen Stand des Vereins, Tabellen, anstehende Spiele und Top-Spieler.

### Vereine
Verwaltung und Übersicht aller Vereine im Spiel.

### Mannschaften
Detaillierte Ansicht und Verwaltung der Mannschaften.

### Spieler
Spielerprofile mit Attributen, Entwicklung und Statistiken.

### Ligen
Tabellenansicht, Spielpläne und Statistiken für alle Ligen.

### Jugendentwicklung
Verwaltung der Jugendakademie, Talentförderung und Nachwuchsmannschaften.

### Transfers
Transfermarkt, Angebote und Verhandlungen für Spieler.

### Finanzen
Finanzübersicht, Einnahmen, Ausgaben und Budgetplanung.

## Lizenz

MIT
