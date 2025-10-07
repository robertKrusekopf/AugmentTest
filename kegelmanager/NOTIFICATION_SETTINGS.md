# Benachrichtigungseinstellungen (Notification Settings)

## Übersicht

Das Benachrichtigungseinstellungs-System ermöglicht es Benutzern, zu konfigurieren, welche Arten von Benachrichtigungen sie im Nachrichten-System erhalten möchten. Deaktivierte Benachrichtigungstypen werden nicht in der Nachrichtenliste angezeigt.

## Features

### Benutzeroberfläche

- **Einstellungen-Button**: In der Nachrichten-Seite gibt es einen "Einstellungen"-Button, der ein Modal-Fenster öffnet
- **Kategorien-Übersicht**: Alle verfügbaren Benachrichtigungskategorien werden mit Namen und Beschreibung angezeigt
- **Toggle-Checkboxen**: Jede Kategorie kann einzeln aktiviert/deaktiviert werden
- **Schnellaktionen**: "Alle auswählen" und "Alle abwählen" Buttons für schnelle Konfiguration
- **Persistenz**: Einstellungen werden in der Datenbank gespeichert und bleiben über Sitzungen hinweg erhalten

### Benachrichtigungskategorien

1. **Spieler-Ruhestand** (`player_retirement`)
   - Benachrichtigungen wenn Spieler in den Ruhestand gehen
   - Nur für Spieler des Manager-Vereins

2. **Transfers** (`transfers`)
   - Benachrichtigungen über Transferangebote und -abschlüsse
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

3. **Spielergebnisse** (`match_results`)
   - Benachrichtigungen über Spielergebnisse und besondere Leistungen
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

4. **Verletzungen** (`injuries`)
   - Benachrichtigungen über Spielerverletzungen
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

5. **Verträge** (`contracts`)
   - Benachrichtigungen über auslaufende Verträge und Vertragsverlängerungen
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

6. **Finanzen** (`finances`)
   - Benachrichtigungen über finanzielle Ereignisse und Warnungen
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

7. **Erfolge** (`achievements`)
   - Benachrichtigungen über Erfolge, Rekorde und Meilensteine
   - (Noch nicht implementiert - für zukünftige Erweiterungen)

8. **Allgemein** (`general`)
   - Allgemeine Informationen und sonstige Benachrichtigungen

## Technische Details

### Backend

**Datenbank-Modelle** (`models.py`):

```python
class Message(db.Model):
    # ... existing fields ...
    notification_category = db.Column(db.String(50), default='general', index=True)
    # ...

class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_retirement = db.Column(db.Boolean, default=True)
    transfers = db.Column(db.Boolean, default=True)
    match_results = db.Column(db.Boolean, default=True)
    injuries = db.Column(db.Boolean, default=True)
    contracts = db.Column(db.Boolean, default=True)
    finances = db.Column(db.Boolean, default=True)
    achievements = db.Column(db.Boolean, default=True)
    general = db.Column(db.Boolean, default=True)
    # ...
```

**API-Endpunkte** (`app.py`):
- `GET /api/notification-settings` - Benachrichtigungseinstellungen abrufen
- `PUT /api/notification-settings` - Benachrichtigungseinstellungen aktualisieren
- `GET /api/notification-settings/categories` - Verfügbare Kategorien mit Beschreibungen abrufen
- `GET /api/messages` - Nachrichten abrufen (gefiltert nach Einstellungen)

**Filterlogik**:
Die `get_messages` API-Endpunkt filtert automatisch Nachrichten basierend auf den Benutzereinstellungen. Nur Nachrichten mit aktivierten Kategorien werden zurückgegeben.

### Frontend

**Komponenten**:
- `NotificationSettingsModal.jsx` - Modal-Komponente für Einstellungen
- `NotificationSettingsModal.css` - Styling für das Modal
- `Messages.jsx` - Aktualisiert mit Einstellungen-Button und Modal-Integration

**API-Integration** (`api.js`):
- `getNotificationSettings()` - Einstellungen abrufen
- `updateNotificationSettings(settings)` - Einstellungen aktualisieren
- `getNotificationCategories()` - Kategorien abrufen

## Migration

Die Notification Settings wurden mit dem Migrationsskript `migrate_add_notification_settings.py` zu bestehenden Datenbanken hinzugefügt.

**Migration ausführen**:
```bash
cd kegelmanager/backend
python migrate_add_notification_settings.py
```

Das Skript:
1. Fügt `notification_category` Spalte zur Message-Tabelle hinzu
2. Erstellt die NotificationSettings-Tabelle
3. Setzt Standard-Kategorien für bestehende Nachrichten
4. Erstellt Standard-Einstellungen (alle Kategorien aktiviert)

## Verwendung im Code

### Nachricht mit Kategorie erstellen

```python
from models import db, Message

message = Message(
    subject="Spieler geht in den Ruhestand",
    content="...",
    message_type='info',
    notification_category='player_retirement',  # Kategorie setzen
    related_player_id=player.id
)
db.session.add(message)
db.session.commit()
```

### Neue Benachrichtigungskategorie hinzufügen

Um eine neue Benachrichtigungskategorie hinzuzufügen:

1. **Backend - models.py**: Füge ein neues Boolean-Feld zur `NotificationSettings` Klasse hinzu
   ```python
   new_category = db.Column(db.Boolean, default=True)
   ```

2. **Backend - models.py**: Aktualisiere die `to_dict()` Methode
   ```python
   'new_category': self.new_category,
   ```

3. **Backend - app.py**: Füge die Kategorie zur `update_notification_settings` Funktion hinzu
   ```python
   if 'new_category' in data:
       settings.new_category = data['new_category']
   ```

4. **Backend - app.py**: Füge die Kategorie zur `get_notification_categories` Liste hinzu
   ```python
   {
       'id': 'new_category',
       'name': 'Neue Kategorie',
       'description': 'Beschreibung der neuen Kategorie'
   }
   ```

5. **Migration**: Erstelle ein Migrationsskript, um die neue Spalte zu bestehenden Datenbanken hinzuzufügen

6. **Code**: Setze `notification_category='new_category'` beim Erstellen von Nachrichten dieser Kategorie

## Beispiele

### Beispiel: Spieler-Ruhestand Benachrichtigung

```python
# In simulation.py
message = Message(
    subject=f"Spieler {player.name} geht in den Ruhestand",
    content=f"...",
    message_type='info',
    notification_category='player_retirement',
    is_read=False,
    related_club_id=player.club_id,
    related_player_id=player.id
)
db.session.add(message)
```

### Beispiel: Transfer-Benachrichtigung (zukünftig)

```python
message = Message(
    subject=f"Transferangebot für {player.name}",
    content=f"...",
    message_type='info',
    notification_category='transfers',
    is_read=False,
    related_player_id=player.id
)
db.session.add(message)
```

### Beispiel: Finanz-Warnung (zukünftig)

```python
message = Message(
    subject="Warnung: Niedriger Kontostand",
    content=f"...",
    message_type='warning',
    notification_category='finances',
    is_read=False,
    related_club_id=club.id
)
db.session.add(message)
```

## Zukünftige Erweiterungen

Mögliche Erweiterungen für das Benachrichtigungseinstellungs-System:

1. **Granularere Einstellungen**:
   - Unterkategorien für detailliertere Kontrolle
   - Beispiel: "Nur Siege" vs. "Alle Spielergebnisse"

2. **Benachrichtigungshäufigkeit**:
   - Sofort, täglich zusammengefasst, wöchentlich zusammengefasst

3. **Prioritäten**:
   - Wichtige Benachrichtigungen immer anzeigen
   - Unwichtige Benachrichtigungen automatisch archivieren

4. **Filter-Kombinationen**:
   - Benachrichtigungen nach Verein filtern
   - Benachrichtigungen nach Spieler filtern

5. **Export/Import**:
   - Einstellungen exportieren und importieren
   - Vorlagen für verschiedene Spielstile

## Fehlerbehebung

### Nachrichten werden nicht gefiltert

- Überprüfen Sie, ob die NotificationSettings-Tabelle existiert
- Überprüfen Sie, ob die notification_category Spalte in der Message-Tabelle existiert
- Führen Sie das Migrationsskript aus, falls noch nicht geschehen

### Einstellungen werden nicht gespeichert

- Überprüfen Sie die Browser-Konsole auf Fehler
- Überprüfen Sie, ob die API-Endpunkte erreichbar sind
- Überprüfen Sie die Backend-Logs auf Fehler

### Alte Nachrichten haben keine Kategorie

- Führen Sie das Migrationsskript aus
- Das Skript setzt automatisch 'general' als Standard-Kategorie
- Ruhestand-Nachrichten werden automatisch erkannt und kategorisiert

