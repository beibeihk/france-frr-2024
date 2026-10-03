from pathlib import Path
from urllib.parse import urljoin
import hashlib,json,datetime,concurrent.futures
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
SOURCES={
 'frr_2024.xlsx':'https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/2.%20dispositifs/France%20ruralit%C3%A9s/Liste%20classement%20FRR.xlsx',
 'frr_2025.xlsx':"https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/Liste%20communes%20FRR_juillet2025.xlsx",
 'faq_2024.pdf':'https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/1.%20politiques%20pub/FAQ%20FRR%20derni%C3%A8re%20maj130924%20.pdf',
 'faq_2025.pdf':"https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/FAQ%20FRR_MAJ%20juillet2025.pdf",
 'zrr_2021.xls':'https://static.data.gouv.fr/resources/zones-de-revitalisation-rurale-zrr/20210907-124104/diffusion-zonages-zrr-cog2021.xls',
 'zrr_2024_legal.html':'https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034298773/2024-06-30/',
 'frr_original_legal.html':'https://www.legifrance.gouv.fr/eli/arrete/2024/6/19/TREB2414964A/jo/texte',
 'frr_extension_2025.html':'https://www.legifrance.gouv.fr/eli/arrete/2025/4/14/ATDB2508688A/jo/texte',
 'service_public_frr.html':'https://entreprendre.service-public.gouv.fr/vosdroits/F31139',
 'frr_2026_bofip.html':'https://bofip.impots.gouv.fr/bofip/14772-PGP.html/identifiant=BOI-BIC-CHAMP-80-10-75-20-20260729',
 'communes_cog2026.csv':'https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_2026.csv',
 'movements_cog2026.csv':'https://www.insee.fr/fr/statistiques/fichier/8740222/v_mvt_commune_2026.csv',
 'communes_history_cog2026.csv':'https://www.insee.fr/fr/statistiques/fichier/8740222/v_commune_depuis_1943.csv',
 'communes_2024_5m.geojson.gz':'https://object.data.gouv.fr/contours-administratifs/2024/geojson/communes-5m.geojson.gz',
 'epci_2024.zip':'https://www.insee.fr/fr/statistiques/fichier/2510634/epci_au_01-01-2024.zip',
 'epci_2023.zip':'https://www.insee.fr/fr/statistiques/fichier/2510634/Intercommunalite_Metropole_au_01-01-2023.zip',
 'population_2021.xlsx':'https://www.insee.fr/fr/statistiques/fichier/7739582/ensemble.xlsx',
}

def fetch(item):
 name,url=item
 dest=ROOT/'data/raw'/name
 if dest.exists(): data=dest.read_bytes();status=200
 else:
  r=requests.get(url,timeout=(30,120));status=r.status_code;data=r.content
  if status==200: dest.write_bytes(data)
 row={'file':name,'url':url,'status_code':status,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest() if status==200 else '', 'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 if status==200 and name.endswith('.html'):
  text=BeautifulSoup(data,'html.parser').get_text('\n',strip=True)
  (ROOT/'data/external'/(name+'.txt')).write_text(text,encoding='utf8')
 print(name,status,len(data),flush=True)
 return row

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(fetch,SOURCES.items()))
 (ROOT/'data/external/zoning_manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
