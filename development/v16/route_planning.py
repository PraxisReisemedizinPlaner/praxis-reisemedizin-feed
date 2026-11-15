"""Every country package must explicitly assess regional route differences."""
from datetime import date
from urllib.parse import urlparse
ALLOWED_TOPICS={"malaria","dengue","yellow_fever","tick_borne","other"}
def validate_route_assessment(code,profile,geography=None,sources=None):
    a=profile.get("routeAssessment")
    if not isinstance(a,dict): raise ValueError(code+": regional route assessment missing")
    try: date.fromisoformat(a.get("assessedAt",""))
    except (TypeError,ValueError): raise ValueError(code+": regional assessment date invalid")
    needed=a.get("regionalSelectionRequired")
    if not isinstance(needed,bool): raise ValueError(code+": regional decision missing")
    topics=a.get("topics");ids=a.get("regionIds");urls=a.get("sourceUrls")
    if not isinstance(topics,list) or any(t not in ALLOWED_TOPICS for t in topics): raise ValueError(code+": invalid route topics")
    if not isinstance(ids,list) or len(ids)!=len(set(ids)) or any(not isinstance(i,str) or not i.startswith(code+"-") for i in ids): raise ValueError(code+": invalid region IDs")
    if not isinstance(a.get("reason"),str) or len(a["reason"])<15: raise ValueError(code+": route decision not explained")
    if not isinstance(urls,list) or not urls or any(not isinstance(u,str) or urlparse(u).scheme!="https" for u in urls): raise ValueError(code+": route sources missing")
    if profile.get("malariaAssessment",{}).get("riskLevel")=="regional" and not needed: raise ValueError(code+": regional malaria requires region selection")
    if needed and (len(ids)<2 or not topics): raise ValueError(code+": regional package incomplete")
    if geography is not None:
        rows={r["id"]:r for r in geography["regions"]}
        source_rows={r["id"]:r for r in sources["regions"]} if sources else {}
        for rid in ids:
            if rid not in rows or rows[rid]["country"]!=code: raise ValueError(code+": region absent from catalogue: "+rid)
            r=source_rows.get(rid)
            if not r or r.get("country")!=code or r.get("scope")!=rows[rid]["name"] or r.get("status") not in {"supported","source_conflict","route_required"} or not r.get("summary") or len(r.get("sourceUrls",[]))<2:
                raise ValueError(code+": region sources incomplete: "+rid)
    return a
