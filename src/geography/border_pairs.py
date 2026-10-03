from pathlib import Path
import json
import numpy as np,pandas as pd,geopandas as gpd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
ROOT=Path(__file__).resolve().parents[2]

def main():
 g=gpd.read_parquet(ROOT/'data/processed/commune_geography.parquet')
 stable=g[g.analysis_stable].copy()
 t=stable[stable.treatment_group.eq('NEW_FRR')].sort_values('commune_code').reset_index(drop=True)
 c=stable[stable.treatment_group.eq('NEVER_TREATED')&stable.population_2021.lt(30000)].sort_values('commune_code').reset_index(drop=True)
 print('CANDIDATES',len(t),len(c),flush=True)
 # Return only real intersecting official polygons; remove point contacts.
 r,cc=c.sindex.query(t.geometry,predicate='intersects')
 edges=[]
 for i,j in zip(r,cc):
  length=t.geometry.iloc[i].boundary.intersection(c.geometry.iloc[j].boundary).length
  if length>50:
   edges.append({'treated_code':t.commune_code.iloc[i],'control_code':c.commune_code.iloc[j],
   'treated_epci':t.epci_2023.iloc[i],'control_epci':c.epci_2023.iloc[j],
   'treated_department':t.department.iloc[i],'control_department':c.department.iloc[j],
   'shared_boundary_m':float(length),'treated_population':float(t.population_2021.iloc[i]),
   'control_population':float(c.population_2021.iloc[j]),'treated_density':float(t.density_2021.iloc[i]),
   'control_density':float(c.density_2021.iloc[j]),'i':int(i),'j':int(j)})
 e=pd.DataFrame(edges).sort_values(['treated_code','control_code']).reset_index(drop=True)
 e.to_csv(ROOT/'data/processed/border_edges.csv',index=False)
 graph=csr_matrix((np.ones(len(e)),(e.i,e.j)),shape=(len(t),len(c)))
 match=maximum_bipartite_matching(graph,perm_type='column')
 selected={(i,int(j)) for i,j in enumerate(match) if j>=0}
 pairs=e[[tuple(x) in selected for x in e[['i','j']].to_numpy()]].copy().reset_index(drop=True)
 pairs['pair_id']=np.arange(len(pairs))
 assert pairs.treated_code.is_unique and pairs.control_code.is_unique
 pairs.to_csv(ROOT/'data/processed/border_pairs.csv',index=False)
 report={'new_frr_stable':len(t),'eligible_never_controls':len(c),'edges':len(e),'disjoint_pairs':len(pairs),
 'treated_border_candidates':e.treated_code.nunique(),'control_border_candidates':e.control_code.nunique(),
 'treated_epci_clusters':pairs.treated_epci.nunique(),'control_epci_clusters':pairs.control_epci.nunique(),
 'same_epci_pairs':int(pairs.treated_epci.eq(pairs.control_epci).sum()),
 'epci_in_both_roles':len(set(pairs.treated_epci)&set(pairs.control_epci)),
 'same_department_pairs':int(pairs.treated_department.eq(pairs.control_department).sum()),
 'matching':'scipy maximum_bipartite_matching; sorted INSEE codes; no outcomes used',
 'topology':'IGN-derived data.gouv 2024 5m contours; exact shared boundary >50m; EPSG:2154'}
 (ROOT/'reports/border_sample_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps(report),flush=True)

if __name__=='__main__':main()
