"""Recreate the exact release from data_sources.csv, never silently use a newer stock."""
from pathlib import Path
import concurrent.futures,hashlib,zipfile
import pandas as pd,requests
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def fetch(r):
 path=ROOT/r.path;path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():
  temp=path.with_suffix(path.suffix+'.part')
  offset=temp.stat().st_size if temp.exists() else 0
  response=requests.get(r.source_url,headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(30,180))
  response.raise_for_status()
  with temp.open('ab' if offset and response.status_code==206 else 'wb') as f:
   for block in response.iter_content(4*1024*1024):
    if block:f.write(block)
  if temp.stat().st_size!=int(r.size_bytes):raise RuntimeError('Size mismatch: '+r.path)
  temp.replace(path)
 if sha(path)!=r.sha256:raise RuntimeError('Historical source changed; refuse to substitute: '+r.path)
 if path.name in ['epci_2023.zip','epci_2024.zip']:
  year=path.stem[-4:]
  with zipfile.ZipFile(path) as z:
   dest=ROOT/'data/raw'/('epci_'+year);dest.mkdir(exist_ok=True)
   for name in z.namelist():
    if Path(name).suffix.lower()=='.xlsx':(dest/Path(name).name).write_bytes(z.read(name))
 print('Source hash verified: '+r.path,flush=True)
def main():
 s=pd.read_csv(ROOT/'data_sources.csv',dtype=str).fillna('')
 rows=list(s[s.required_rebuild.eq('true')&s.retrieval.eq('http_binary')].itertuples())
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(fetch,rows))
if __name__=='__main__':main()
