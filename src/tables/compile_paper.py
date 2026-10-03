"""Compile this multi-file research project using the existing TeX installation."""
from pathlib import Path
import subprocess,shutil,json
ROOT=Path(__file__).resolve().parents[2];PAPER=ROOT/'paper'
def executable(name):
 path=shutil.which(name)
 if path:return path
 win=Path('C:/texlive/2022/bin/win32')/(name+'.exe')
 if win.exists():return str(win)
 raise RuntimeError('Missing existing TeX executable: '+name)
def run(args,label):
 p=subprocess.run(args,cwd=PAPER,capture_output=True)
 (ROOT/'logs').mkdir(exist_ok=True)
 (ROOT/'logs'/(label+'.txt')).write_bytes(p.stdout+p.stderr)
 if p.returncode:
  print((p.stdout+p.stderr).decode('utf8',errors='replace')[-3000:])
  raise RuntimeError('Compilation failed: '+label)
def main():
 xe=executable('xelatex');bib=executable('bibtex');args=['-interaction=nonstopmode','-halt-on-error']
 run([xe,*args,'main_fr.tex'],'main_pass1')
 run([bib,'main_fr'],'bibliography')
 for n in [2,3]:run([xe,*args,'main_fr.tex'],f'main_pass{n}')
 for n in [1,2]:run([xe,*args,'appendix_fr.tex'],f'appendix_pass{n}')
 checks={}
 for name in ['main_fr','appendix_fr']:
  log=(PAPER/(name+'.log')).read_text(encoding='utf8',errors='replace')
  checks[name]={'compiled':True,'overfull_boxes':log.count('Overfull'),'undefined_citations':log.count('undefined'),
   'pdf_bytes':(PAPER/(name+'.pdf')).stat().st_size}
 (ROOT/'reports/compilation.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
