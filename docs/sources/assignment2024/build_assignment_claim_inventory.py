"""New institutional/assignment claims, separate from root claims and new research Y."""
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[3]
LAW='https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049130324/2024-07-01/'
ARRETE='https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820'
SENAT='https://www.senat.fr/cra/s20231126/s20231126.pdf'
INCOME='https://www.insee.fr/fr/statistiques/6692392?sommaire=6692394'
POP='https://www.insee.fr/fr/statistiques/7632565'
THRESHOLDS='https://www.assemblee-nationale.fr/dyn/17/rapports/cion-dvp/l17b0486-tviii_rapport-avis.pdf'
EPCI='https://www.insee.fr/fr/statistiques/fichier/2510634/Intercommunalite_Metropole_au_01-01-2023.zip'
BV='https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip'
MOUNTAIN='https://www.data.gouv.fr/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022'
MOV='https://www.insee.fr/fr/statistiques/fichier/8740222/v_mvt_commune_2026.csv'
NEVERS='https://www.senat.fr/questions/base/2025/qSEQ250102997.html'
rows=[]

def add(claim,location,url,kind,notes):
    rows.append(dict(claim=claim,paper_location=location,source_url=url,source_type=kind,verified='true',notes=f'A2-{len(rows)+1:02d}; independent REVIEW A 2026-10-04; '+notes))

L1='main §3.2 paragraph 1 [paper/main_fr.tex:41]'
L2='main §3.2 paragraph 2 and table thresholds [paper/main_fr.tex:43]'
L3='main §3.2 paragraph 3 [paper/main_fr.tex:47]'
L4='main §3.2 paragraph 4 [paper/main_fr.tex:49]'
L5='abstract; main §3.2 paragraph 5 and table paths [paper/main_fr.tex:53]'
LP='main §5.3 and table assignment support [paper/main_fr.tex:131]'
DERIVED='independent_reconstruction_from_official_sources'
LEGAL='official_historical_law'
NUM='official_contemporaneous_parliamentary_report_and_independent_reproduction'

add('Le ministre confirme le recensement 2020 et Filosofi 2020 pour la réforme initiale.',L1,SENAT,'official_contemporaneous_parliamentary_record','PDF page66, printed63; intervention Dominique Faure, 26 November 2023. Observation year, not mere July2023 availability.')
add('Filosofi 2020 est publié le 24 avril 2023 dans la géographie au 1er janvier 2023.',L1,INCOME,'official_statistical_documentation','Published source page and MED20 archive; available before2023-07-01. Source SHA44229f0a9ce3dcd95014e6cfadb79beae85597944862664c41493ca3be65a8fd.')
add('La série historique de population 2020 est diffusée le 27 juin 2023 en COG2023.',L1,POP,'official_statistical_documentation','P20_POP/SUPERF canonical table, before legal availability cutoff; source SHA89bff69833bb186a3e91ba11d338dad96f5d367275fad0bf5cd82fdb0acc7e32.')
add('La densité légale est fondée sur la population municipale.',L1,LAW,LEGAL,'IV; geographical density computed as sum population/sum area, not unweighted mean of commune densities.')
add('MED20 est la médiane du revenu disponible du ménage par unité de consommation.',L1,INCOME,'official_statistical_documentation','Use direct native COM/EPCI/BV2022/DEP medians. Definition corroboration https://www.insee.fr/fr/metadonnees/definition/c1890; no mean or aggregation of commune medians.')
add('Le plafond communal de 30 000 habitants est appliqué à la population municipale de 2020.','main §3.1 population limit; main §3.2 paragraph1, explicit source precision recommended',NEVERS,'official_retrospective_government_answer','10 April2025 government response states initial municipal2020 ceiling; not latest population substituted. Historical law requires population strictly<30000.')
add('Le classement initial utilise les données disponibles au 1er juillet 2023 et le périmètre EPCI au 1er janvier 2023.','main §3.1 paragraph2 [paper/main_fr.tex:38]',LAW,LEGAL,'IV; observation year remains2020. General date fact may overlap existing root institutional inventory; do not duplicate blindly.')
add('La distribution de référence comprend 1 232 EPCI métropolitains réels.',L2,EPCI,DERIVED,'Independent composition/income count; exclude island sentinel ZZZZZZZZZ. Table units are reference universe, not eligible units.')
add('La distribution de référence comprend 1 681 bassins de vie métropolitains.',L2,BV,DERIVED,'BV2022 definition on COG2023, native income and reconstructed census density; table units are reference universe, not approved basin count.')
add('Le seuil départemental publié de revenu est reproduit sur 96 départements métropolitains.',L2,THRESHOLDS,DERIVED,'96 metropolitan native MED20 values median21665; all98 published department incomes median21620. Original C median clause does not expressly repeat metropolitan denominator.')
add('Le seuil de densité EPCI affiché est 63,57 habitants par km².',L2,THRESHOLDS,NUM,'25 October2024 reportp18. Exact public-input reconstruction63.569845464551264; tests use full precision. No claim government published these extra decimals.')
add('Le seuil de revenu EPCI de droit commun est 21 570 euros.',L2,THRESHOLDS,NUM,'Contemporary reportp18; unweighted median of1232 direct EPCI MED20 values independently reproduced.')
add('Le troisième quartile de revenu EPCI pour la voie montagne est 22 822,5 euros.',L2,THRESHOLDS,NUM,'Reportp18; pandas linear Q75 reproduces this value. Administrative software quantile convention and unrounded microdata not recovered.')
add('Le seuil de densité bassin affiché est 70,84 habitants par km².',L2,THRESHOLDS,NUM,'Reportp18. Full-precision public reconstruction70.84363836218742; no claim government published these extra decimals.')
add('Le seuil de revenu bassin est 21 600 euros.',L2,THRESHOLDS,NUM,'Reportp18; median of1681 native BV2022 MED20 values independently reproduced. Numeric condition alone is not observed proposal/approval.')
add('Le seuil départemental de revenu publié est 21 665 euros.',L2,THRESHOLDS,NUM,'Reportp18; independent direct department MED20 verification; not own-department median as comparison threshold.')
add('La voie C exige une densité strictement inférieure à 35 et le critère de revenu conjoint.',L2,LAW,LEGAL,'II-C AND; <35, not<=35. Replacement recommends median of departmental medians to remove ambiguity in current phrasing.')
add('Treize départements satisfont les deux conditions de la voie C.',L2,THRESHOLDS,DERIVED,'Codes04/05/09/12/15/23/32/36/46/48/52/55/58; direct public2020/COG2023 inputs. Numerically derived, not number stated by original law.')
add('La voie A requiert conjointement les conditions de densité et de revenu EPCI.',L2,LAW,LEGAL,'II-A; inclusive national metropolitan medians and commune population<30000. No additional original INSEE rural-grid requirement.')
add('La voie D exige au moins 50 % de population dans la zone montagne légale et les critères conjoints de densité et de revenu.',L2,LAW,LEGAL,'II-D; legalLoiMontagne1985art3 population share, not share of communes/area/massif. D is mandatory when true; public D flag is only possible.')
add('La voie B requiert les critères numériques et une procédure complémentaire préfet/ministres.',L2,LAW,LEGAL,'II-B; general-interest regional-prefect proposal and joint ministerial classification. Current replacement makes final arrete explicit. National actual proposal archive not recovered.')
add('Le plafond de population se vérifie commune par commune, pas sur la population totale du bassin.',L2,LAW,LEGAL,'II-B communes<30000; a large-city basin member does not automatically invalidate other target communes.')
add('Les quatre communes insulaires sans EPCI visées au CGCT utilisent leurs propres indicateurs dans A.',L3,LAW,LEGAL,'II-A finalparagraph and L5210-1-1V; codes22016/29083/29155/85113. Sans objet is not sharedEPCI. Only29155 meetsA in observed inputs; code counts not asserted in current text.')
add('Un revenu communal inconnu reste inconnu; une condition nécessaire fausse permet néanmoins de rejeter A.',L3,LAW,DERIVED,'Three-valued AND, independent checks. 29083 incomeNaN preserved; density443.3333>63.569845 rejects A. No imputation and no claim confidential income recovered.')
add('Le fichier montagne utilisé est une archive COG2022 ; il ne mesure pas la population située en zone montagne en 2023.',L4,MOUNTAIN,'official_statistical_documentation','Required manuscriptprecision: resource23March2022. 5611 presence rows/233 merger records are source-audit-only, not current manuscript claims; exact2023 share unavailable.')
add('Les parties classées de commune ne disposent pas de population propre dans ce fichier montagne.',L4,MOUNTAIN,'official_statistical_documentation','Official metadata explicitly preserves formerly classified parts after fusion; workbook lacks population-in-classified-part column. Presence is not actual50percent condition.')
add('La population entière des membres concernés ou inconnus constitue seulement un majorant conditionnel.',L4,MOUNTAIN,DERIVED,'Upper bound relies on legal-list coverage and cross-vintage mapping. COG movements check same-code survivors; not exhaustive verification of legal-zone changes absent from COG. PositiveDpotential is not verifiedDassignment.')
add('Les contrôles de 2022 à 2023 ne trouvent aucun code survivant absorbant un membre montagne tout en échappant aux deux drapeaux.','source audit only; recommended main§3.2 mountain precision',MOV,DERIVED,'79 movement records between dates; zero unflagged survivors. C separately counts10 perimeter/code targets. Objects differ; neither identifies intracommunal population.')
add('Le domaine légal COG2023 contient 34 816 communes métropolitaines.',L3,BV,DERIVED,'Official historical composition and censusCOM, whole cities, not PLM arrondissements. Separate from later stable empirical sample.')
add('17 672 communes métropolitaines figurent dans la liste initiale.',L3,ARRETE,DERIVED,'Official original annex; nationwide17717 minus45 overseas. Derived count independently verified; not2025current list substituted.')
add('14 316 communes classées satisfont une voie obligatoire A ou C vérifiée.',L5,ARRETE,DERIVED,'Union M=A_epci OR A_isolated OR C, not sum of overlapping route counts; direct official2020 inputs and original list. D is not declared discretionary; exactshare not observed.')
add('3 356 communes classées restantes satisfont uniquement une voie B ou D possible.',L5,ARRETE,DERIVED,'Residual outside M. Candidate union under recorded inputs, no actual administrative path flag. Current table matches independent audit.')
add("3 013 communes classées hors M n'ont que B comme voie restante conditionnellement à la reconstruction.",L5,ARRETE,DERIVED,'~M AND Bpotential AND ~Dpotential AND listed. B logical necessity is conditional on conservative mountaincoverage, not national proposal archive or externalassignment proof.')
add("304 communes classées hors M n'ont que D possible au regard du majorant.",L5,ARRETE,DERIVED,'~M AND ~Bpotential AND Dpotential AND listed; upperbound>=.5 is possibleD, not observed actualD eligibility.')
add('39 communes classées hors M satisfont conjointement B possible et D possible.',L5,ARRETE,DERIVED,'Overlap among residual candidates; actual administrative path cannot be separated.')
add('Les 3 013 communes B-only couvrent 314 bassins distincts.',L5,ARRETE,DERIVED,'Current macro314 verified; initial wrong340 display repaired by explicitstr administrativecode andlow_memoryFalse. 314 is subsetcoverage, not observed prefect proposal/approval count.')
add('17 144 communes ne sont pas classées et ne satisfont aucune voie possible reconstruite.',L5,ARRETE,DERIVED,'Includes known necessary failure for29083 despite incomeNaN. Conditional reconstructed union; not official per-commune administrative reasons.')
add("Aucune commune satisfaisant M n'est omise et aucun non-classé ne satisfait l'union possible reconstruite.",L5,ARRETE,DERIVED,'Zero observed discrepancy in34816metroCOM; independent matrix. Finite observed-set equality is not exogeneity or complete policy-path recovery.')
add('Les domaines EPCI propres ont 0, 6 et au plus 1 EPCI du côté éligible dans les fenêtres indiquées.',LP,LAW,DERIVED,'reports/rd_assignment_only_support.csv independently verified. A-income wholebarrier0; B-income communebarrier6; D-density communebarriermax1; refers oldEPCI candidates, not actualBV/Vdesign.')
add('Le domaine V à h = 1000 contient 119 bassins éligibles et 79 non éligibles.','main §5.4 paragraph1 [paper/main_fr.tex:138]; protocol§11',BV,DERIVED,'REVIEW B assignment-only interface; current119/79 manuscript macros verified without inspecting V estimate.67/56distinct scores,1tie, selectedinitialdesignation conflicts0. Minimumsupport passes only operational screen, not causalcontinuity or spatialinference gate.')
add('V exclut les quatre communes sans EPCI de son domaine sélectionné.','protocol§11/source audit only; not yet asserted in reviewed manuscript',EPCI,DERIVED,'Actual assignment-only selectedcommune interface has none of22016/29083/29155/85113; fullBV dependence graph gives noEPCIcommunes separateCOMMUNEprimitives.')
add("Le filtre stable utilise également les mouvements après juillet 2024 jusqu'au COG2026.",'main §5.4 paragraph2 [paper/main_fr.tex:140]; Vprotocol§§10-11',MOV,DERIVED,'Current V methods disclose postpolicy stability selection. prepare_communes.py analysis_stable excludes non-name movements since2017 fromCOG2026history. Frozen before newestimation does not mean exclusivelyprepolicy attributes; coverage aroundcutoff requiresdiagnosis.')

out=ROOT/'reports/assignment_claims_audit.csv'
with out.open('w',encoding='utf8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['claim','paper_location','source_url','source_type','verified','notes'])
    writer.writeheader();writer.writerows(rows)
print(f'Wrote {len(rows)} separate assignment claims: {out}')
