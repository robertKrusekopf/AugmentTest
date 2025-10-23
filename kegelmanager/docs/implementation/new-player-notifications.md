# Neue Spieler Benachrichtigungen

## Übersicht

Das System erstellt automatisch Benachrichtigungen, wenn ein neuer Spieler für einen Verein generiert wird. Diese Nachrichten werden **nur für Spieler des Vereins erstellt, den Sie in den Einstellungen als Manager-Verein ausgewählt haben**.

## Voraussetzung: Manager-Verein einstellen

Damit Sie Benachrichtigungen über neue Spieler erhalten, müssen Sie zunächst in den **Einstellungen** einen Verein als Ihren Manager-Verein auswählen:

1. Öffnen Sie die **Einstellungen** (Zahnrad-Symbol im Menü)
2. Wechseln Sie zum Tab **"Spieleinstellungen"**
3. Wählen Sie unter **"Manager Verein"** den Verein aus, den Sie managen möchten
4. Klicken Sie auf **"Einstellungen speichern"**

**Wichtig**: Nur für Spieler dieses Vereins werden Benachrichtigungen erstellt!

## Funktionsweise

### Automatische Erstellung

Beim **Saisonwechsel** (`simulation.py` → `start_new_season()`):

1. Alle aktiven Spieler werden um 1 Jahr gealtert
2. Für jeden Spieler wird geprüft: `age >= retirement_age`?
3. Wenn ja:
   - Spieler wird als `is_retired = True` markiert
   - Spieler wird aus allen Teams entfernt
   - Ruhestandsnachricht wird erstellt (wenn Spieler zum Manager-Verein gehört)
   - **Neuer Spieler wird für den Verein generiert**
   - **Wenn der neue Spieler zum Manager-Verein gehört**: Automatisch wird eine Benachrichtigung erstellt
   - **Wenn der neue Spieler zu einem anderen Verein gehört**: Keine Nachricht wird erstellt

### Nachrichteninhalt

Die Nachricht enthält:

- **Betreff**: "Neuer Spieler [Name] ist dem Verein beigetreten"
- **Inhalt**:
  - Persönliche Ansprache an den Manager
  - **Klickbarer Link** zum Spielerprofil
  - Vereinsname
  - Alter des Spielers
  - Position (Kegler)
  - Willkommensnachricht
- **Typ**: `success` (grünes Icon)
- **Kategorie**: `player_new`
- **Verknüpfungen**:
  - `related_club_id`: Verein des Spielers
  - `related_player_id`: ID des neuen Spielers

**Hinweis**: Stärke und Talent werden bewusst NICHT angezeigt, da dies geheime Attribute für die Spielberechnung sind. Der Manager soll die Stärke des Spielers nur an den Ergebnissen abschätzen können.

### Beispiel-Nachricht

```
Betreff: Neuer Spieler Max Mustermann ist dem Verein beigetreten

Sehr geehrter Manager,

wir freuen uns, Ihnen mitteilen zu können, dass Max Mustermann unserem
Verein beigetreten ist!

Der 18-jährige Kegler hat einen Vertrag bei SV Beispielverein unterschrieben
und steht ab sofort zur Verfügung.

Wir wünschen Max Mustermann viel Erfolg und eine erfolgreiche Karriere
bei SV Beispielverein!

Mit freundlichen Grüßen
Die Geschäftsführung
```

## Klickbare Links

### Im Frontend

Die Nachrichten-Komponente (`Messages.jsx`) rendert HTML-Links:

```jsx
<div 
  className="message-content" 
  dangerouslySetInnerHTML={{ __html: message.content }}
/>
```

Der Link `<a href="/players/{player.id}" class="player-link">` wird als klickbarer Link dargestellt, der direkt zum Spielerprofil führt.

### Styling

Die CSS-Klasse `.player-link` kann in `Messages.css` gestylt werden:

```css
.player-link {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.player-link:hover {
  text-decoration: underline;
}
```

## Code-Implementierung

### Backend (`simulation.py`)

#### Funktion: `create_new_player_message(player)`

```python
def create_new_player_message(player):
    """
    Erstellt eine Nachricht, wenn ein neuer Spieler für einen Verein generiert wird.
    Nur für Spieler des Manager-Vereins.
    
    Args:
        player: Der neu generierte Spieler
    """
    try:
        # Get game settings to check if this player belongs to the manager's club
        settings = GameSettings.query.first()
        
        # Only create message if player belongs to the manager's club
        if not settings or not settings.manager_club_id:
            # No manager club set, don't create messages
            return
        
        if player.club_id != settings.manager_club_id:
            # Player doesn't belong to manager's club, don't create message
            return
        
        # Get the club name
        club_name = player.club.name if player.club else "Unbekannter Verein"
        
        # Create the message
        subject = f"Neuer Spieler {player.name} ist dem Verein beigetreten"
        
        # Create HTML content with clickable player name
        content = f"""Sehr geehrter Manager,

wir freuen uns, Ihnen mitteilen zu können, dass <a href="/players/{player.id}" class="player-link">{player.name}</a> unserem Verein beigetreten ist!

Der {player.age}-jährige {player.position} hat einen Vertrag bei {club_name} unterschrieben und steht ab sofort zur Verfügung.

Wir wünschen {player.name} viel Erfolg und eine erfolgreiche Karriere bei {club_name}!

Mit freundlichen Grüßen
Die Geschäftsführung"""
        
        # Create the message
        message = Message(
            subject=subject,
            content=content,
            message_type='success',
            notification_category='player_new',
            is_read=False,
            related_club_id=player.club_id,
            related_player_id=player.id
        )
        
        db.session.add(message)
        print(f"  Created new player notification for {player.name} (Manager's club)")
        
    except Exception as e:
        print(f"  Error creating new player message for {player.name}: {e}")
```

#### Integration in `start_new_season()`

```python
# In the retirement loop:
for player in players:
    player.age += 1
    
    # Check if player should retire
    if player.retirement_age and player.age >= player.retirement_age:
        # Mark player as retired
        player.is_retired = True
        player.retirement_season_id = new_season.id
        
        # Remove player from all teams
        player.teams.clear()
        
        retired_count += 1
        print(f"  Player {player.name} retired at age {player.age}")
        
        # Create retirement notification message for the player's club
        if player.club_id:
            create_retirement_message(player)
            
            # Generate a replacement player for the club
            new_player = generate_replacement_player(player.club_id)
            if new_player:
                db.session.add(new_player)
                new_players_generated += 1
                
                # Create notification for new player if club is managed
                create_new_player_message(new_player)
```

## Testen

### Test-Script

Ein Test-Script (`test_new_player_notifications.py`) ist verfügbar:

```bash
python kegelmanager/backend/test_new_player_notifications.py kegelmanager/backend/instance/kegelmanager_default.db
```

Das Script:
- Prüft, ob ein Manager-Verein gesetzt ist (setzt einen, falls nicht)
- Generiert einen Testspieler für den Manager-Verein
- Erstellt eine Benachrichtigung
- Prüft, ob die Benachrichtigung korrekt erstellt wurde
- Generiert einen Testspieler für einen anderen Verein
- Prüft, dass KEINE Benachrichtigung erstellt wurde

### Erwartete Ausgabe

```
✅ Manager club: SG Großgrimma/Hohenmölsen (ID: 1)

Test 1: Generate player for manager's club
✅ Generated player: Tobias Schmidt
✅ Notification created successfully!
   Subject: Neuer Spieler Tobias Schmidt ist dem Verein beigetreten
   Type: success
   Category: player_new

Test 2: Generate player for non-manager club
✅ Correctly did NOT create notification for non-managed club

✅ All tests passed!
```

## Zusammenhang mit anderen Systemen

### Player Regeneration System

Die neue Spieler-Benachrichtigung ist eng mit dem Player Regeneration System verbunden:

1. **Ruhestand**: Spieler geht in den Ruhestand → Ruhestandsnachricht
2. **Regeneration**: Neuer Spieler wird generiert → Neue Spieler-Nachricht
3. **Beide Nachrichten** werden nur für den Manager-Verein erstellt

### Notification Categories

Das System verwendet die Kategorie `player_new` für neue Spieler-Benachrichtigungen. Dies ermöglicht:

- Filterung nach Nachrichtentyp
- Separate Einstellungen für verschiedene Benachrichtigungstypen
- Statistiken über verschiedene Nachrichtentypen

Andere Kategorien:
- `player_retirement`: Ruhestandsnachrichten
- `match_result`: Spielergebnisse
- `transfer`: Transfernachrichten
- etc.

## Vorteile

1. **Automatische Benachrichtigung**: Manager wird sofort informiert, wenn ein neuer Spieler dem Verein beitritt
2. **Detaillierte Informationen**: Alle wichtigen Spielerdetails auf einen Blick
3. **Direkter Zugriff**: Klickbarer Link zum Spielerprofil
4. **Konsistenz**: Gleiche Formatierung wie Ruhestandsnachrichten
5. **Selektiv**: Nur für den Manager-Verein, keine Spam-Nachrichten

## Zukünftige Erweiterungen

Mögliche Verbesserungen:

1. **Spielervergleich**: Vergleich des neuen Spielers mit dem pensionierten Spieler
2. **Empfehlungen**: Automatische Teamzuweisungsempfehlungen
3. **Trainingsplan**: Vorgeschlagener Trainingsplan für den neuen Spieler
4. **Vertragsdetails**: Detaillierte Vertragsinformationen
5. **Statistiken**: Erwartete Entwicklung basierend auf Talent

## Fehlerbehebung

### Keine Benachrichtigungen erhalten?

1. **Manager-Verein gesetzt?**
   - Öffnen Sie die Einstellungen
   - Prüfen Sie, ob ein Manager-Verein ausgewählt ist
   - Speichern Sie die Einstellungen

2. **GameSettings-Tabelle leer?**
   - Prüfen Sie mit: `SELECT * FROM game_settings;`
   - Falls leer, wird beim nächsten Einstellungen-Speichern ein Eintrag erstellt

3. **Spieler gehört zu anderem Verein?**
   - Benachrichtigungen werden nur für den Manager-Verein erstellt
   - Prüfen Sie, ob der neue Spieler wirklich zu Ihrem Verein gehört

4. **Fehler in der Konsole?**
   - Prüfen Sie die Backend-Konsole auf Fehlermeldungen
   - Fehler werden mit `print(f"Error creating new player message...")` ausgegeben

## Technische Details

- **Datenbank-Tabelle**: `message`
- **Nachrichtentyp**: `success` (grünes Icon)
- **Kategorie**: `player_new`
- **Erstellt in**: `simulation.py` → `create_new_player_message()`
- **Aufgerufen von**: `start_new_season()` nach `generate_replacement_player()`
- **Abhängigkeiten**: `GameSettings`, `Club`, `Player`, `Message`

