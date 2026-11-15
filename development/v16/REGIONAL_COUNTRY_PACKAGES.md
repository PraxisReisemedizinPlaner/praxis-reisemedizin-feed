# Länderpakete und regionale Quelleninformationen

Stand: 15.11.2026. Autorisierte Umstellung durch Dr. med. Sebastian Münster im Chat: Eine gültige ärztliche Länderfreigabe umfasst die regelbasierte Darstellung aktueller regionaler Quelleninformationen. Eine eigene ärztliche Bestätigung jedes Ortes entfällt.

## Datenfluss
- Länderfreigabe: `country_profiles_draft_v16.json`, einschließlich Freigabestatus und Gültigkeitszeitraum.
- Geografische Identitäten: `region_profiles_draft_v1.json`.
- Redaktionell zugeordnete AA-/CDC-Quelleninformationen: `region_source_packages_v2.json`.
- Export: `export_public_regions_v2.py` → `region_directory_public_v2.json`.
- V24.2 lädt den V2-Feed. V23 und der bisherige V1-Feed bleiben kompatibel mit dem historischen Einzelfreigabemodell.

## Keine Einzelfreigabe
`clinicalReview` und `publicationAllowed` des einzelnen Geografieeintrags sind für den V2-Export keine Voraussetzungen. Die vier früheren Einzelfreigaben bleiben als Historie bestehen, werden nicht nachträglich auf andere Orte übertragen. V2 bezeichnet Datensätze als `source_based`, niemals als einzeln ärztlich geprüft.

Eine Freigabe des Landes allein erzeugt keine fehlenden lokalen Fakten. Neue eindeutige Orte benötigen eine geografische Zuordnung und belegte Quellenzusammenfassung. Sie benötigen keinen zusätzlichen ärztlichen Klick.

## Quellen und Ausnahmen
`supported`: aktuelle, eindeutig zugeordnete Quellen erlauben die hinterlegte Darstellung.
`source_conflict`: Quellenabweichung mit Erläuterung, ohne automatisch zugewiesene Risikostufe.
`route_required`: räumliche Aussage zu grob, konkrete Reiseroute erforderlich, ohne Risikostufe.
Fehlende, ungültige oder abgelaufene Quellen oder Länderfreigaben erzeugen `source_unavailable`.

Der öffentliche Feed enthält `exceptions` als Ausnahmeliste. Diese Liste beschreibt Quellen-/Routenprobleme und ist keine Liste verpflichtender ärztlicher Ortsfreigaben. Quellen und Geltungsbereich müssen bei redaktionellen Aktualisierungen mitgepflegt werden. Es gibt keinen automatischen KI-Import beliebiger Ortsnamen und keinen automatischen Volltextabgleich der AA-/CDC-Malariaempfehlungen. Der tägliche Veröffentlichungsworkflow prüft die vorhandenen Daten und deren Ablauf; aktuelle CDC-Gesundheitsmeldungen werden separat abgerufen.

Keine strukturierten DTG-Daten, keine Kartenübernahme, keine automatische konkrete Medikamentenauswahl oder Dosierung. Freitext erzeugt keine lokale Risikoeinstufung. Quelleninformationen tragen ein echtes Abruf-/Abgleichdatum; ein Deployment verlängert dieses Datum nicht.

## Aktueller Umfang
25 Orte aus Thailand und Indonesien: 7 eindeutig quellenbasierte Einordnungen, 18 nachvollziehbare Quellen- oder Routenhinweise. Die bisherigen individuellen Freigabestatus werden nicht als Voraussetzung verwendet.

## Prüfungen
`python -m unittest discover -s development/v16 -p 'test_*.py' -v`
`python development/v16/validate_jimdo_v24.py`
`python development/v16/test_v24_browser.py` (Playwright, Desktop/Mobil)
