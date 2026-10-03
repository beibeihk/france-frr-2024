# REVIEW D — Examen final de langue française (IA)

**Avis dans le périmètre examiné : PASS_AI_FRENCH_ACADEMIC_LANGUAGE_WITHIN_RECORDED_SOURCE_SCOPE.** La rédaction relève d’un français académique naturel et suffisamment précis pour ce document de travail. Cet avis concerne la langue des sources examinées ; il ne certifie ni une identification causale, ni une validation scientifique globale, ni une lecture personnelle de l’auteur, ni un dépôt HAL.

L’examen a été réalisé par un agent d’IA distinct. Il ne constitue ni une relecture par une personne de langue maternelle française ni une expertise par des pairs humains. Il n’impose pas par lui-même un recours supplémentaire à un éditeur humain.

## Périmètre réellement lu et édité

Les deux sources ont été lues intégralement : front matter, corps, notes, formules, intitulés et notes des tableaux/figures, clôture et déclaration IA. La nouvelle analyse des bassins de vie et la reconstitution des voies initiales sont incluses. Les sept nouvelles tables générées d’assignation et de bassin ont été lues intégralement dans leur version ci-dessous. Elles n’ont pas été éditées par cet agent. La compilation et la vérification des PDF restent à réaliser par le responsable.

- `paper/main_fr.tex` : avant `d641bace0fccf1ad53e8a2ef1fc10e5a29c3510005de87c0fb609a5944320837` ; final `a91f093537f3862a070a24f746b0ed2f6dec680aee05f99734680208f0828f12` ; 66041 octets.
- `paper/appendix_fr.tex` : avant `6340768c39779a7946b7904ef3a75b981cba908c08d5fec6851170b65282d59c` ; final `b10a2263fda8ba506605603fa890879587b61e87efcdec318b07ae95ba223cb5` ; 20203 octets.

## Modifications réellement appliquées

31 corrections ponctuelles ont été appliquées. Elles développent INSEE, EPCI, NIC et RBC, explicitent BV et IC dans la nouvelle table, corrigent les ellipses de support statistique, la liaison des conditions de la voie B, la terminologie des dénombrements et la syntaxe du rang de covariance. Le texte distingue la variable de résultat de son estimation et n’utilise plus la métaphore de fermeture d’un candidat. « Interfaces » dans les diagnostics de couverture devient « caractéristiques ».

Les limitations de montagne, le dénominateur de revenu départemental, les fenêtres, seuils, nombres de groupes, niveaux d’incertitude et diagnostics défavorables sont maintenus. La formulation non causale reste cohérente entre résumé, résultats, discussion et conclusion.

Une précision de mesure expressément autorisée après l’audit B corrige la transformation en `log(1+n)`, où `n` est le dénombrement mensuel brut d’immatriculations. Le programme `src/analysis/estimate.py`, lignes 61 et 64, confirme cette définition ; aucun résultat n’est recalculé par cette revue.

La seule insertion de nouveaux nombres est la description du candidat E, expressément demandée par le responsable et vérifiée dans `reports/review_B_E_assignment_support.csv`. À 1 000 euros : 14/34 EPCI et 13 revenus distincts du côté éligible ; à 1 500 euros : 16/50 EPCI. Les quatre fenêtres échouent au minimum opérationnel ; aucune nouvelle variable d’immatriculations n’est examinée pour ce candidat. Le hash de la source et le texte inséré figurent dans le JSON.

## Fidélité et portée

Hors ce paragraphe E autorisé, toutes les suites de chiffres existantes, toutes les macros de faits et toutes les commandes LaTeX existantes sont conservées dans leur ordre. Aucun caractère `%` non échappé n’est présent dans les deux sources ou les sept nouvelles tables. L’identité de l’auteur, les références, URL, labels, formules d’estimation et chemins de figures sont préservés ; le seul changement de symbole est le `y` vers `n` demandé pour la définition logarithmique.

Le résumé contient 290 mots séparés par des espaces avant expansion des macros.

Les formulations des tables sont compréhensibles avec leurs notes. Deux améliorations typographiques restent facultatives : séparer les milliers des revenus et écrire « exclusion de l’EPCI entier » dans le générateur du support. Ces détails ne changent ni les valeurs ni les conclusions.

## Tables générées examinées

- `paper/generated/assignment_paths.tex` : `572b81ad39f2b2c76cfa32aab80372944bd8b3bab82673e4983867c5f66f8244`.
- `paper/generated/assignment_support.tex` : `d0bec7095e0c03720b38d02a46b4c184aa8922c813d9f337e63bba6a9976da62`.
- `paper/generated/assignment_thresholds.tex` : `2fbcd948922c794bef695f67823081d484877824ac3f0512265657d6047e4438`.
- `paper/generated/bassin_rd_clustering.tex` : `ac0e614758853cc1fd858813385db813a97be8c8344815af83046b6dce366a77`.
- `paper/generated/bassin_rd_covariates.tex` : `5b4e53d2d10553fc1ff63ae7b759ef7e6494258c6ec1c2f6f4766c8113b3fb6e`.
- `paper/generated/bassin_rd_placebos.tex` : `1212064b56dcbfbdd8f3fde40f931f0e2560f25424eaa52fb29c1d553e571361`.
- `paper/generated/bassin_rd_primary.tex` : `e41f16082d15ff59634b2f763fc4007c8d8b89d505e2377724c12997f59f2359`.

Le journal exhaustif des remplacements, les sources avant édition, la conservation des chaînes protégées et les vérifications de l’insertion E sont dans `paper/.paper-write-sci/run_20261004_review_D_final/analysis/`. La validité de cet avis est attachée aux empreintes ci-dessus ; de nouveaux ajouts substantiels requerraient une nouvelle lecture.
