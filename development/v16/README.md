# ReiseCheck V16 – Entwicklungsbereich

**Stand:** 15.11.2026 · **Status:** kontrollierte Entwicklungsprofile; nur ausdrücklich ärztlich freigegebene Datensätze werden veröffentlicht.

Dieser Entwicklungsbereich dient der strukturierten Übernahme und anschließenden fachlichen Prüfung von Länderprofilen. Die alte Datei `country_profiles_v1.json` bleibt archiviert; die öffentliche Jimdo-Version V22 liest ausschließlich den medizinisch gefilterten V16-Public-Feed. Ungeprüfte Profile aus dieser Entwicklungsdatei dürfen weiterhin nicht in die Patientenansicht gelangen.

## Inhalt

- `country_profiles_draft_v16.json`: zehn Länder (Thailand, Indonesien, Tansania, Kenia, Vietnam, Indien, Ägypten, Marokko, Österreich, Türkei). Frühere Einträge aus ReiseCheck V15 sind **nur im Feld `legacySnapshot`** als ungeprüfte historische Vorschläge dokumentiert.
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

Die GitHub-Pages-Automatisierung veröffentlicht den V16-Feed nach erfolgreichen Tests und Änderungen auf `main`. Die öffentliche Jimdo-Oberfläche wurde am 15.11.2026 vom Praxisinhaber auf V22 umgestellt und ruft den V16-Public-Feed automatisch bei Seitenaufruf ab. Für zusätzliche Länderprofile ist kein neuer Jimdo-Code erforderlich.

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

- Marokko (MA) und Österreich (AT) wurden am 11.11.2026 nach ärztlicher Freigabe veröffentlicht; erneute Prüfung spätestens 11.01.2027.
- Thailand, Indonesien, Ägypten und Türkei (TH/ID/EG/TR) wurden am **15.11.2026 ausdrücklich ärztlich freigegeben** (siehe Nachtrag in `clinical_review_TH_ID_EG_TR_2026-11-15.md`). Neue Überprüfung bis 15.01.2027. Insgesamt sind **10 Länder erfasst, 6 veröffentlicht und 4 gesperrt** (TZ, KE, VN, IN).
- Die Herkunft und Wiederverwendung externer Quellen weiter prüfen; DTG-Karten ausschließlich verlinken. TH/ID liefern ohne Ortsauflösung keine automatisch abgeleitete Medikamentenempfehlung.
- Bei neuer ausdrücklicher ärztlicher Freigabe automatischen Export, GitHub-Tests und öffentlichen ReiseCheck überprüfen. Achtung: Das aktuelle V22-Widget klassifiziert freie Regionseingaben **nicht** automatisch in Malaria-Unterregionen; bei Thailand/Indonesien dürfen daher nur konservative allgemeine Regionalhinweise ohne automatische Arzneimittelempfehlung ausgegeben werden.


## Geplante Orts-/Regionserkennung

Zur neuen Orts-/Regionserkennung (inklusive ärztlich verifizierter regionaler Malariadaten, sicherer Mehrfachauswahl und medizinischem Freigabegate) siehe [GitHub-Issue #10](https://github.com/PraxisReisemedizinPlaner/praxis-reisemedizin-feed/issues/10). Bis zur Umsetzung wertet die V22-Jimdo-Oberfläche Freitexte nicht als medizinisch freigegebene Gebietszuordnung aus. Die Länderfreigabe bleibt davon unabhängig.

## V23 – Regionale Ortsauswahl (Entwicklungs-/Testfassung, 15.11.2026)

**Status:** Die bisherige produktive Jimdo-Version ist weiterhin **V22**. V23 ist zunächst nur als separate GitHub-Pages-Vorschau gedacht, nicht als öffentliche medizinische Regionalfreigabe.

- `region_profiles_draft_v1.json`: 25 geografische Einträge für Thailand und Indonesien (inklusive getrenntem Little Koh Chang/Ranong und Ko Chang/Trat). **Alle sind klinisch unfreigegeben.**
- `export_public_regions_v1.py`: veröffentlicht ausgewählte Ortsnamen/Synonyme ohne klinische Risikodaten. Regionale medizinische Aussagen erscheinen ausschließlich nach eigener ärztlicher Regionsfreigabe, aktuellem Freigabedatum, geprüften externen Quellenlinks und gültiger Landesfreigabe. Keine Übernahme von DTG-Karten/-Datensammlungen.
- `test_regions.py`: automatische Tests der Risiko-Sperre, Länderabhängigkeit, Ablaufdaten, Quellenrechte und Veröffentlichungskontrollen.
- `clinical_review_regions_TH_ID_2026-11-15.md`: fachlicher Prüfbogen mit offen dokumentierten AA/CDC-Unterschieden.
- `website/ReiseCheck_Jimdo_V23.html`: Ortsvorschläge, Checkbox-unabhängige Mehrfach-Chips, Tastatursteuerung, nicht erkannter Freitext bleibt neutral, Hinweis zur ausstehenden medizinischen Regionalprüfung.
- Der Public Feed `region_directory_public_v1.json` wird über GitHub Pages ausgeliefert, die V23-Testadresse lautet `reisecheck-v23-jimdo-test.html`.

**Ausdrücklich kein Live-Rollout nach Jimdo**: Erst nach Sichtung der Benutzeroberfläche, Prüfung der Ortsdaten und fachlicher Regionsfreigaben kann die Praxis V23 einmalig einbinden. Die sechs bereits freigegebenen Länderprofile bleiben unabhängig davon unverändert. GitHub-Issue #10 dokumentiert die offenen Schritte.
