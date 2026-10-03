from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.vendor'))
import duckdb
c=duckdb.connect()
E=str(ROOT/'data/raw/stock-stocketablissement-parquet.parquet').replace('\\','/')
H=str(ROOT/'data/raw/stock-stocketablissementhistorique-parquet.parquet').replace('\\','/')
q=f"""EXPLAIN SELECT e.siret,h.caractereEmployeurEtablissement FROM read_parquet('{E}') e LEFT JOIN read_parquet('{H}') h
ON e.siret=h.siret AND TRY_CAST(h.dateDebut AS DATE)<=TRY_CAST(e.dateCreationEtablissement AS DATE)
AND coalesce(TRY_CAST(h.dateFin AS DATE),DATE '9999-12-31')>=TRY_CAST(e.dateCreationEtablissement AS DATE)
WHERE TRY_CAST(e.dateCreationEtablissement AS DATE) BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'"""
plan=c.sql(q).fetchall()[0][1]
(ROOT/'reports/birth_join_query_plan.txt').write_text(plan,encoding='utf8')
print(plan)
