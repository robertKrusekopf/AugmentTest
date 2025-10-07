# Spielergenerierung basierend auf Liga-Altersklasse

## Zusammenfassung der Änderungen

Die Spielergenerierung wurde angepasst, um das `altersklasse`-Feld der Liga zu berücksichtigen. Zuvor wurde nur zwischen `is_youth_team` (16-19 Jahre) und Erwachsenen (20-35 Jahre) unterschieden.

## Neue Funktion: `get_age_range_for_altersklasse()`

Diese Funktion bestimmt den Altersbereich basierend auf der Altersklasse der Liga:

- **"Herren"** oder `None`: 18-35 Jahre (Standard)
- **"A-Jugend"** oder **"A"**: 17-18 Jahre
- **"B-Jugend"** oder **"B"**: 15-16 Jahre
- **"C-Jugend"** oder **"C"**: 13-14 Jahre
- **"D-Jugend"** oder **"D"**: 11-12 Jahre
- **"E-Jugend"** oder **"E"**: 9-10 Jahre
- **"F-Jugend"** oder **"F"**: 7-8 Jahre

Die Funktion ist case-insensitive und erkennt sowohl Langformen ("A-Jugend", "A Jugend") als auch Kurzformen ("A", "a").

## Geänderte Dateien

### 1. `kegelmanager/backend/init_db.py`

- **Neue Funktion** `get_age_range_for_altersklasse()` hinzugefügt (Zeile 110-140)
- **Spielergenerierung** in `create_sample_data()` angepasst (Zeile 582-590):
  - Prüft zuerst `team.league.altersklasse`
  - Fallback auf `team.is_youth_team` wenn keine Altersklasse gesetzt
  - Fallback auf Standard-Erwachsenenalter (20-35) als letzte Option

### 2. `kegelmanager/backend/extend_existing_db.py`

- **Neue Funktion** `get_age_range_for_altersklasse()` hinzugefügt (Zeile 80-110)
  - Identisch zur Version in `init_db.py` für Konsistenz
- **Spielergenerierung** für Teams ohne Spieler angepasst (Zeile 458-466)
  - Gleiche Logik wie in `init_db.py`
- **Ergänzung fehlender Attribute** angepasst (Zeile 544-586):
  - SQL-Query erweitert um `l.altersklasse`
  - Altersbestimmung basierend auf Altersklasse der Liga

## Fallback-Logik

Die Implementierung verwendet eine dreistufige Fallback-Logik:

1. **Primär**: Verwende `team.league.altersklasse` wenn vorhanden
2. **Sekundär**: Verwende `team.is_youth_team` (16-19 Jahre) wenn keine Altersklasse gesetzt
3. **Tertiär**: Verwende Standard-Herrenalter (18-35 Jahre)

Dies stellt sicher, dass auch bei fehlenden oder unvollständigen Daten sinnvolle Alterswerte generiert werden.

## Hinweis zum `is_youth_team`-Feld

Das Feld `is_youth_team` am Team-Modell wird weiterhin als Fallback verwendet, könnte aber in Zukunft obsolet werden, wenn alle Ligen eine `altersklasse` haben. Es wird empfohlen, das Feld konsistent mit der Liga-Altersklasse zu setzen.

## Beispiele

- Wenn eine Liga mit `altersklasse = "B-Jugend"` oder `altersklasse = "B"` existiert, werden alle Spieler für Teams in dieser Liga mit einem Alter zwischen 15 und 16 Jahren generiert, unabhängig vom `is_youth_team`-Flag.
- Wenn eine Liga mit `altersklasse = "Herren"` existiert (oder keine Altersklasse gesetzt ist), werden Spieler zwischen 18 und 35 Jahren generiert, sodass auch junge Erwachsene (18-jährige) in Herrenteams spielen können.

## Wichtiger Hinweis: Kurzformen in Excel-Daten

Die Excel-Datei (`Daten.xls`) verwendet **Kurzformen** für Jugendklassen (z.B. "B", "C", "D", "E" statt "B-Jugend", "C-Jugend", etc.). Die Funktion `get_age_range_for_altersklasse()` wurde entsprechend angepasst, um beide Formen zu erkennen:

- Kurzform: `"B"` → 15-16 Jahre
- Langform: `"B-Jugend"` → 15-16 Jahre
- Mit Leerzeichen: `"B Jugend"` → 15-16 Jahre

Dies stellt sicher, dass die Spielergenerierung unabhängig vom Format der Altersklasse in der Datenquelle korrekt funktioniert.

## Fehlerbehebung für bestehende Datenbanken

Wenn eine Datenbank bereits mit falschen Spieler-Altern generiert wurde (vor dieser Änderung), kann das Script `fix_player_ages.py` verwendet werden, um die Alter aller Spieler basierend auf der Altersklasse ihrer Liga zu korrigieren:

```bash
python fix_player_ages.py
```

Das Script:
1. Liest die Altersklasse jeder Liga
2. Bestimmt den korrekten Altersbereich für diese Altersklasse
3. Aktualisiert alle Spieler, deren Alter außerhalb des erwarteten Bereichs liegt
4. Zeigt eine Zusammenfassung der Änderungen an

