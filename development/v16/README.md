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

## Veröffentlichung V16 – als Entwurf implementiert

`export_public_v16.py` erzeugt eine **gesonderte** JSON-Datei `country_profiles_public_v16.json`. Darin werden nur freigegebene und nicht abgelaufene ärztliche Profile ausgegeben. Für andere Länder werden ausschließlich Name, Ländercode und „medical_review_required“ veröffentlicht. **Die vorhandene V1-Datei wird weder gelöscht noch überschrieben.**

Die aktualisierte GitHub-Pages-Automatisierung erzeugt den V16-Feed **erst nach dem Zusammenführen dieses Entwicklungszweigs nach main**. Vorher erfolgt keine Änderung am bestehenden Live-Feed. Die Jimdo-Oberfläche verwendet den V16-Feed **noch nicht automatisch**; die einmalige Umstellung muss nach medizinischer Prüfung erfolgen.

Der Export ist technisch „fail-closed“: fehlende Quellenfreigaben, nicht freigegebene Impf-/Malaria-Aussagen oder eine unzulässige DTG-Datennutzung verhindern eine Veröffentlichung. Das ist keine Aussage über die medizinische Richtigkeit.

### Testen

```bash
python development/v16/validate_v16.py
python -m unittest discover -s development/v16 -p 'test_*.py' -v
python development/v16/export_public_v16.py --output /tmp/country_profiles_public_v16.json
```

GitHub Actions prüft diese Schritte zusätzlich im Pull Request.

### Ärztliche Freigabe je Land

- Identität, Reiseroute, Regionen, Saison, Aufenthaltsdauer und Reiseart sachgerecht berücksichtigen. Länderprofile ersetzen keine individuelle Beratung.
- Aktuelle Primärquellen überprüfen, exakte Links, Datum und Nutzungsrechte dokumentieren.
- Erst bei vollständiger inhaltlicher Prüfung `vaccineAssessment.status`, `malariaAssessment.status` und `missions.status` auf `approved` setzen.
- `medicalReview` vollständig mit `status: approved`, `reviewer`, `reviewedAt`, `nextReviewDate` sowie geprüften `approvedSources` dokumentieren. Pro Quelle wird `reuseRightsChecked: true` erst nach tatsächlicher rechtlicher Prüfung hinterlegt.
- `publicationAllowed: true` erst als letzten Schritt setzen.
- Freigegebene Informationen können im V16-Feed nach dem nächsten GitHub-Pages-Deployment verfügbar sein. Die Jimdo-Einbindung muss ausdrücklich auf den neuen Feed zeigen.

### Nicht erlaubt

- Eine KI darf keine ärztliche oder urheberrechtliche Freigabe selbst setzen.
- DTG-Daten nicht strukturiert übernehmen; nur auf Originalkarten verlinken.
- Fehlen Daten, dürfen sie nicht durch „kein Risiko“ oder allgemeine Entwarnung ersetzt werden.
- Keine sensiblen Patientendaten oder personenbezogenen Konsultationsdaten in GitHub ablegen.

## Nächste fachliche Arbeit

- Zuerst zwei Musterländer (Marokko und Österreich) gegen Quellen, Einreisevorschriften und Auslandsvertretungen vollständig prüfen.
- Danach die sieben bisherigen Profile Land für Land prüfen.
- Quellenrechte und die Zuverlässigkeit regionaler Malariaangaben prüfen; DTG-Karten nur verlinken.
- Erst danach Datenexport, Tests, GitHub-Pages-Anbindung und Jimdo-Freigabe.

