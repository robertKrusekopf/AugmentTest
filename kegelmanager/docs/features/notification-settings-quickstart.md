# Benachrichtigungseinstellungen - Schnellstart

## Für Benutzer

### Wie öffne ich die Einstellungen?

1. Klicken Sie auf **"Nachrichten"** im Menü
2. Klicken Sie auf den **"Einstellungen"** Button oben rechts
3. Ein Fenster öffnet sich mit allen Benachrichtigungskategorien

### Wie ändere ich meine Einstellungen?

1. **Einzelne Kategorie aktivieren/deaktivieren**: Klicken Sie auf die Checkbox neben der Kategorie
2. **Alle aktivieren**: Klicken Sie auf "Alle auswählen"
3. **Alle deaktivieren**: Klicken Sie auf "Alle abwählen"
4. **Speichern**: Klicken Sie auf "Speichern" um Ihre Änderungen zu übernehmen

### Was passiert, wenn ich eine Kategorie deaktiviere?

- Nachrichten dieser Kategorie werden **nicht mehr angezeigt**
- Die Nachrichten werden **nicht gelöscht**, nur ausgeblendet
- Wenn Sie die Kategorie wieder aktivieren, werden die Nachrichten wieder sichtbar

### Welche Kategorien gibt es?

| Kategorie | Beschreibung |
|-----------|--------------|
| **Spieler-Ruhestand** | Benachrichtigungen wenn Ihre Spieler in den Ruhestand gehen |
| **Transfers** | Benachrichtigungen über Transferangebote und -abschlüsse *(zukünftig)* |
| **Spielergebnisse** | Benachrichtigungen über Spielergebnisse und besondere Leistungen *(zukünftig)* |
| **Verletzungen** | Benachrichtigungen über Spielerverletzungen *(zukünftig)* |
| **Verträge** | Benachrichtigungen über auslaufende Verträge *(zukünftig)* |
| **Finanzen** | Benachrichtigungen über finanzielle Ereignisse und Warnungen *(zukünftig)* |
| **Erfolge** | Benachrichtigungen über Erfolge, Rekorde und Meilensteine *(zukünftig)* |
| **Allgemein** | Allgemeine Informationen und sonstige Benachrichtigungen |

---

## Für Administratoren

### Erste Einrichtung (Neue Datenbank)

Keine Aktion erforderlich! Die Benachrichtigungseinstellungen werden automatisch erstellt.

### Migration (Bestehende Datenbank)

```bash
cd kegelmanager/backend
python migrate_add_notification_settings.py
```

**WICHTIG**: Erstellen Sie vorher ein Backup Ihrer Datenbank!

### Überprüfung

```bash
cd kegelmanager/backend
python test_notification_settings.py
```

---

## Für Entwickler

### Nachricht mit Kategorie erstellen

```python
from models import db, Message

message = Message(
    subject="Ihr Betreff",
    content="Ihr Inhalt",
    message_type='info',
    notification_category='player_retirement',  # Kategorie!
    is_read=False
)
db.session.add(message)
db.session.commit()
```

### Verfügbare Kategorien

- `player_retirement` - Spieler-Ruhestand
- `transfers` - Transfers
- `match_results` - Spielergebnisse
- `injuries` - Verletzungen
- `contracts` - Verträge
- `finances` - Finanzen
- `achievements` - Erfolge
- `general` - Allgemein (Standard)

### Neue Kategorie hinzufügen

Siehe `NOTIFICATION_SETTINGS.md` für detaillierte Anweisungen.

---

## Häufige Fragen (FAQ)

### Werden meine Einstellungen gespeichert?

Ja, Ihre Einstellungen werden in der Datenbank gespeichert und bleiben über Sitzungen hinweg erhalten.

### Kann ich Nachrichten wiederherstellen, die ich ausgeblendet habe?

Ja, aktivieren Sie einfach die entsprechende Kategorie wieder und die Nachrichten werden wieder angezeigt.

### Werden alte Nachrichten automatisch kategorisiert?

Ja, das Migrationsskript kategorisiert automatisch:
- Ruhestand-Nachrichten als `player_retirement`
- Alle anderen als `general`

### Was ist die Standard-Einstellung?

Alle Kategorien sind standardmäßig aktiviert.

### Kann ich verschiedene Einstellungen für verschiedene Vereine haben?

Aktuell nicht - die Einstellungen gelten global. Dies könnte in einer zukünftigen Version hinzugefügt werden.

---

## Fehlerbehebung

### Problem: Einstellungen-Button wird nicht angezeigt

**Lösung**: Löschen Sie den Browser-Cache und laden Sie die Seite neu.

### Problem: Einstellungen werden nicht gespeichert

**Lösung**: Überprüfen Sie die Browser-Konsole (F12) auf Fehler.

### Problem: Nachrichten werden nicht gefiltert

**Lösung**: Führen Sie das Migrationsskript aus (siehe oben).

---

## Weitere Informationen

- **Technische Dokumentation**: `NOTIFICATION_SETTINGS.md`
- **Setup-Anleitung**: `NOTIFICATION_SETTINGS_SETUP.md`
- **Implementierungsdetails**: `NOTIFICATION_SETTINGS_IMPLEMENTATION.md`

