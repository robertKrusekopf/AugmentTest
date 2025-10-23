# Flaggen-Assets

Dieser Ordner enthält Flaggen-Bilder für die Nationalitäten-Anzeige.

## ⚠️ WICHTIG: Nationalitäten als Adjektive

Die Datenbank speichert Nationalitäten als **Adjektive** (z.B. "Deutsch", "Französisch"), nicht als Ländernamen!

**Richtig:**
- Deutsch (nicht "Deutschland")
- Französisch (nicht "Frankreich")
- Italienisch (nicht "Italien")
- Spanisch (nicht "Spanien")

## Verwendung

### Option 1: Bild-basierte Flaggen (Standard)
Die Anwendung lädt automatisch Flaggen-Bilder aus diesem Ordner. Bei Fehler wird automatisch auf CSS-Flaggen zurückgegriffen.

### Option 2: CSS-basierte Flaggen (Fallback)
Wenn keine Bild-Dateien vorhanden sind, werden CSS-basierte Flaggen verwendet, die direkt im Code definiert sind.

1. Laden Sie Flaggen-Bilder herunter (z.B. von https://flagicons.lipis.dev/ oder https://github.com/lipis/flag-icons)
2. Speichern Sie sie in diesem Ordner: `kegelmanager/frontend/src/assets/flags/`
3. Benennen Sie die Dateien nach dem **ISO-Ländercode**: `{country-code}.svg` oder `{country-code}.png`
4. Die Anwendung lädt automatisch die Bilder (SVG wird bevorzugt, PNG als Fallback)

## Benötigte Flaggen-Dateien

Für die vollständige Unterstützung benötigen Sie folgende Dateien (SVG oder PNG):

| Dateiname | Nationalität (in DB) | Land |
|-----------|---------------------|------|
| `de.svg` | Deutsch | Deutschland |
| `at.svg` | Österreichisch | Österreich |
| `ch.svg` | Schweizerisch | Schweiz |
| `nl.svg` | Niederländisch | Niederlande |
| `be.svg` | Belgisch | Belgien |
| `fr.svg` | Französisch | Frankreich |
| `it.svg` | Italienisch | Italien |
| `es.svg` | Spanisch | Spanien |
| `pl.svg` | Polnisch | Polen |
| `cz.svg` | Tschechisch | Tschechien |
| `dk.svg` | Dänisch | Dänemark |
| `se.svg` | Schwedisch | Schweden |
| `no.svg` | Norwegisch | Norwegen |
| `fi.svg` | Finnisch | Finnland |
| `ru.svg` | Russisch | Russland |
| `us.svg` | Amerikanisch | USA |
| `ca.svg` | Kanadisch | Kanada |
| `au.svg` | Australisch | Australien |
| `jp.svg` | Japanisch | Japan |
| `kr.svg` | Südkoreanisch | Südkorea |
| `cn.svg` | Chinesisch | China |
| `br.svg` | Brasilianisch | Brasilien |
| `ar.svg` | Argentinisch | Argentinien |
| `mx.svg` | Mexikanisch | Mexiko |
| `tr.svg` | Türkisch | Türkei |
| `gr.svg` | Griechisch | Griechenland |
| `pt.svg` | Portugiesisch | Portugal |
| `hr.svg` | Kroatisch | Kroatien |
| `rs.svg` | Serbisch | Serbien |
| `si.svg` | Slowenisch | Slowenien |
| `hu.svg` | Ungarisch | Ungarn |
| `ro.svg` | Rumänisch | Rumänien |
| `bg.svg` | Bulgarisch | Bulgarien |
| `ua.svg` | Ukrainisch | Ukraine |
| `sk.svg` | Slowakisch | Slowakei |
| `lt.svg` | Litauisch | Litauen |
| `lv.svg` | Lettisch | Lettland |
| `ee.svg` | Estnisch | Estland |

**Beispiel:** Wenn Sie `fr.svg` in diesen Ordner legen, wird die französische Flagge für Spieler mit Nationalität "Französisch" angezeigt.

## Wie funktioniert das System?

Die `FlagIcon` Komponente lädt automatisch Flaggen-Bilder:

1. **Zuerst**: Versucht `{country-code}.svg` zu laden
2. **Fallback 1**: Wenn SVG fehlt, versucht `{country-code}.png`
3. **Fallback 2**: Wenn beide fehlen, zeigt CSS-basierte Flagge

**Beispiel:**
- Spieler hat Nationalität "Französisch" in der Datenbank
- System sucht nach `fr.svg` in diesem Ordner
- Wenn gefunden: Zeigt die SVG-Flagge an
- Wenn nicht gefunden: Zeigt CSS-basierte französische Flagge (Blau-Weiß-Rot)

## Aktueller Status

✅ Die Anwendung ist bereits auf **Bild-Modus** eingestellt (`mode="image"`).

**Legen Sie einfach Flaggen-Dateien in diesen Ordner und sie werden automatisch verwendet!**

## Empfohlene Quellen für Flaggen-Bilder

1. **Flag Icons**: https://github.com/lipis/flag-icons
2. **Flagpedia**: https://flagpedia.net/
3. **Country Flags API**: https://countryflagsapi.com/

## Bildformat-Empfehlungen

- **Format**: PNG oder SVG
- **Größe**: 32x24px oder 64x48px
- **Qualität**: Hochauflösend für Retina-Displays
- **Dateigröße**: Unter 5KB pro Flagge
