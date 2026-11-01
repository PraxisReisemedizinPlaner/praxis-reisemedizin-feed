#!/usr/bin/env python3
"""Fetch current CDC Travelers' Health RSS headlines to a dated Jimdo-compatible feed.

No clinical decision is computed: no vaccination recommendation, prophylaxis, drug or
individual disease-risk level is inferred. PAHO, WHO and ECDC are in the UI as
redactional source links and date-stamped manually checked examples; these sources
are NOT advertised as automatically integrated.

Deploy public_international_alerts.json via HTTPS hosting with permissive CORS,
then set INTERNATIONAL_ALERT_FEED_URL in the Jimdo HTML widget.

Run daily in GitHub Actions. Errors fail closed and do not overwrite prior JSON.
"""
from __future__ import annotations
import datetime as dt
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import json
import re
import sys
import xml.etree.ElementTree as ET

SRC='https://wwwnc.cdc.gov/travel/rss/notices.xml'
MAX_NOTICE_AGE_DAYS=28
DEST=Path(__file__).parent/'public_international_alerts.json'
COUNTRIES={
    'Colombia':'CO','Ghana':'GH','Kenya':'KE','Indonesia':'ID',
    'Costa Rica':'CR','Nicaragua':'NI','Yemen':'YE','Mayotte':'YT',
    'French Guiana':'GF','Haiti':'HT','Canada':'CA','Mexico':'MX',
    'Democratic Republic of the Congo':'CD',
    'DRC':'CD','Uganda':'UG','Saudi Arabia':'SA','Brazil':'BR',
    'India':'IN','Thailand':'TH','Vietnam':'VN','Philippines':'PH',
    'Peru':'PE','Ecuador':'EC','Bolivia':'BO','Venezuela':'VE',
    'Nigeria':'NG','France':'FR','Italy':'IT','Cambodia':'KH',
    'Turkey':'TR','Türkiye':'TR','Bangladesh':'BD','Pakistan':'PK',
    'Iran':'IR','Egypt':'EG','China':'CN',
}

def get_text(e:ET.Element, tag:str)->str:
    v=e.findtext(tag)
    return v.strip() if v else ''

def parse_date(value:str)->str:
    return parsedate_to_datetime(value).astimezone(dt.timezone.utc).date().isoformat()

def country_codes(title:str)->list[str]:
    # Conservative: only known explicit place names in the source headline;
    # generic 'Global' warnings are NOT assigned to every country.
    codes=[]
    for name,code in sorted(COUNTRIES.items(), key=lambda x:len(x[0]),reverse=True):
        if re.search(r'(?<![A-Za-z])'+re.escape(name)+r'(?![A-Za-z])', title,flags=re.I):
            if code not in codes:codes.append(code)
    return codes

def build(feed_bytes:bytes, checked_at:dt.date)->dict:
    root=ET.fromstring(feed_bytes)
    items=root.findall('.//channel/item')
    if not items:raise ValueError('CDC RSS contains no items; refusing to overwrite feed')
    alerts=[]
    for item in items:
        title=get_text(item,'title')
        url=get_text(item,'link')
        d=get_text(item,'pubDate')
        if not (title and d and url):continue
        p=urlsplit(url)
        if p.scheme!='https' or p.hostname!='wwwnc.cdc.gov' or not p.path.startswith('/travel/notices/'):
            continue
        try:
            published=parse_date(d)
            days_old=(checked_at-dt.date.fromisoformat(published)).days
        except (ValueError, TypeError, OverflowError):
            continue
        # Nur offizielle Meldungen mit Erstveröffentlichung innerhalb der letzten vier Wochen.
        # Ein alter RSS-Artikel wird durch einen täglichen Feed-Abruf NICHT aktuell.
        if not 0 <= days_old <= MAX_NOTICE_AGE_DAYS:
            continue
        countries=country_codes(title)
        if not countries:continue
        alerts.append({
            'id':'cdc-'+re.sub('[^a-z0-9]+','-',title.lower()).strip('-')[:75],
            'source':'CDC',
            'date':published,
            'countries':countries,
            'title':title[:240],
            'url':url,
            'scope':'country',
            'reviewed':False
        })
    # Eine leere Liste ist möglich und wird als solche ausgegeben: keine erfundenen Meldungen.
    return {'schemaVersion':1,'fetchedAt':checked_at.isoformat(),
            'notes':'CDC RSS headlines published within the past 28 calendar days only. Retrieval is not medical review; follow STIKO/DTG and AA guidance.',
            'alerts':alerts}

if __name__=='__main__':
    try:
        request=Request(SRC,headers={'User-Agent':'Reisemedizin-OfficialAlertMonitor/1.0 (+medical editorial review required)','Accept':'application/rss+xml, application/xml, text/xml'})
        with urlopen(request,timeout=25) as response:
            if int(response.headers.get('Content-Length') or '0')>2_000_000:raise ValueError('RSS too large')
            raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError('RSS exceeds size limit')
        data=build(raw,dt.datetime.now(dt.timezone.utc).date())
        tmp=DEST.with_suffix('.tmp')
        tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        tmp.replace(DEST)
        print('CDC alerts from last 28 days:',len(data['alerts']),'at',data['fetchedAt'])
    except Exception as exc:
        print('FAIL-CLOSED: CDC RSS update failed:',str(exc),file=sys.stderr)
        raise SystemExit(1)
