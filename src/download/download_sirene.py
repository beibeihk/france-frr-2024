"""Download only the INSEE official release, streaming to disk; no identifying output."""
from pathlib import Path
import concurrent.futures, hashlib, json, time, sys
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw'
EXT = ROOT / 'data/external'
API = 'https://www.data.gouv.fr/api/1/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/'

def download(r):
    suffix = '.parquet' if r['format'] == 'parquet' else Path(r['url']).suffix
    name = r['url'].split('/')[-1]
    folder = RAW if suffix == '.parquet' else EXT / 'sirene_dictionary'
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / name
    expected = r.get('filesize')
    part = dest.with_suffix(dest.suffix + '.part')
    if not (dest.exists() and (not expected or dest.stat().st_size == expected)):
        for attempt in range(5):
            try:
                offset = part.stat().st_size if part.exists() else 0
                h = {'Range': f'bytes={offset}-'} if offset else {}
                resp = requests.get(r['url'], headers=h, stream=True, timeout=(30,180))
                resp.raise_for_status()
                mode = 'ab' if offset and resp.status_code == 206 else 'wb'
                if mode == 'wb': offset = 0
                print(f'DOWNLOAD {name} resume={offset}', flush=True)
                with part.open(mode) as f:
                    for block in resp.iter_content(4*1024*1024):
                        if block: f.write(block)
                if expected and part.stat().st_size != expected:
                    raise ValueError(f'Incomplete file {name}: {part.stat().st_size} != {expected}')
                part.replace(dest)
                break
            except Exception as exc:
                print(f'RETRY {name} {type(exc).__name__}', flush=True)
                if attempt == 4: raise
                time.sleep(min(2**attempt, 16))
    hasher = hashlib.sha256()
    with dest.open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''): hasher.update(block)
    result = {'resource_id':r['id'], 'title':r['title'], 'url':r['url'],
              'stable_url':f"https://www.data.gouv.fr/api/1/datasets/r/{r['id']}",
              'size_bytes':dest.stat().st_size, 'sha256':hasher.hexdigest(),
              'downloaded_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              'last_modified':r.get('last_modified'), 'relative_path':str(dest.relative_to(ROOT)),
              'license':'Licence Ouverte / Open Licence 2.0', 'publisher':'INSEE'}
    manifest = EXT / 'download_manifest'
    manifest.mkdir(exist_ok=True)
    (manifest / (r['id']+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'VERIFIED {name} bytes={result["size_bytes"]}', flush=True)
    return result

def main():
    RAW.mkdir(parents=True,exist_ok=True)
    if (EXT/'sirene_metadata.json').exists():
        j=json.loads((EXT/'sirene_metadata.json').read_text(encoding='utf8'))
    else:
        j=requests.get(API,timeout=60).json()
        (EXT/'sirene_metadata.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
    resources=[r for r in j['resources'] if r['format']=='parquet' or r.get('type')=='documentation']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        result=list(pool.map(download,resources))
    (EXT/'sirene_download_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__': main()
