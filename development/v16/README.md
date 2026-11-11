# ReiseCheck V16 – Entwicklungsbereich

**Stand:** 11.11.2026 · **Status:** Entwurf, NICHT für Patienten freigegeben.

Dieser Entwicklungsbereich dient der strukturierten Übernahme und anschließenden fachlichen Prüfung von Länderprofilen. Die Live-Daten `country_profiles_v1.json`, der produktive CDC-Feed und die Jimdo-Test- bzw. öffentliche Seite werden **nicht** verändert.

## Inhalt

- `country_profiles_draft_v16.json`: neun Länder (Thailand, Indonesien, Tansania, Kenia, Vietnam, Indien, Ägypten, Marokko, Österreich). Frühere Einträge aus ReiseCheck V15 sind **nur im Feld `legacySnapshot`** als ungeprüfte historische Vorschläge dokumentiert.
- `malaria_sources_registry.json`: 17 Referenzquellen; keine Forschungs- oder DTG-Daten werden automatisch importiert.
- `validate_v16.py`: Strukturtest mit gesperrten Empfehlungen für alle nicht freigegebenen Profile.

## Regeln für die ärztliche Freigabe

1. Reiseroute, Regionen/Höhenlage, Reisedauer, Aufenthaltsart sowie relevante Patientendaten bei jeder konkreten Empfehlung berücksichtigen.
2. Impfempfehlungen und Einreiseanforderungen anhand geeigneter **aktueller Primärquellen** überprüfen, exakte Quelle und Prüfdatum dokumentieren; Handelsnamen und Impfschemata gesondert gegen zugelassene Fachinformationen abgleichen.
3. Für Malaria keine automatisierte Empfehlung allein aus Forschung, Resistenzdaten oder landesweiten Fallzahlen ableiten. Regionale Risiken, Art der Prophylaxe und Notfall-Selbsttherapie ärztlich beurteilen.
4. **DTG:** Karten und strukturierte DTG-Daten nicht kopieren, nicht mittels KI nachbilden oder automatisch extrahieren; ausschließliche Verlinkung. Schriftliche Antwort der DTG liegt der Praxis vor.
5. Nutzungsrechte jedes externen Datenfeeds prüfen. Ein erfolgreicher technischer Abruf ist **keine** medizinische Freigabe.
6. Für jede tatsächliche Freigabe Reviewer, Datum, Primärquellen, Gültigkeits-/Revisionsdatum und konkrete Indikation festhalten.
7. Fehlende oder veraltete Daten müssen **neutral** erscheinen: „Nicht ausreichend geprüft – reisemedizinische Beratung erforderlich“; niemals automatisch „kein Risiko“ angeben.
8. Die Freigabelogik muss **serverseitig** bzw. bereits bei der Veröffentlichung der JSON-Datei durchgesetzt werden. Ein `publicationAllowed`-Flag allein ist keine Zugangskontrolle und darf nicht die finale Freigabekontrolle ersetzen.

## Prüfung

Aus dem Repository-Stamm:

```bash
python development/v16/validate_v16.py
```

Die Validierung prüft nur Datenstruktur und Sicherheitsstatus, **nicht** die medizinische Richtigkeit und nicht die Rechte der verlinkten Quellen.

## Veröffentlichung – noch nicht implementiert

Derzeit gibt es absichtlich **keinen** neuen Release-Job. Erst nach separatem Review bauen wir einen Export, der ungeprüfte Profile und `legacySnapshot` vollständig entfernt und ausschließlich freigegebene medizinische Informationen in eine eigene Datei überträgt. Erst danach wird Jimdo auf den neuen geprüften Feed umgestellt.

## Nächste fachliche Arbeit

- Zuerst zwei Musterländer (Marokko und Österreich) gegen Quellen, Einreisevorschriften und Auslandsvertretungen vollständig prüfen.
- Danach die sieben bisherigen Profile Land für Land prüfen.
- Quellenrechte und die Zuverlässigkeit regionaler Malariaangaben prüfen; DTG-Karten nur verlinken.
- Erst danach Datenexport, Tests, GitHub-Pages-Anbindung und Jimdo-Freigabe.

