# Nachrichten-System

## Übersicht

Das Nachrichten-System ist ein integriertes Benachrichtigungssystem im Kegelmanager, das wie ein E-Mail-Programm (z.B. Outlook) aufgebaut ist.

## Features

### Benutzeroberfläche

- **Zwei-Spalten-Layout**: 
  - Links: Liste aller Nachrichten, sortiert nach Datum (neueste zuerst)
  - Rechts: Detailansicht der ausgewählten Nachricht

- **Nachrichtenliste**:
  - Zeigt Betreff, Vorschau und Datum
  - Ungelesene Nachrichten sind hervorgehoben
  - Filterung nach: Alle, Ungelesen, Gelesen
  - Visueller Indikator für Nachrichtentyp (Info, Erfolg, Warnung, Fehler)

- **Nachrichtendetails**:
  - Vollständiger Nachrichteninhalt
  - Nachrichtentyp-Badge
  - Aktionen: Als gelesen/ungelesen markieren, Löschen
  - Zeitstempel mit relativer Zeitanzeige

### Nachrichtentypen

1. **Info** (blau): Allgemeine Informationen
2. **Erfolg** (grün): Positive Ereignisse (z.B. Siege, erfolgreiche Transfers)
3. **Warnung** (orange): Wichtige Hinweise (z.B. auslaufende Verträge, niedrige Finanzen)
4. **Fehler** (rot): Kritische Probleme

### Funktionen

- ✅ Nachrichten lesen
- ✅ Als gelesen/ungelesen markieren
- ✅ Nachrichten löschen
- ✅ Alle Nachrichten als gelesen markieren
- ✅ Filterung nach Lesestatus
- ✅ Verknüpfung mit Spielentitäten (Vereine, Teams, Spieler, Spiele)

## Technische Details

### Backend

**Datenbank-Modell** (`models.py`):
```python
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Optional: Verknüpfungen zu anderen Entitäten
    related_club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=True)
    related_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    related_player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    related_match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=True)
```

**API-Endpunkte** (`app.py`):
- `GET /api/messages` - Alle Nachrichten abrufen (optional gefiltert nach Lesestatus)
- `GET /api/messages/<id>` - Einzelne Nachricht abrufen
- `PUT /api/messages/<id>/mark-read` - Als gelesen markieren
- `PUT /api/messages/<id>/mark-unread` - Als ungelesen markieren
- `DELETE /api/messages/<id>` - Nachricht löschen
- `PUT /api/messages/mark-all-read` - Alle als gelesen markieren
- `GET /api/messages/unread-count` - Anzahl ungelesener Nachrichten

### Frontend

**Komponenten**:
- `Messages.jsx` - Hauptkomponente für die Nachrichtenseite
- `Messages.css` - Styling im Outlook-Stil

**API-Integration** (`api.js`):
- `getMessages(isRead)` - Nachrichten abrufen
- `getMessage(id)` - Einzelne Nachricht abrufen
- `markMessageRead(id)` - Als gelesen markieren
- `markMessageUnread(id)` - Als ungelesen markieren
- `deleteMessage(id)` - Nachricht löschen
- `markAllMessagesRead()` - Alle als gelesen markieren
- `getUnreadMessageCount()` - Anzahl ungelesener Nachrichten

**Navigation**:
- Menüeintrag "Nachrichten" zwischen "Dashboard" und "Verein"
- Route: `/messages`

## Migration

Die Message-Tabelle wurde mit dem Migrationsskript `migrate_add_messages.py` zu bestehenden Datenbanken hinzugefügt.

**Migration ausführen**:
```bash
cd kegelmanager/backend
python migrate_add_messages.py
```

## Beispiel-Nachrichten erstellen

Für Testzwecke können Beispiel-Nachrichten erstellt werden:

```bash
cd kegelmanager/backend
python create_sample_messages.py
```

Das Skript erstellt 7 Beispiel-Nachrichten verschiedener Typen.

## Zukünftige Erweiterungen

Mögliche Erweiterungen für das Nachrichten-System:

1. **Automatische Benachrichtigungen**:
   - Nach Spielen (Ergebnisse, besondere Leistungen)
   - Bei Transferangeboten
   - Bei Vertragsverlängerungen
   - Bei Verletzungen
   - Bei finanziellen Ereignissen

2. **Kategorien/Tags**:
   - Nachrichten nach Kategorien filtern
   - Wichtige Nachrichten markieren

3. **Archivierung**:
   - Alte Nachrichten automatisch archivieren
   - Archiv-Ansicht

4. **Benachrichtigungs-Badge**:
   - Anzahl ungelesener Nachrichten im Menü anzeigen
   - Desktop-Benachrichtigungen (optional)

5. **Suchfunktion**:
   - Nachrichten durchsuchen
   - Nach Datum filtern

6. **Anhänge**:
   - Verknüpfungen zu relevanten Seiten (z.B. direkt zum Spieler-Profil)
   - Schnellaktionen aus Nachrichten heraus

## Verwendung im Spiel

Das Nachrichten-System kann verwendet werden, um Spieler über wichtige Ereignisse zu informieren:

### Beispiel: Nachricht nach einem Spiel erstellen

```python
from models import db, Message, Match

# Nach der Spielsimulation
match = Match.query.get(match_id)

if match.home_score > match.away_score:
    message = Message(
        subject=f"Sieg gegen {match.away_team.name}!",
        content=f"Glückwunsch! Ihre Mannschaft {match.home_team.name} hat mit {match.home_score}:{match.away_score} gegen {match.away_team.name} gewonnen!",
        message_type='success',
        related_match_id=match.id,
        related_team_id=match.home_team_id
    )
    db.session.add(message)
    db.session.commit()
```

### Beispiel: Warnung bei niedrigem Kontostand

```python
from models import db, Message, Club

club = Club.query.get(club_id)

if club.balance < 10000:
    message = Message(
        subject="Warnung: Niedriger Kontostand",
        content=f"Der Kontostand Ihres Vereins beträgt nur noch €{club.balance:,.2f}. Achten Sie auf Ihre Ausgaben!",
        message_type='warning',
        related_club_id=club.id
    )
    db.session.add(message)
    db.session.commit()
```

## Design-Entscheidungen

1. **Outlook-ähnliches Layout**: Vertrautes Design für Benutzer
2. **Einfache Bedienung**: Klare Aktionen und Filteroptionen
3. **Responsive Design**: Funktioniert auf verschiedenen Bildschirmgrößen
4. **Visuelle Hierarchie**: Ungelesene Nachrichten sind deutlich erkennbar
5. **Nachrichtentypen**: Farbcodierung für schnelle Erkennung der Wichtigkeit

