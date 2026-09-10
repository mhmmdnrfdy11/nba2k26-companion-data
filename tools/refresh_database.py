import json, hashlib, re, os
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
UA = 'NBA2K26-Companion-Cloud-Master/2.0 (+https://github.com/mhmmdnrfdy11/nba2k26-companion-data)'
URLS = {
    'animations': 'https://nba2kw.com/nba-2k26-all-animation-requirements',
    'jumpshots': 'https://nba2kw.com/all-nba-2k26-jumpshot-requirements',
    'badges': 'https://nba2kw.com/nba-2k26-badge-requirements',
}


def clean(v):
    return re.sub(r'\s+', ' ', str(v or '')).strip()


def heading_before(table):
    h = table.find_previous(['h2','h3','h4'])
    return clean(h.get_text(' ', strip=True)) if h else ''


def height_from_heading(h):
    x = h.lower()
    if 'under 6’5' in x or "under 6'5" in x:
        return "under 6'5"
    if '6’5' in x and '6’9' in x:
        return "6'5-6'9"
    if '6’10' in x or "6'10" in x:
        return "6'10-7'4"
    return ''


def fetch(url):
    r = requests.get(url, headers={'User-Agent': UA}, timeout=45)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def parse_animations():
    soup = fetch(URLS['animations'])
    out=[]
    for table in soup.find_all('table'):
        rows=table.find_all('tr')
        if not rows: continue
        headers=[clean(c.get_text(' ', strip=True)) for c in rows[0].find_all(['th','td'])]
        if not headers or headers[0].lower() not in ('animation','animations'): continue
        category=heading_before(table)
        category=re.sub(r'\s+Requirements$','',category,flags=re.I) or 'Animation'
        for tr in rows[1:]:
            cells=[clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td','th'])]
            if len(cells)<2: continue
            rec={'type':category,'name':cells[0]}
            vals=dict(zip(headers[1:],cells[1:]))
            mins=vals.get('Min',''); maxs=vals.get('Max','')
            if mins or maxs:
                rec['height']=f"{mins}-{maxs}".replace('”','"').replace('’',"'")
            req=[]
            for k,v in vals.items():
                if k.lower() in ('min','max') or not v or v.lower() in ('any','n/a'): continue
                req.append(f'{k}: {v}')
            rec['requirement']=' | '.join(req) if req else 'No attribute requirement'
            rec['status']='verified_secondary'
            rec['source']='NBA2KW'
            rec['source_url']=URLS['animations']
            out.append(rec)
    return out


def parse_jumpshots():
    soup=fetch(URLS['jumpshots'])
    out=[]
    for table in soup.find_all('table'):
        rows=table.find_all('tr')
        if not rows: continue
        headers=[clean(c.get_text(' ', strip=True)) for c in rows[0].find_all(['th','td'])]
        if not headers or headers[0].lower() not in ('jump shot','jumpshot','player','guest jumpshot'): continue
        heading=heading_before(table)
        for tr in rows[1:]:
            cells=[clean(c.get_text(' ', strip=True)) for c in tr.find_all(['td','th'])]
            if len(cells)<2: continue
            rec={'name':cells[0]}
            try: rec['min_shooting']=int(cells[1])
            except: rec['min_shooting']=None
            if len(cells)>=3:
                rec['height']=cells[2]
            else:
                rec['height']=height_from_heading(heading) or 'all heights'
            rec['status']='verified_secondary'
            rec['source']='NBA2KW'
            rec['source_url']=URLS['jumpshots']
            out.append(rec)
    # dedupe exact records while preserving order
    seen=set(); ded=[]
    for r in out:
        k=(r['name'],r.get('min_shooting'),r.get('height'))
        if k not in seen:
            seen.add(k); ded.append(r)
    return ded


def parse_badges():
    soup=fetch(URLS['badges'])
    out=[]
    for table in soup.find_all('table'):
        rows=table.find_all('tr')
        if not rows: continue
        headers=[clean(c.get_text(' ',strip=True)) for c in rows[0].find_all(['th','td'])]
        if len(headers)<6 or headers[0].lower()!='badge': continue
        category=heading_before(table)
        category=re.sub(r'\s+Badge Requirements$','',category,flags=re.I).title() or 'Badge'
        for tr in rows[1:]:
            cells=[clean(c.get_text(' ',strip=True)) for c in tr.find_all(['td','th'])]
            if len(cells)<6: continue
            levels={headers[i]:cells[i] for i in range(2,min(7,len(cells)))}
            out.append({'name':cells[0],'category':category,'height':cells[1],'levels':levels,'status':'verified_secondary','source':'NBA2KW','source_url':URLS['badges']})
    seen=set(); ded=[]
    for r in out:
        k=r['name'].lower()
        if k not in seen: seen.add(k); ded.append(r)
    return ded


def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    animations=parse_animations(); jumps=parse_jumpshots(); badges=parse_badges()
    # Safety gates: never replace the cloud master with a partial scrape.
    if len(animations)<500: raise RuntimeError(f'Animation scrape too small: {len(animations)}')
    if len(jumps)<400: raise RuntimeError(f'Jumpshot scrape too small: {len(jumps)}')
    if len(badges)<30: raise RuntimeError(f'Badge scrape too small: {len(badges)}')
    write_json(DATA/'animations.json',animations)
    write_json(DATA/'jumpshots.json',jumps)
    write_json(DATA/'badges.json',badges)
    # Cloud master mirrors the app's manifest paths.
    write_json(DATA/'animations'/'master.json',animations)
    write_json(DATA/'jumpshots'/'master.json',jumps)
    write_json(DATA/'badges'/'master.json',badges)
    ts=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    files={}
    for rel in ['animations/master.json','jumpshots/master.json','badges/master.json','builds/master.json','builds/hidden_builds.json','cap_breakers/master.json','cap_breakers/sources.json','cap_breakers/specializations.json','cap_breakers/research.json','tips/master.json','sources/master_sources.json','sources/sources.json','sources/catalog_completeness.json','sources/feature_manifest.json']:
        p=DATA/rel
        if p.exists(): files[rel]={'sha256':sha(p)}
    manifest={
      'schema_version':2,'game':'NBA 2K26','database_version':'2.0.0',
      'last_updated':ts,'status':'AUTO-SOURCE-MASTER',
      'counts':{'animations.json':len(animations),'jumpshots.json':len(jumps),'badges.json':len(badges)},
      'files':files,
      'update_policy':{'add_new_records':True,'update_changed_records':True,'archive_missing_records':True,'never_delete_missing_immediately':True,'preserve_user_builds':True},
      'sources':[URLS['animations'],URLS['jumpshots'],URLS['badges'],'https://www.operationsports.com/all-nba-2k26-jump-shot-requirements/','https://newsroom.2k.com/news/nbar-2k26-myplayer-builder-delivers-all-new-animation-glossary-scouting-reports-and-build-by-badges-for-increased-customization'],
      'cloud_manifest_url':'https://raw.githubusercontent.com/mhmmdnrfdy11/nba2k26-companion-data/refs/heads/main/manifest.json',
      'database_mode':'cloud_master_cache','generated_by':'GitHub Actions source refresh','generated_at':ts
    }
    write_json(DATA/'manifest.json',manifest)
    print('REFRESH OK',len(animations),len(jumps),len(badges))

if __name__=='__main__': main()
