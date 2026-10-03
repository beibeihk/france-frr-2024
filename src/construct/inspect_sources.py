from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.vendor'))
import duckdb,pandas as pd,fitz

def main():
 c=duckdb.connect()
 p=ROOT/'data/raw'
 q=str(p/'stock-stocketablissement-parquet.parquet').replace('\\','/')
 print(c.sql(f"SELECT statutDiffusionEtablissement, count(*) AS n, count(codeCommuneEtablissement) AS geo FROM read_parquet('{q}') GROUP BY 1").fetchall())
 for name in ['movements_cog2026.csv','communes_cog2026.csv']:
  d=pd.read_csv(p/name,dtype=str)
  print(name,d.columns.tolist(),d.head(2).to_dict('records'))
 d=pd.read_excel(p/'zrr_2021.xls',sheet_name=0,header=5,dtype=str)
 print('ZRR columns',d.columns.tolist())
 print('ZRR labels',d.iloc[:,3].value_counts().to_dict())
 for f in (ROOT/'data/external/sirene_dictionary').glob('*.pdf'):
  print(f.name,[l.get('uri') for pg in fitz.open(f) for l in pg.get_links() if l.get('uri')])

if __name__=='__main__':main()
