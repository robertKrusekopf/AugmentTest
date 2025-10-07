# Ruhestandsnachrichten-System

## Übersicht

Das Ruhestandsnachrichten-System erstellt automatisch Benachrichtigungen, wenn ein Spieler in den Ruhestand geht. Diese Nachrichten werden **nur für Spieler des Vereins erstellt, den Sie in den Einstellungen als Manager-Verein ausgewählt haben**.

## Voraussetzung: Manager-Verein einstellen

Damit Sie Ruhestandsnachrichten erhalten, müssen Sie zunächst in den **Einstellungen** einen Verein als Ihren Manager-Verein auswählen:

1. Öffnen Sie die **Einstellungen** (Zahnrad-Symbol im Menü)
2. Wechseln Sie zum Tab **"Spieleinstellungen"**
3. Wählen Sie unter **"Manager Verein"** den Verein aus, den Sie managen möchten
4. Klicken Sie auf **"Einstellungen speichern"**

**Wichtig**: Nur für Spieler dieses Vereins werden Ruhestandsnachrichten erstellt!

## Funktionsweise

### Automatische Erstellung

Beim **Saisonwechsel** (`simulation.py` → `start_new_season()`):

1. Alle aktiven Spieler werden um 1 Jahr gealtert
2. Für jeden Spieler wird geprüft: `age >= retirement_age`?
3. Wenn ja:
   - Spieler wird als `is_retired = True` markiert
   - Spieler wird aus allen Teams entfernt
   - **Wenn der Spieler zum Manager-Verein gehört**: Automatisch wird eine Ruhestandsnachricht erstellt
   - **Wenn der Spieler zu einem anderen Verein gehört**: Keine Nachricht wird erstellt

### Nachrichteninhalt

Die Nachricht enthält:

- **Betreff**: "Spieler [Name] geht in den Ruhestand"
- **Inhalt**: 
  - Persönliche Ansprache an den Manager
  - **Klickbarer Link** zum Spielerprofil
  - Vereinsname
  - Alter des Spielers
  - Dankesworte
- **Typ**: `info` (blaues Icon)
- **Verknüpfungen**:
  - `related_club_id`: Verein des Spielers
  - `related_player_id`: ID des pensionierten Spielers

### Beispiel-Nachricht

```
Betreff: Spieler Max Mustermann geht in den Ruhestand

Sehr geehrter Manager,

wir möchten Sie darüber informieren, dass Max Mustermann seine aktive 
Karriere beendet hat.

Nach vielen Jahren im Dienste von SV Beispielverein hat sich Max Mustermann 
im Alter von 38 Jahren dazu entschieden, in den wohlverdienten Ruhestand 
zu gehen.

Wir danken Max Mustermann für seinen Einsatz und wünschen ihm alles Gute 
für die Zukunft!

Mit freundlichen Grüßen
Die Geschäftsführung
```

## Klickbare Links

### Im Frontend

Die Nachrichten-Komponente (`Messages.jsx`) rendert HTML-Links:

- **Spielername** ist ein klickbarer Link: `<a href="/players/{id}">`
- Beim Klick wird der Benutzer zum Spielerprofil navigiert
- Links werden mit `react-router-dom` Navigation behandelt
- Externe Links öffnen in neuem Tab

### Styling

Links in Nachrichten haben spezielles Styling (`Messages.css`):

```css
.message-content-html a {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 500;
  border-bottom: 1px solid transparent;
}

.message-content-html a:hover {
  border-bottom-color: var(--primary-color);
}

.message-content-html a.player-link {
  font-weight: 600;
}
```

## Code-Implementierung

### Backend (`simulation.py`)

```python
def create_retirement_message(player):
    """
    Erstellt eine Nachricht, wenn ein Spieler in den Ruhestand geht.
    Nur für Spieler des Manager-Vereins.
    """
    # Get game settings to check if this player belongs to the manager's club
    settings = GameSettings.query.first()

    # Only create message if player belongs to the manager's club
    if not settings or not settings.manager_club_id:
        return  # No manager club set

    if player.club_id != settings.manager_club_id:
        return  # Player doesn't belong to manager's club

    club_name = player.club.name if player.club else "Unbekannter Verein"

    subject = f"Spieler {player.name} geht in den Ruhestand"

    content = f"""Sehr geehrter Manager,

wir möchten Sie darüber informieren, dass <a href="/players/{player.id}" class="player-link">{player.name}</a> seine aktive Karriere beendet hat.

Nach vielen Jahren im Dienste von {club_name} hat sich {player.name} im Alter von {player.age} Jahren dazu entschieden, in den wohlverdienten Ruhestand zu gehen.

Wir danken {player.name} für seinen Einsatz und wünschen ihm alles Gute für die Zukunft!

Mit freundlichen Grüßen
Die Geschäftsführung"""
    
    message = Message(
        subject=subject,
        content=content,
        message_type='info',
        is_read=False,
        related_club_id=player.club_id,
        related_player_id=player.id
    )
    
    db.session.add(message)
```

### Frontend (`Messages.jsx`)

```javascript
// Render message content with clickable links
const renderMessageContent = (content) => {
  const contentWithBreaks = content.replace(/\n/g, '<br>');
  
  return (
    <div 
      className="message-content-html"
      dangerouslySetInnerHTML={{ __html: contentWithBreaks }}
      onClick={handleContentClick}
    />
  );
};

// Handle clicks on links in message content
const handleContentClick = (e) => {
  if (e.target.tagName === 'A') {
    e.preventDefault();
    const href = e.target.getAttribute('href');
    
    if (href && href.startsWith('/')) {
      navigate(href);
    } else if (href && href.startsWith('http')) {
      window.open(href, '_blank');
    }
  }
};
```

## Testen

### Test-Skript

Ein Test-Skript ist verfügbar: `test_retirement_message.py`

```bash
cd kegelmanager/backend
python test_retirement_message.py
```

Dieses Skript:
1. Findet einen aktiven Spieler in der Datenbank
2. Erstellt eine Test-Ruhestandsnachricht für diesen Spieler
3. Zeigt Details der erstellten Nachricht an

### Manuelles Testen

1. Starten Sie die Anwendung
2. Führen Sie einen Saisonwechsel durch
3. Wenn Spieler in den Ruhestand gehen, werden automatisch Nachrichten erstellt
4. Öffnen Sie das Nachrichten-Menü
5. Klicken Sie auf eine Ruhestandsnachricht
6. Klicken Sie auf den Spielernamen → Sie werden zum Spielerprofil navigiert

## Erweiterungsmöglichkeiten

### Weitere automatische Nachrichten

Das gleiche System kann für andere Ereignisse verwendet werden:

1. **Vertragsende**: Benachrichtigung 3 Monate vor Vertragsende
2. **Verletzungen**: Wenn ein Spieler verletzt wird
3. **Transferangebote**: Wenn ein anderer Verein Interesse zeigt
4. **Spielergebnisse**: Zusammenfassung nach jedem Spieltag
5. **Aufstieg/Abstieg**: Am Ende der Saison
6. **Pokalerfolge**: Bei Pokalsiegen
7. **Rekorde**: Wenn ein Spieler einen Rekord bricht

### Nachrichtenfilter

Zukünftige Erweiterungen könnten umfassen:

- Filter nach Nachrichtentyp (Ruhestand, Transfer, Spiele, etc.)
- Filter nach Verein
- Filter nach Spieler
- Suchfunktion in Nachrichten

### Benachrichtigungen

- Badge im Menü zeigt Anzahl ungelesener Nachrichten ✅ (bereits implementiert)
- Push-Benachrichtigungen (zukünftig)
- E-Mail-Benachrichtigungen (zukünftig)

## Sicherheit

### HTML-Sanitization

Aktuell wird `dangerouslySetInnerHTML` verwendet, um HTML-Links zu rendern. Dies ist sicher, weil:

1. Der HTML-Inhalt wird **nur vom Backend** erstellt
2. Es gibt **keine Benutzereingaben** in den Nachrichten
3. Alle Links werden vom System generiert

Für zukünftige Erweiterungen mit Benutzereingaben sollte eine HTML-Sanitization-Bibliothek wie `DOMPurify` verwendet werden.

## Zusammenfassung

✅ **Automatische Erstellung** bei Spieler-Ruhestand  
✅ **Klickbare Links** zum Spielerprofil  
✅ **Professionelle Formatierung** mit HTML  
✅ **Verknüpfung** zu Verein und Spieler  
✅ **Badge-Anzeige** für ungelesene Nachrichten  
✅ **Test-Skript** verfügbar  

Das System ist vollständig funktionsfähig und kann als Basis für weitere automatische Benachrichtigungen dienen!

