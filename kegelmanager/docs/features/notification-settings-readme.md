# Benachrichtigungseinstellungen - Vollständige Dokumentation

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Schnellstart](#schnellstart)
3. [Für Benutzer](#für-benutzer)
4. [Für Administratoren](#für-administratoren)
5. [Für Entwickler](#für-entwickler)
6. [Dokumentation](#dokumentation)
7. [Support](#support)

---

## 🎯 Übersicht

Das Benachrichtigungseinstellungs-System ermöglicht es Benutzern, zu konfigurieren, welche Arten von Benachrichtigungen sie im Nachrichten-System erhalten möchten.

### Hauptfunktionen

✅ **Benutzerfreundlich**: Einfache Checkbox-Oberfläche zum Aktivieren/Deaktivieren von Kategorien  
✅ **Persistent**: Einstellungen werden in der Datenbank gespeichert  
✅ **Flexibel**: 8 verschiedene Benachrichtigungskategorien  
✅ **Erweiterbar**: Einfaches Hinzufügen neuer Kategorien  
✅ **Rückwärtskompatibel**: Funktioniert mit bestehenden Datenbanken  

---

## 🚀 Schnellstart

### Für Benutzer

1. Öffnen Sie die **Nachrichten**-Seite
2. Klicken Sie auf **"Einstellungen"**
3. Wählen Sie Ihre gewünschten Kategorien
4. Klicken Sie auf **"Speichern"**

### Für Administratoren (Bestehende Datenbank)

```bash
cd kegelmanager/backend
python migrate_add_notification_settings.py
```

### Für Entwickler

```python
message = Message(
    subject="Betreff",
    content="Inhalt",
    notification_category='player_retirement',  # Kategorie setzen!
    message_type='info'
)
```

---

## 👤 Für Benutzer

### Einstellungen öffnen

1. Navigieren Sie zur **"Nachrichten"** Seite im Hauptmenü
2. Klicken Sie auf den **"Einstellungen"** Button (⚙️ Symbol) oben rechts
3. Ein Modal-Fenster öffnet sich

### Kategorien verwalten

**Einzelne Kategorie aktivieren/deaktivieren:**
- Klicken Sie auf die Checkbox neben der Kategorie

**Alle Kategorien auf einmal:**
- **"Alle auswählen"** - Aktiviert alle Kategorien
- **"Alle abwählen"** - Deaktiviert alle Kategorien

**Änderungen speichern:**
- Klicken Sie auf **"Speichern"** um Ihre Einstellungen zu übernehmen
- Klicken Sie auf **"Abbrechen"** um Änderungen zu verwerfen

### Verfügbare Kategorien

| Kategorie | Status | Beschreibung |
|-----------|--------|--------------|
| 🏃 **Spieler-Ruhestand** | ✅ Aktiv | Benachrichtigungen wenn Spieler in den Ruhestand gehen |
| 🔄 **Transfers** | 🔜 Geplant | Transferangebote und -abschlüsse |
| 🎯 **Spielergebnisse** | 🔜 Geplant | Spielergebnisse und besondere Leistungen |
| 🏥 **Verletzungen** | 🔜 Geplant | Spielerverletzungen |
| 📝 **Verträge** | 🔜 Geplant | Auslaufende Verträge und Verlängerungen |
| 💰 **Finanzen** | 🔜 Geplant | Finanzielle Ereignisse und Warnungen |
| 🏆 **Erfolge** | 🔜 Geplant | Erfolge, Rekorde und Meilensteine |
| ℹ️ **Allgemein** | ✅ Aktiv | Allgemeine Informationen |

### Effekt der Einstellungen

**Deaktivierte Kategorien:**
- Nachrichten werden **nicht angezeigt** in der Nachrichtenliste
- Nachrichten werden **nicht gelöscht**, nur ausgeblendet
- Können jederzeit wieder aktiviert werden

**Aktivierte Kategorien:**
- Nachrichten werden normal angezeigt
- Neue Nachrichten dieser Kategorie werden erstellt

---

## 🔧 Für Administratoren

### Neue Datenbank

Keine Aktion erforderlich! Die Benachrichtigungseinstellungen werden automatisch bei der Datenbankerstellung initialisiert.

### Bestehende Datenbank migrieren

#### Schritt 1: Backup erstellen

**WICHTIG**: Erstellen Sie immer ein Backup vor der Migration!

```bash
# Windows
copy kegelmanager\backend\instance\ihre_db.db kegelmanager\backend\instance\ihre_db_backup.db

# Linux/Mac
cp kegelmanager/backend/instance/ihre_db.db kegelmanager/backend/instance/ihre_db_backup.db
```

#### Schritt 2: Migration ausführen

```bash
cd kegelmanager/backend
python migrate_add_notification_settings.py
```

Das Skript wird:
- ✅ `notification_category` Spalte zur Message-Tabelle hinzufügen
- ✅ NotificationSettings-Tabelle erstellen
- ✅ Standard-Einstellungen erstellen (alle aktiviert)
- ✅ Bestehende Ruhestand-Nachrichten kategorisieren

#### Schritt 3: Testen

```bash
cd kegelmanager/backend
python test_notification_settings.py
```

### Fehlerbehebung

**Migration schlägt fehl:**
1. Schließen Sie die Anwendung
2. Überprüfen Sie Datei-Berechtigungen
3. Stellen Sie Backup wieder her
4. Versuchen Sie es erneut

**Einstellungen werden nicht angezeigt:**
1. Löschen Sie Browser-Cache
2. Laden Sie die Seite neu (Strg+F5)
3. Überprüfen Sie Browser-Konsole (F12)

---

## 💻 Für Entwickler

### Nachricht mit Kategorie erstellen

```python
from models import db, Message

# Beispiel: Spieler-Ruhestand
message = Message(
    subject=f"Spieler {player.name} geht in den Ruhestand",
    content="...",
    message_type='info',
    notification_category='player_retirement',  # Wichtig!
    is_read=False,
    related_player_id=player.id
)
db.session.add(message)
db.session.commit()
```

### Verfügbare Kategorien (IDs)

```python
CATEGORIES = [
    'player_retirement',  # Spieler-Ruhestand
    'transfers',          # Transfers
    'match_results',      # Spielergebnisse
    'injuries',           # Verletzungen
    'contracts',          # Verträge
    'finances',           # Finanzen
    'achievements',       # Erfolge
    'general'             # Allgemein (Standard)
]
```

### Neue Kategorie hinzufügen

1. **Backend - models.py**: Feld zur NotificationSettings-Klasse hinzufügen
2. **Backend - models.py**: to_dict() Methode aktualisieren
3. **Backend - app.py**: update_notification_settings() aktualisieren
4. **Backend - app.py**: get_notification_categories() aktualisieren
5. **Migration**: Migrationsskript für bestehende DBs erstellen
6. **Code**: notification_category beim Erstellen von Nachrichten setzen

Siehe `NOTIFICATION_SETTINGS.md` für detaillierte Anweisungen.

### API-Endpunkte

```javascript
// Einstellungen abrufen
GET /api/notification-settings

// Einstellungen aktualisieren
PUT /api/notification-settings
Body: { "player_retirement": false, "transfers": true, ... }

// Kategorien abrufen
GET /api/notification-settings/categories

// Nachrichten abrufen (automatisch gefiltert)
GET /api/messages
```

### Frontend-Integration

```javascript
import { 
  getNotificationSettings, 
  updateNotificationSettings,
  getNotificationCategories 
} from '../services/api';

// Einstellungen laden
const settings = await getNotificationSettings();

// Einstellungen aktualisieren
await updateNotificationSettings({
  player_retirement: false,
  transfers: true
});

// Kategorien laden
const categories = await getNotificationCategories();
```

---

## 📚 Dokumentation

### Vollständige Dokumentation

- **[NOTIFICATION_SETTINGS.md](NOTIFICATION_SETTINGS.md)** - Technische Dokumentation
- **[NOTIFICATION_SETTINGS_SETUP.md](NOTIFICATION_SETTINGS_SETUP.md)** - Setup und Verwendung
- **[NOTIFICATION_SETTINGS_IMPLEMENTATION.md](NOTIFICATION_SETTINGS_IMPLEMENTATION.md)** - Implementierungsdetails
- **[NOTIFICATION_SETTINGS_QUICKSTART.md](NOTIFICATION_SETTINGS_QUICKSTART.md)** - Schnellstart-Anleitung

### Skripte

- **migrate_add_notification_settings.py** - Migrationsskript für bestehende DBs
- **test_notification_settings.py** - Test-Skript zur Überprüfung

### Komponenten

**Backend:**
- `models.py` - Message und NotificationSettings Modelle
- `app.py` - API-Endpunkte
- `simulation.py` - Nachrichtenerstellung
- `init_db.py` - Datenbank-Initialisierung

**Frontend:**
- `Messages.jsx` - Nachrichten-Seite mit Einstellungen-Button
- `NotificationSettingsModal.jsx` - Einstellungen-Modal
- `api.js` - API-Integration

---

## 🆘 Support

### Häufige Fragen

**Q: Werden meine Einstellungen gespeichert?**  
A: Ja, in der Datenbank. Sie bleiben über Sitzungen hinweg erhalten.

**Q: Werden Nachrichten gelöscht, wenn ich eine Kategorie deaktiviere?**  
A: Nein, sie werden nur ausgeblendet. Bei Reaktivierung sind sie wieder sichtbar.

**Q: Kann ich verschiedene Einstellungen für verschiedene Vereine haben?**  
A: Aktuell nicht - die Einstellungen gelten global.

**Q: Was ist die Standard-Einstellung?**  
A: Alle Kategorien sind standardmäßig aktiviert.

### Probleme melden

Bei Problemen:
1. Überprüfen Sie die Dokumentation
2. Überprüfen Sie Browser-Konsole (F12)
3. Überprüfen Sie Backend-Logs
4. Erstellen Sie ein Issue im Repository

---

## 📝 Lizenz

Teil des Kegelmanager Bowling Simulation Game Projekts.

---

**Version**: 1.0.0  
**Datum**: 2024  
**Status**: ✅ Produktionsbereit

