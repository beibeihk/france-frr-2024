"""Read-only PDF checks and page rendering; does not modify source PDFs."""
from pathlib import Path
import json,hashlib,shutil,subprocess
import fitz
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'tmp/pdfs';OUT.mkdir(parents=True,exist_ok=True)
def main():
 results={}
 for name in ['main_fr','appendix_fr']:
  path=ROOT/'paper'/(name+'.pdf');doc=fitz.open(path);counts=[];outside=[];fontrefs={};urls=[];tiles=[]
  for i,page in enumerate(doc):
   text=page.get_text();counts.append(len(text))
   for b in page.get_text('blocks'):
    if b[4].strip() and (b[0]<0 or b[1]<0 or b[2]>page.rect.width+.5 or b[3]>page.rect.height+.5):outside.append(i+1)
   for f in page.get_fonts(full=True):fontrefs[f[0]]=f[3]
   urls.extend(l.get('uri','') for l in page.get_links() if l.get('uri'))
  embedded={font:bool(doc.extract_font(ref)[3]) for ref,font in fontrefs.items()}
  # Prefer Poppler as prescribed for visual fidelity.
  poppler=shutil.which('pdftoppm')
  if poppler:
   p=subprocess.run([poppler,'-r','110','-png',str(path),str(OUT/name)],capture_output=True)
   if p.returncode:raise RuntimeError('Poppler render failed')
   pages=sorted((p for p in OUT.glob(name+'-*.png') if 1<=int(p.stem.rsplit('-',1)[1])<=len(doc)),key=lambda x:int(x.stem.rsplit('-',1)[1]))
  else:
   pages=[]
   for i,page in enumerate(doc):
    dest=OUT/f'{name}-{i+1}.png';page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(dest);pages.append(dest)
  if len(pages)!=len(doc):raise RuntimeError('Rendered page count differs from PDF')
  width=310;height=460;cols=4;sheet=Image.new('RGB',(cols*width,((len(pages)+cols-1)//cols)*height),'#d8d8d8');draw=ImageDraw.Draw(sheet)
  for n,page in enumerate(pages):
   img=Image.open(page).convert('RGB');img.thumbnail((width-14,height-26))
   x=(n%cols)*width+7;y=(n//cols)*height+20;sheet.paste(img,(x,y));draw.text((x,y-15),f'{name} — {n+1}',fill='black')
  sheet.save(OUT/(name+'_contact.png'))
  results[name]={'pages':len(doc),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'text_chars_per_page':counts,
   'searchable_all_pages':all(x>100 for x in counts),'replacement_glyphs':sum(page.get_text().count('\ufffd') for page in doc),
   'outside_page_text':outside,'fonts_embedded':embedded,'all_fonts_embedded':all(embedded.values()),'external_link_count':len(urls),
   'link_backslash_errors':sum('\\' in x for x in urls),'rendered_pages':len(pages),'visual_review':'pending manual agent inspection of contact and selected full pages'}
  doc.close()
 (ROOT/'reports/pdf_quality.json').write_text(json.dumps(results,indent=2),encoding='utf8')
 print(json.dumps({name:{k:v for k,v in result.items() if k not in ['fonts_embedded','text_chars_per_page']} for name,result in results.items()}),flush=True)
if __name__=='__main__':main()
