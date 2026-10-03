from pathlib import Path
import concurrent.futures,datetime,hashlib,json,os
os.environ['NIQUESTS_DISABLE_HTTP2']='1'
os.environ['NIQUESTS_DISABLE_HTTP3']='1'
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/raw/legal'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES={
 'faq_2024_july.pdf':'https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/FAQ%20FRR%20actualis%C3%A9e%2003072024-1.pdf',
 'faq_2024_september.pdf':'https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/1.%20politiques%20pub/FAQ%20FRR%20derni%C3%A8re%20maj130924%20.pdf',
 'frr_aelb.xlsx':'https://www.eau-loire-bretagne.fr/files/live/sites/aides-redevances/files/Aides-12prog/Outils%20de%20mise%20en%20oeuvre/FRR_communes_AELB.xlsx',
 'correze_frr_page.html':'https://www.correze.gouv.fr/Action-de-l-Etat/Emploi-economie-et-finances/Economie-et-soutien-aux-entreprises/Aides-aux-entreprises/France-Ruralite-Revitalisation',
 'frr_2024_new_path.xlsx':"https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/Liste%20classement%20FRR.xlsx",
 'frr_2024_legal.html':'https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820?query=ens&searchField=ALL&tab_selection=jorf',
 'frr_2024_law_article73.html':'https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000048727426?isSuggest=true',
}

def fetch(item):
 name,url=item
 try:
  r=requests.get(url,timeout=(15,40))
  data=r.content
  good=r.status_code==200 and (not name.endswith('.pdf') or data.startswith(b'%PDF')) and (not name.endswith('.xlsx') or data.startswith(b'PK'))
  if good:
   (OUT/name).write_bytes(data)
   if name.endswith('.html'):
    (OUT/(name+'.txt')).write_text(BeautifulSoup(data,'html.parser').get_text('\n',strip=True),encoding='utf8')
  row={'file':str(OUT/name),'url':url,'http_status':r.status_code,'valid_file_signature':good,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest() if good else None,'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 except Exception as e:
  row={'file':str(OUT/name),'url':url,'error':str(e),'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 print(json.dumps(row,ensure_ascii=False),flush=True)
 return row

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  rows=list(pool.map(fetch,SOURCES.items()))
 (OUT/'legal_download_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
