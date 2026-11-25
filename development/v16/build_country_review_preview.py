#!/usr/bin/env python3
"""Render the exact four country drafts for the physician's country-package decision."""
import argparse
import html
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
CODES=("PR","VI","TT","FK")
OTHER_REVIEW_PACKAGES=(("BS","BB","DM","GD"),("AG","LC","KN","VC"),("AD","MC","SM","LI"),("FJ","WS","TO","TV"),("CK","NU","NR","KI"),("MH","FM","PW","GU"),("MP","AS","PF","NC"),("WF","GP","MQ","RE"),("MF","BL","PM","BM"),("AI","VG","KY","TC"),("MS","SX","AW","CW"))
def esc(s): return html.escape(str(s),quote=True)
def bullets(items): return "<ul>"+"".join("<li>"+esc(v)+"</li>" for v in items)+"</ul>"
def render(data,codes=CODES):
    checked=max(data["countries"][code]["sourceReview"]["researchCheckedAt"] for code in codes)
    next_review=min(data["countries"][code]["sourceReview"]["proposedNextReviewDate"] for code in codes)
    cards=[]
    for code in codes:
        p=data["countries"][code]; v=p["vaccineAssessment"]; m=p["malariaAssessment"]
        released=p["publicationAllowed"] is True and p["medicalReview"]["status"]=="approved"
        contacts="".join("<h4>"+esc(x["title"])+"</h4><p>"+esc(x["address"])+"<br>Telefon: "+esc(x["phone"])+("<br>Notfall: "+esc(x["emergency"]) if x.get("emergency") else "")+"</p><p>"+esc(x["scope"])+"</p><p><a href='"+esc(x["url"])+"' target='_blank' rel='noopener noreferrer'>Originalkontakt öffnen ↗</a></p>" for x in p["missions"]["verifiedEntries"])
        sources="".join("<li><a href='"+esc(u)+"' target='_blank' rel='noopener noreferrer'>"+esc(u)+"</a></li>" for u in p["sourceReview"]["evidenceLinks"])
        regional=p["sourceReview"].get("regionalReview",[])
        regional_html=("<details><summary>Regionale Hinweise ("+str(len(regional))+")</summary>"+bullets(regional)+"</details>") if regional else ""
        cards.append("<article id='"+code+"'><div class='head'><h2>"+esc(p["name"])+"</h2><span class='badge'>"+("Freigegeben" if released else "Zur Länderfreigabe vorbereitet")+"</span></div><h3>Impfungen</h3><p><strong>Basis-Reiseimpfungen / Impfstatus:</strong> "+esc(" · ".join(v["forAll"]) or "Keine zusätzliche allgemeine Reiseimpfung nach STIKO hinterlegt; Standardimpfschutz separat prüfen.")+"</p><p><strong>Nach individueller Indikation:</strong> "+esc(" · ".join(v["riskBased"]))+"</p><h4>Einreise und Route</h4>"+bullets(v["entryRequirements"]+v["routeDependent"])+regional_html+"<h3>Malaria</h3><p>"+esc(m["clinicalRecommendation"])+"</p>"+bullets(m["regions"])+"<details><summary>Kontakte, Quellen und fachliche Prüfpunkte</summary>"+contacts+"<h4>Zusätzliche Prüfpunkte</h4>"+bullets(p["sourceReview"]["researchNotes"])+"<h4>Quellen, abgeglichen am "+esc(p["sourceReview"]["researchCheckedAt"])+"</h4><ul>"+sources+"</ul></details></article>")
    return """<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>ReiseCheck – Länderpaket zur ärztlichen Prüfung</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f0f5f7;color:#243b46;font:16px/1.6 system-ui,sans-serif}main{max-width:1060px;margin:auto;padding:28px 18px 50px}header,article{background:white;border:1px solid #d8e4e9;border-radius:16px;padding:25px;margin:0 0 20px}header{border-top:6px solid #6592a7}h1{font-size:30px;line-height:1.2;margin:8px 0 14px}h2{font-size:25px;margin:0;color:#234556}h3{margin:24px 0 8px;font-size:20px;color:#234556}h4{margin:18px 0 6px}p{margin:8px 0}.head{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap}.badge{padding:5px 12px;background:#fff3df;border-radius:20px;font-size:13px;font-weight:700}nav{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}nav a{background:#e5f0f5;border-radius:9px;padding:8px 14px;text-decoration:none;color:#234556}a{color:#245b76;overflow-wrap:anywhere}li{margin:6px 0}details{border-top:1px solid #d8e4e9;margin-top:20px;padding-top:15px}summary{cursor:pointer;font-weight:700}.note{background:#fff3df;padding:14px;border-radius:10px}.brand{font-weight:700;color:#527f92}small{color:#566c75}@media print{body{background:white}main{padding:0}header,article{break-inside:avoid}nav{display:none}}
    </style><main><header><div class="brand">Dr. Münster | Dein Hausarzt · ReiseCheck</div><h1>Vier Länder als gemeinsames Freigabepaket</h1><p class="note"><strong>Ärztliche Prüfvorschau – keine Patientenempfehlung für noch nicht freigegebene Länder.</strong> Die Inhalte werden erst nach der Länderfreigabe in den Patientenfeed übernommen. Die medizinische Freigabe erfolgt im Chat, nicht durch das Öffnen dieser Seite.</p><nav>"""+"".join("<a href='#"+c+"'>"+esc(data["countries"][c]["name"])+"</a>" for c in codes)+"""</nav><p>Prüfumfang: Impfungen, Einreisebedingungen, Malaria, Quellenabweichungen und amtliche Kontakte. STIKO-Standardimpfungen werden im ReiseCheck zusätzlich berücksichtigt. „Basis“ bedeutet Impfstatus prüfen, keine erneute Impfung ohne Anamnese.</p><p>Bei Dengue gilt die individuelle STIKO-Indikation, insbesondere eine gesicherte frühere Dengueinfektion. Für Chikungunya sind aktuelle Indikation, Alter und Impfstoff-Fachinformation zu beachten. Keine der Listen ist eine pauschale Verordnung. Medikamentenwahl und Dosierungen sind hier nicht automatisiert.</p><small>Quellenabgleich: """+esc(checked)+""" · Vorgeschlagene nächste Länderprüfung: """+esc(next_review)+""" · Regionale Quelleninformationen folgen nach Freigabe dem vereinbarten Länderpaketmodell.</small></header>"""+"".join(cards)+"</main></html>"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--batch-copy",action="store_true")
    args=ap.parse_args()
    data=json.loads((HERE/"country_profiles_draft_v16.json").read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    html=render(data)
    args.output.write_text(html,encoding="utf-8")
    if args.batch_copy:
        for codes in (CODES, *OTHER_REVIEW_PACKAGES):
            suffix="-".join(codes).lower()
            batch_path=args.output.with_name(f"{args.output.stem}-{suffix}{args.output.suffix}")
            batch_path.write_text(render(data,codes),encoding="utf-8")
if __name__=="__main__": main()
