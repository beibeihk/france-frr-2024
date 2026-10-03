from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
refs=pd.read_csv(ROOT/'references_verified.csv').fillna('')
entries=[]
for i,r in refs.iterrows():
 authors=' and '.join(x.strip() for x in r.authors.split(';'))
 title=r.title.replace('&',r'\&')
 journal=r.journal_or_series.replace('&',r'\&')
 typ='misc' if 'arXiv' in journal else 'article'
 fields={'author':authors,'title':'{'+title+'}','year':str(r.year),'journal' if typ=='article' else 'howpublished':journal,'doi':r.DOI,'url':r.URL}
 entry='@'+typ+'{ref'+str(i)+',\n'+',\n'.join('  '+k+' = {'+v+'}' for k,v in fields.items() if v)+'\n}'
 entries.append(entry)
(ROOT/'paper/references.bib').write_text('\n\n'.join(entries)+'\n',encoding='utf8')
print(str(len(refs))+' verified references converted to BibTeX.')
