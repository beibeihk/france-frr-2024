"""One entry point; data/analysis, paper build and scientific gate are separate.

--rebuild recomputes outputs from frozen official raw sources. --download obtains
and hashes the exact vintage first. Default checks syntax and the saved gate.
No mode creates accounts, publishes GitHub or submits to HAL.
"""
from pathlib import Path
import argparse,subprocess,sys,json,ast
ROOT=Path(__file__).resolve().parent
def run(path):
 print('RUN '+path,flush=True)
 subprocess.run([sys.executable,str(ROOT/path)],cwd=ROOT,check=True)
def main():
 a=argparse.ArgumentParser();a.add_argument('--download',action='store_true');a.add_argument('--rebuild',action='store_true');a.add_argument('--figures',action='store_true');a.add_argument('--compile',action='store_true');args=a.parse_args()
 for folder in ['data/raw','data/intermediate','data/external','data/processed','logs','reports','tables','results/tables','results/figures','paper/generated','tmp']:
  (ROOT/folder).mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'src').rglob('*.py'):ast.parse(p.read_text(encoding='utf8'))
 if args.download:run('src/download/frozen_download.py')
 if args.rebuild:
  for path in ['src/legal/extract_verified_frr_codes.py','src/construct/prepare_communes.py','src/geography/border_pairs.py',
   'src/legal/audit_final_treatment_and_borders.py','src/legal/institutional_facts_for_macros.py','src/construct/construct_panel.py','src/construct/secondary_outcomes.py','src/construct/birth_structure.py','src/construct/audit_observations.py',
   'src/construct/assignment_sources.py','src/construct/assignment2024.py','src/construct/audit_assignment_paths.py',
   'src/analysis/estimate.py','src/analysis/broad_and_matched.py','src/analysis/ppml.py','src/analysis/diagnostics.py','src/analysis/secondary_analysis.py',
   'src/analysis/assignment_extended_support.py','src/analysis/bassin_rd.py']:
   run(path)
 if args.figures or args.rebuild:
  run('src/figures/build_artifacts.py');run('src/figures/build_assignment_artifacts.py')
 if args.compile:run('src/tables/build_bibliography.py');run('src/tables/compile_paper.py')
 status=json.loads((ROOT/'reports/analysis_status.json').read_text())
 print('SCIENTIFIC GATE: '+status['status'],flush=True)
 print('Causal designs remain closed. This pipeline rebuilds the noncausal research; it never publishes or submits deposits.',flush=True)
if __name__=='__main__':main()
