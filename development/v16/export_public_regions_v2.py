#!/usr/bin/env python3
"""Source-based regions inherit country approval, never an invented local physician sign-off."""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse

HERE=Path(__file__).resolve().parent
STATUS={"supported","source_conflict","route_required"}
PREVENTION={"none","exposure_only","standby_consider","chemoprophylaxis_consider","regional_assessment_required"}
def day(value):
    try: return date.fromisoformat(value)
    except (TypeError,ValueError): return None
def valid_window(start,end,today):
    a,b=day(start),day(end)
    return bool(a and b and a<=today<=b)
def source_url(value):
    if not isinstance(value,str): return False
    p=urlparse(value)
    return p.scheme=="https" and p.hostname in {"www.auswaertiges-amt.de","wwwnc.cdc.gov","www.cdc.gov"} and not p.username and not p.password and p.port in (None,443)
def country_valid(parent,today):
    review=parent.get("medicalReview") or {}
    return parent.get("publicationAllowed") is True and review.get("status")=="approved" and bool(review.get("reviewer")) and valid_window(review.get("reviewedAt"),review.get("nextReviewDate"),today)
def build_public_regions(geography,countries,packages,as_of=None):
    today=as_of or datetime.now(timezone.utc).date()
    if packages.get("schemaVersion")!=2 or packages.get("approvalModel")!="country_package":
        raise ValueError("Country-package model missing")
    for key in ("noDTGStructuredReuse","noAutomaticRiskFromFreitext","noMedicationNames","requireValidCountryApproval"):
        if packages.get("rules",{}).get(key) is not True: raise ValueError("Missing rule: "+key)
    auth=packages.get("authorization") or {}
    if not auth.get("authorizedBy") or not day(auth.get("recordedAt")) or day(auth["recordedAt"])>today:
        raise ValueError("Country-package authorization missing")
    rows=geography.get("regions")
    if not isinstance(rows,list) or not rows: raise ValueError("Geography missing")
    source_rows=packages.get("regions")
    if not isinstance(source_rows,list): raise ValueError("Sources missing")
    by_id={}
    for r in source_rows:
        if not isinstance(r,dict) or not isinstance(r.get("id"),str) or r["id"] in by_id: raise ValueError("Duplicate source ID")
        by_id[r["id"]]=r
    out=[]; seen=set(); exceptions=[]
    for row in rows:
        rid,code=row.get("id"),row.get("country")
        if not isinstance(rid,str) or not isinstance(code,str) or not rid.startswith(code+"-") or rid in seen: raise ValueError("Invalid geography ID")
        seen.add(rid)
        if row.get("kind") not in ("city","island","region") or not isinstance(row.get("name"),str): raise ValueError("Invalid geography")
        aliases=row.get("aliases")
        if not isinstance(aliases,list) or len(aliases)>15 or not all(isinstance(a,str) and len(a)<100 for a in aliases): raise ValueError("Invalid aliases")
        item={k:row[k] for k in ("id","country","name","kind","aliases")}
        item["clinicalStatus"]="source_unavailable"
        parent=countries.get("countries",{}).get(code,{})
        r=by_id.get(rid)
        reason="source_missing"
        if not country_valid(parent,today):
            reason="country_approval_unavailable"
        elif r:
            urls=r.get("sourceUrls")
            state=r.get("status")
            source_ok=(r.get("country")==code and r.get("scope")==row["name"] and state in STATUS
                and valid_window(r.get("checkedAt"),r.get("nextSourceCheckDate"),today)
                and r.get("reuseRightsChecked") is True
                and isinstance(urls,list) and len(urls)>=2 and all(source_url(u) for u in urls)
                and any(urlparse(u).hostname=="www.auswaertiges-amt.de" for u in urls)
                and any(urlparse(u).hostname in {"wwwnc.cdc.gov","www.cdc.gov"} for u in urls)
                and isinstance(r.get("summary"),str) and 10<len(r["summary"])<2500
                and not r.get("medicationName") and not r.get("dose"))
            if source_ok:
                expiry=min(parent["medicalReview"]["nextReviewDate"],r["nextSourceCheckDate"])
                item.update(approvalScope="country_package",nextReviewDate=expiry,sources=urls,sourceCheckedAt=r["checkedAt"])
                if state=="supported":
                    if r.get("riskLevel") not in ("none","low","moderate","high") or r.get("preventionType") not in PREVENTION:
                        raise ValueError("Invalid supported assessment: "+rid)
                    item["clinicalStatus"]="source_based"
                    item["malaria"]={"riskLevel":r["riskLevel"],"preventionType":r["preventionType"],"clinicalRecommendation":r["summary"]}
                else:
                    if r.get("riskLevel") is not None or r.get("preventionType") is not None:
                        raise ValueError("Unresolved source must not assign risk: "+rid)
                    item["clinicalStatus"]=state
                    item["sourceNotice"]=r["summary"]
                reason=state
            else: reason="source_invalid_or_expired"
        if item["clinicalStatus"]!="source_based":
            item["exceptionReason"]=reason
            exceptions.append({"id":rid,"country":code,"reason":reason})
        out.append(item)
    if set(by_id)-seen: raise ValueError("Source references unknown geography")
    return {"schemaVersion":2,"dataset":"praxis-dr-muenster-regions-public-v2",
        "approvalModel":"country_package","generatedAt":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "geographyCount":len(out),"sourceBasedCount":sum(r["clinicalStatus"]=="source_based" for r in out),
        "exceptionCount":len(exceptions),"exceptions":exceptions,"regions":out,
        "notice":"Regionale Quelleninformationen unter der Länderfreigabe; keine gesonderte ärztliche Prüfung jedes Ortes."}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    read=lambda n:json.loads((HERE/n).read_text(encoding="utf-8"))
    data=build_public_regions(read("region_profiles_draft_v1.json"),read("country_profiles_draft_v16.json"),read("region_source_packages_v2.json"))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_name(args.output.name+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(args.output)
    print(f"Country-package regions: {data['sourceBasedCount']} source-based, {data['exceptionCount']} exceptions")
if __name__=="__main__": main()
