"""Record exact institutional precision corrections after independent reviews.

Idempotent source transformations; changes concern exposition, never estimates.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'paper/main_fr.tex';t=p.read_text(encoding='utf8')
def paragraph(start,replacement):
 global t
 at=t.find(start)
 if at<0:return
 end=t.find('\\footnote',at)
 if end<0:raise ValueError('Missing source footnote')
 t=t[:at]+replacement+t[end:]
paragraph('La cotisation foncière des entreprises (CFE)',
 'La cotisation foncière des entreprises (CFE) et la taxe foncière sur les propriétés bâties (TFPB) requièrent des délibérations locales distinctes, pour la part de chaque collectivité concernée. Pour un établissement créé par une entreprise bénéficiant de l’exonération de bénéfices, la CFE peut être exonérée pendant cinq années à compter de l’année suivant la création, puis sa base peut être réduite de 75, 50 et 25 \\% durant les trois années suivantes. La TFPB concerne un immeuble rattaché à un établissement remplissant les conditions de la CFE ; l’exonération suit les mêmes proportions et durée, à compter du 1er janvier suivant le rattachement. Les demandes et déclarations requises doivent aussi être effectuées. La fenêtre exceptionnelle de délibération de 2024 se termine le 18 septembre inclus pour permettre une application dès les impositions de 2025. Ce millésime correspond notamment aux créations et rattachements éligibles de 2024, sous réserve des autres conditions. Aucun inventaire national officiel complet des décisions effectivement adoptées n’a été vérifié pour cette étude ; le classement ne mesure donc pas le bénéfice effectif de ces exonérations locales.')
paragraph('Le régime d’exonération de cotisations patronales',
 'Le régime national exonère, pour les embauches éligibles, les cotisations patronales d’assurances sociales et d’allocations familiales pendant douze mois. La rédaction historique exclut une embauche portant l’effectif total de l’entreprise à au moins cinquante salariés ; l’exonération est pleine jusqu’à 1,5 SMIC, décroît ensuite et devient nulle à partir de 2,4 SMIC. L’employeur ne doit pas avoir procédé à un licenciement économique dans les douze mois précédents. Le contrat doit être un CDI ou un CDD admissible d’au moins douze mois ; la déclaration historique doit être transmise dans les trente jours. L’indicateur employeur de SIRENE ne permet pas de vérifier ces conditions ni de mesurer la réduction de cotisations effectivement obtenue.')
paragraph('La référence avant réforme inclut les communes classées',
 'La situation territoriale avant réforme repose sur l’arrêté du 16 mars 2017 modifié le 22 février 2018, ainsi que sur les dispositifs de maintien des effets pour les communes sorties du classement en 2017. L’article 73, XVI et XVII, de la loi de finances pour 2024 prolonge ces dispositifs de maintien jusqu’au 30 juin 2024. Le fichier officiel ANCT en COG 2021 convertit cette géographie et distingue les situations de classement et de maintien. La stabilité du code et du territoire est contrôlée ; les communes dont la correspondance n’est pas sûre sont exclues. L’arrêté ZRR du 19 juin 2024 entre en vigueur le 1er juillet et ne fournit pas une nouvelle liste à utiliser au 30 juin.')
paragraph('La loi de finances pour 2025 et l’arrêté du 14 avril',
 'La loi de finances pour 2025 ajoute des voies de classement et accorde les effets FRR aux communes auparavant classées en ZRR ou bénéficiant de ses effets, qui ne sont pas reclassées en FRR. Ce maintien, prévu à l’article 99, IV, s’applique rétroactivement au 1er juillet 2024 en vertu du VII-A ; les autres modifications doivent être suivies selon leurs propres clauses d’entrée en vigueur. L’arrêté du 14 avril 2025 publie les classements complémentaires et les communes bénéficiaires. Le décret de mise en œuvre et l’arrêté de classement FRR+ sont publiés le 10 juillet 2025, avec effet juridique au 1er janvier 2025. La loi de finances pour 2026 prolonge jusqu’en 2029 le terme des effets pour les communes bénéficiaires concernées, sans leur conférer le statut FRR+. Ces communes ne sont jamais utilisées comme témoins non bénéficiaires.')
t=t.replace('Les références géographiques et les données disponibles renvoient à l’année précédente.',
 'Pour le classement initial, la loi retient les données disponibles au 1er juillet 2023 et le périmètre des EPCI arrêté au 1er janvier 2023 ; ces dates ne signifient pas que toutes les variables économiques sont observées en 2023.')
t=t.replace('communes nouvellement bénéficiaires','communes nouvellement classées dans la liste initiale FRR')
t=t.replace('avantages locaux commençant en 2025','avantages locaux applicables aux créations ou rattachements de 2024 à partir des impositions de 2025')
t=t.replace('17\\,717 codes distincts, dont vingt communes','\\FRRInitialN{} codes distincts, dont \\FRRInitialPartialN{} communes')
t=t.replace('Elles fournissent 128 composantes.','Elles fournissent \\EPCIComponentsN{} composantes.')
t=t.replace('que 36 groupes','que \\EDBComponentsN{} groupes')
t=t.replace('128 composantes EPCI','\\EPCIComponentsN{} composantes EPCI')
t=t.replace('et log(1+immatriculations)',r'et la transformation $\log(1+y)$ des immatriculations')
p.write_text(t,encoding='utf8')
p=ROOT/'paper/appendix_fr.tex';t=p.read_text(encoding='utf8')
t=t.replace('17\\,717 codes','\\FRRInitialN{} codes').replace('36 composantes','\\EDBComponentsN{} composantes').replace('contient 191 paires','contient \\EDBMaxPairsN{} paires').replace('des 774 paires','des \\BorderPairs{} paires').replace('128 composantes EPCI','\\EPCIComponentsN{} composantes EPCI')
t=t.replace(r'\texttt{reports/UL\_historical\_HQ\_stage\_counts.csv}',r'\path{reports/UL_historical_HQ_stage_counts.csv}')
p.write_text(t,encoding='utf8')
print('Institutional and numerical wording corrections applied.')
