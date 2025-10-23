# Altersklassen-basierte Team-Zuordnung für Spieler

## Übersicht

Das System berücksichtigt jetzt die Altersklasse der Liga bei der permanenten Team-Zuordnung von Spielern. Spieler dürfen nur Teams zugeordnet werden, deren Liga-Altersklasse **gleich oder älter** als das Spieler-Alter ist.

## Altersklassen-Hierarchie

Von jung nach alt:

| Altersklasse | Altersbereich | Rang |
|--------------|---------------|------|
| F-Jugend     | 7-8 Jahre     | 0    |
| E-Jugend     | 9-10 Jahre    | 1    |
| D-Jugend     | 11-12 Jahre   | 2    |
| C-Jugend     | 13-14 Jahre   | 3    |
| B-Jugend     | 15-16 Jahre   | 4    |
| A-Jugend     | 17-18 Jahre   | 5    |
| Herren       | 18-35 Jahre   | 6    |

## Zuordnungsregeln

### Grundregel

Ein Spieler darf **niemals** einem Team zugeordnet werden, dessen Altersklasse jünger ist als der Spieler.

### Beispiele

#### Beispiel 1: 15-jähriger Spieler (B-Jugend)
- ✓ Darf spielen in: B-Jugend, A-Jugend, Herren
- ✗ Darf NICHT spielen in: C-Jugend, D-Jugend, E-Jugend, F-Jugend

#### Beispiel 2: 10-jähriger Spieler (E-Jugend)
- ✓ Darf spielen in: E-Jugend, D-Jugend, C-Jugend, B-Jugend, A-Jugend, Herren
- ✗ Darf NICHT spielen in: F-Jugend

#### Beispiel 3: 20-jähriger Spieler (Herren)
- ✓ Darf spielen in: Herren
- ✗ Darf NICHT spielen in: Alle Jugendklassen

## Implementierung

### Neue Funktionen

#### `age_class_utils.py`

Enthält Hilfsfunktionen für Altersklassen-Management:

- **`get_minimum_altersklasse_for_age(age)`**: Bestimmt die minimal zulässige Altersklasse für ein Spieler-Alter
- **`get_allowed_altersklassen_for_age(age)`**: Gibt alle zulässigen Altersklassen für ein Spieler-Alter zurück
- **`is_player_allowed_in_team(player_age, team_altersklasse)`**: Prüft, ob ein Spieler einem Team zugeordnet werden darf
- **`normalize_altersklasse(altersklasse)`**: Normalisiert Altersklassen-Strings (z.B. "B-Jugend" → "B")
- **`get_age_class_rank(altersklasse)`**: Gibt den Rang einer Altersklasse in der Hierarchie zurück
- **`find_suitable_team_for_player(player_age, available_teams)`**: Findet das passendste Team für einen Spieler

#### `player_redistribution.py`

Erweitert um altersklassen-bewusste Umverteilung:

- **`redistribute_players_by_strength_and_age()`**: Neue Hauptfunktion für Spieler-Umverteilung
  - Berücksichtigt Altersklassen-Einschränkungen
  - Sortiert Spieler nach Stärke innerhalb ihrer Altersklasse
  - Weist beste Spieler den höchsten zulässigen Teams zu

- **`redistribute_club_players_by_strength_and_age(club_id)`**: Umverteilung für einen spezifischen Verein

- **`redistribute_players_by_strength()`**: Legacy-Funktion (ruft jetzt die neue Funktion auf)

### Saisonwechsel-Logik

#### `simulation.py` - `create_new_season()`

Beim Saisonwechsel:

1. **Spieler altern um 1 Jahr** (`player.age += 1`)
2. **Ruhestand-Prüfung** (Spieler ≥ Ruhestandsalter werden entfernt)
3. **Automatische Umverteilung** (`redistribute_players_by_strength_and_age()`)
   - Spieler werden basierend auf ihrem neuen Alter neu zugeordnet
   - Beispiel: Ein 10-jähriger E-Jugend-Spieler wird mit 11 Jahren automatisch in die D-Jugend "hochgestuft"

## Verwendung

### Bestehende Datenbank korrigieren

```bash
python fix_age_class_violations.py
```

Dieses Script:
- Findet alle Altersklassen-Verstöße
- Verteilt Spieler neu basierend auf Alter und Stärke
- Stellt sicher, dass alle Zuordnungen den Regeln entsprechen

### Verstöße prüfen

```bash
python test_age_based_redistribution.py
```

Dieses Script:
- Zeigt Vereine mit Teams in verschiedenen Altersklassen
- Listet Spieler und ihre zulässigen Teams auf
- Identifiziert Altersklassen-Verstöße

### Unit-Tests

```bash
python test_age_class_utils.py
```

Testet alle Hilfsfunktionen für Altersklassen-Management.

## Fallback-Logik

### Spieler ohne Alter

Spieler ohne gesetztes Alter (`player.age is None`) werden standardmäßig als "Herren" behandelt und können nur Herren-Teams zugeordnet werden.

### Teams ohne Altersklasse

Teams ohne gesetztes `league.altersklasse` werden als "Herren"-Teams behandelt und akzeptieren Spieler aller Altersklassen.

### Unzureichende Teams

Wenn ein Verein keine Teams in der passenden Altersklasse hat:
- Der Spieler wird dem nächst-älteren verfügbaren Team zugeordnet
- Beispiel: Ein 11-jähriger (D-Jugend) in einem Verein ohne D-Jugend-Team wird dem C-Jugend-Team zugeordnet
- Falls auch kein C-Jugend-Team existiert, dann B-Jugend, usw.

## Wichtige Hinweise

### Permanente vs. Dynamische Zuordnung

- **Permanente Zuordnung** (`player.teams`): Wird durch `player_redistribution.py` verwaltet
  - Bestimmt, zu welchen Teams ein Spieler grundsätzlich gehört
  - Wird beim Saisonwechsel aktualisiert
  - Berücksichtigt jetzt Altersklassen

- **Dynamische Zuordnung** (Match-Day): Wird durch `club_player_assignment.py` verwaltet
  - Bestimmt, welche Spieler an einem bestimmten Spieltag für welches Team spielen
  - Berücksichtigt Verfügbarkeit und Stärke
  - Noch NICHT altersklassen-bewusst (TODO)

### Zukünftige Verbesserungen

1. **Match-Day-Zuordnung**: Auch die dynamische Spieler-Zuordnung für Spieltage sollte Altersklassen berücksichtigen
2. **UI-Validierung**: Beim manuellen Hinzufügen von Spielern zu Teams sollte die Altersklasse geprüft werden
3. **Warnungen**: Bei Altersklassen-Verstößen sollten Warnungen im UI angezeigt werden

## Beispiel-Szenario

### Verein mit mehreren Teams

**Verein: "1. FC Zeitz II"**

Teams:
- Herren-Team (Kreisoberliga)
- C-Jugend-Team (C-KL 1)
- D-Jugend-Team (D-KL 1)
- E-Jugend-Team (E-KL 1)

Spieler:
- 10x Herren-Spieler (18-32 Jahre) → Nur Herren-Team
- 8x C-Jugend-Spieler (13-14 Jahre) → Herren oder C-Jugend
- 12x D-Jugend-Spieler (11-12 Jahre) → Herren, C-Jugend oder D-Jugend
- 15x E-Jugend-Spieler (9-10 Jahre) → Alle Teams

### Umverteilung

1. **Herren-Spieler** (10 Spieler):
   - Alle 10 → Herren-Team

2. **C-Jugend-Spieler** (8 Spieler):
   - Beste 6 → C-Jugend-Team
   - Restliche 2 → Herren-Team (falls Platz)

3. **D-Jugend-Spieler** (12 Spieler):
   - Beste 6 → D-Jugend-Team
   - Nächste 6 → C-Jugend-Team (falls Platz)

4. **E-Jugend-Spieler** (15 Spieler):
   - Beste 6 → E-Jugend-Team
   - Nächste 6 → D-Jugend-Team (falls Platz)
   - Restliche 3 → C-Jugend-Team (falls Platz)

## Technische Details

### Sortierung der Teams

Teams werden sortiert nach:
1. **Altersklassen-Rang** (älteste zuerst)
2. **Liga-Level** (höchste Liga zuerst, innerhalb der Altersklasse)

Beispiel:
```
1. Herren (Level 1)
2. Herren (Level 2)
3. Herren (Level 4)
4. A-Jugend (Level 1)
5. B-Jugend (Level 1)
6. C-Jugend (Level 2)
7. D-Jugend (Level 1)
8. E-Jugend (Level 1)
```

**Wichtig**: Die besten Spieler werden zuerst den Herren-Teams zugeordnet,
dann den Jugend-Teams (von älter nach jünger).

### Spieler-Zuordnungs-Algorithmus

```python
for team in teams:
    # Finde alle Spieler, die für dieses Team zulässig sind
    eligible_players = [p for p in players if is_player_allowed_in_team(p.age, team.altersklasse)]
    
    # Sortiere nach Stärke
    eligible_players.sort(by_strength, reverse=True)
    
    # Weise beste Spieler zu
    assign_best_players(team, eligible_players, target_count)
```

## Fehlerbehebung

### Problem: Spieler werden nicht zugeordnet

**Ursache**: Spieler ist zu alt für alle verfügbaren Teams

**Lösung**: 
- Prüfe, ob der Verein ein Team in der passenden Altersklasse hat
- Falls nicht, füge ein passendes Team hinzu oder ändere das Spieler-Alter

### Problem: Team hat zu wenige Spieler

**Ursache**: Nicht genug Spieler in der passenden Altersklasse

**Lösung**:
- Füge mehr Spieler in der passenden Altersklasse hinzu
- Oder: Ändere die Altersklasse des Teams zu einer jüngeren Klasse

### Problem: Altersklassen-Verstöße nach Saisonwechsel

**Ursache**: Umverteilung wurde nicht ausgeführt oder ist fehlgeschlagen

**Lösung**:
```bash
python fix_age_class_violations.py
```

