"""Save official evidence for the independent initial-2024 assignment audit only."""
from pathlib import Path
import requests, hashlib, json, datetime
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'data/raw/assignment2024'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = [
 ('an_avis_2024_486VIII.pdf', 'https://www.assemblee-nationale.fr/dyn/17/rapports/cion-dvp/l17b0486-tviii_rapport-avis.pdf'),
 ('an_avis_2024_486VIII.html', 'https://www.assemblee-nationale.fr/dyn/opendata/AVISANR5L17B0486-tVIII.html'),
 ('senat_debate_2023_11_26.pdf', 'https://www.senat.fr/cra/s20231126/s20231126.pdf'),
 ('insee_filosofi2020_geography2023.html', 'https://www.insee.fr/fr/statistiques/6692392?sommaire=6692394'),
 ('an_question2634_corsica_2025.html', 'https://questions.assemblee-nationale.fr/q17/17-2634QE.htm'),
 ('senat_question00328_2024.html', 'https://www.senat.fr/questions/base/2024/qSEQ241000328.html'),
 ('senat_question05373_2025.html', 'https://www.senat.fr/questions/base/2025/qSEQ250705373.html'),
 ('dgcl_faq_2024_09_13.pdf', 'https://www.collectivites-locales.gouv.fr/files/Coh%C3%A9sion%20territoriale/1.%20politiques%20pub/FAQ%20FRR%20derni%C3%A8re%20maj130924%20.pdf'),
 ('datagouv_frr_metadata.json', 'https://www.data.gouv.fr/api/1/datasets/communes-france-ruralite-revitalisation-frr/'),
]
records = []
for filename, url in SOURCES:
    record = dict(filename=filename, source_url=url, accessed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        response = requests.get(url, timeout=45)
        record.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get('content-type'), bytes=len(response.content))
        response.raise_for_status()
        if filename.endswith('.pdf') and not response.content.startswith(b'%PDF'):
            raise ValueError('Response is not a PDF')
        path = OUT / filename
        path.write_bytes(response.content)
        record.update(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(response.content).hexdigest(), saved=True)
        print(filename, response.status_code, len(response.content), record['sha256'])
        if filename == 'insee_filosofi2020_geography2023.html':
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [{'label': a.get_text(' ', strip=True), 'url': a.get('href')} for a in soup.find_all('a', href=True) if any(v in a.get('href','').lower() for v in ('.csv', '.xlsx', '.zip'))]
            (OUT / 'insee_filosofi2020_download_links.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
            print('INSEE_LINKS', json.dumps(links, ensure_ascii=False))
        if filename == 'datagouv_frr_metadata.json':
            meta=response.json()
            print('DATASET', meta.get('organization'), json.dumps([dict(title=x.get('title'),url=x.get('url'),format=x.get('format')) for x in meta.get('resources',[])],ensure_ascii=False))
    except Exception as exc:
        record.update(saved=False, error=str(exc))
        print(filename, 'FAILED', str(exc))
    records.append(record)
    (OUT / 'official_download_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
