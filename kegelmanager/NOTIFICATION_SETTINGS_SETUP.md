# Benachrichtigungseinstellungen - Setup und Verwendung

## Übersicht

Dieses Dokument beschreibt, wie Sie die Benachrichtigungseinstellungen in Ihrer Bowling-Simulation einrichten und verwenden.

## Für neue Datenbanken

Wenn Sie eine neue Datenbank erstellen, werden die Benachrichtigungseinstellungen automatisch initialisiert:

1. Die `NotificationSettings` Tabelle wird automatisch erstellt
2. Standard-Einstellungen werden erstellt (alle Kategorien aktiviert)
3. Keine weiteren Schritte erforderlich!

## Für bestehende Datenbanken

Wenn Sie bereits eine Datenbank haben, müssen Sie das Migrationsskript ausführen:

### Schritt 1: Backup erstellen

**WICHTIG**: Erstellen Sie immer ein Backup Ihrer Datenbank, bevor Sie Migrationen durchführen!

```bash
# Windows
copy kegelmanager\backend\instance\ihre_datenbank.db kegelmanager\backend\instance\ihre_datenbank_backup.db

# Linux/Mac
cp kegelmanager/backend/instance/ihre_datenbank.db kegelmanager/backend/instance/ihre_datenbank_backup.db
```

### Schritt 2: Migration ausführen

```bash
cd kegelmanager/backend
python migrate_add_notification_settings.py
```

Das Skript wird:
- Alle Datenbanken im `instance` Ordner finden
- Sie fragen, ob Sie alle migrieren möchten
- Für jede Datenbank:
  - `notification_category` Spalte zur `Message` Tabelle hinzufügen
  - `NotificationSettings` Tabelle erstellen
  - Standard-Einstellungen erstellen
  - Bestehende Ruhestand-Nachrichten automatisch kategorisieren

### Schritt 3: Überprüfung

Nach der Migration können Sie die Funktionalität testen:

```bash
cd kegelmanager/backend
python test_notification_settings.py
```

## Verwendung im Spiel

### Benachrichtigungseinstellungen öffnen

1. Navigieren Sie zur "Nachrichten" Seite
2. Klicken Sie auf den "Einstellungen" Button oben rechts
3. Ein Modal-Fenster öffnet sich mit allen verfügbaren Kategorien

### Kategorien aktivieren/deaktivieren

- Klicken Sie auf die Checkbox neben einer Kategorie, um sie zu aktivieren/deaktivieren
- Verwenden Sie "Alle auswählen" oder "Alle abwählen" für schnelle Änderungen
- Klicken Sie auf "Speichern", um Ihre Änderungen zu speichern

### Effekt der Einstellungen

- Deaktivierte Kategorien werden **nicht** in Ihrer Nachrichtenliste angezeigt
- Die Nachrichten werden nicht gelöscht, nur ausgeblendet
- Wenn Sie eine Kategorie wieder aktivieren, werden die Nachrichten wieder sichtbar

## Verfügbare Kategorien

### Aktuell implementiert:

1. **Spieler-Ruhestand** (`player_retirement`)
   - Benachrichtigungen wenn Ihre Spieler in den Ruhestand gehen
   - Wird automatisch bei Saisonwechsel erstellt

### Für zukünftige Implementierung vorbereitet:

2. **Transfers** (`transfers`)
3. **Spielergebnisse** (`match_results`)
4. **Verletzungen** (`injuries`)
5. **Verträge** (`contracts`)
6. **Finanzen** (`finances`)
7. **Erfolge** (`achievements`)
8. **Allgemein** (`general`)

## Für Entwickler

### Neue Benachrichtigung mit Kategorie erstellen

```python
from models import db, Message

message = Message(
    subject="Ihr Betreff",
    content="Ihr Inhalt",
    message_type='info',  # info, success, warning, error
    notification_category='player_retirement',  # Kategorie setzen!
    is_read=False,
    related_player_id=player.id  # Optional: Verknüpfung zu Entitäten
)
db.session.add(message)
db.session.commit()
```

### Neue Kategorie hinzufügen

Siehe `NOTIFICATION_SETTINGS.md` für detaillierte Anweisungen zum Hinzufügen neuer Kategorien.

## Fehlerbehebung

### Problem: Einstellungen-Button wird nicht angezeigt

**Lösung**: 
- Stellen Sie sicher, dass Sie die neueste Version des Frontends haben
- Löschen Sie den Browser-Cache und laden Sie die Seite neu
- Überprüfen Sie die Browser-Konsole auf Fehler

### Problem: Nachrichten werden nicht gefiltert

**Lösung**:
- Führen Sie das Migrationsskript aus (siehe oben)
- Überprüfen Sie, ob die `NotificationSettings` Tabelle existiert
- Überprüfen Sie die Backend-Logs auf Fehler

### Problem: Migration schlägt fehl

**Lösung**:
- Stellen Sie sicher, dass die Datenbank nicht von einem anderen Prozess verwendet wird
- Schließen Sie die Anwendung, bevor Sie die Migration ausführen
- Überprüfen Sie die Berechtigungen für die Datenbankdatei
- Stellen Sie Ihr Backup wieder her und versuchen Sie es erneut

### Problem: Alte Nachrichten haben keine Kategorie

**Lösung**:
- Das Migrationsskript setzt automatisch 'general' als Standard
- Ruhestand-Nachrichten werden automatisch als 'player_retirement' kategorisiert
- Wenn dies nicht funktioniert, führen Sie das Migrationsskript erneut aus

## API-Endpunkte

Für Frontend-Entwickler oder API-Nutzung:

### Einstellungen abrufen
```
GET /api/notification-settings
```

Antwort:
```json
{
  "id": 1,
  "player_retirement": true,
  "transfers": true,
  "match_results": true,
  "injuries": true,
  "contracts": true,
  "finances": true,
  "achievements": true,
  "general": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Einstellungen aktualisieren
```
PUT /api/notification-settings
Content-Type: application/json

{
  "player_retirement": false,
  "transfers": true,
  ...
}
```

### Kategorien abrufen
```
GET /api/notification-settings/categories
```

Antwort:
```json
[
  {
    "id": "player_retirement",
    "name": "Spieler-Ruhestand",
    "description": "Benachrichtigungen wenn Spieler in den Ruhestand gehen"
  },
  ...
]
```

### Nachrichten abrufen (gefiltert)
```
GET /api/messages
```

Die Nachrichten werden automatisch basierend auf den Einstellungen gefiltert.

## Support

Bei Problemen oder Fragen:
1. Überprüfen Sie die Dokumentation in `NOTIFICATION_SETTINGS.md`
2. Überprüfen Sie die Backend-Logs
3. Überprüfen Sie die Browser-Konsole
4. Erstellen Sie ein Issue im Repository

