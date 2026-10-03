# France ruralités revitalisation : reconstruction et diagnostics

Kun Huang — Economics and Management School, Wuhan University. Document de travail en français, 4 octobre 2026.

Le projet reconstitue l’éligibilité initiale FRR avec les revenus et populations de 2020 dans les périmètres de 2023, mesure les immatriculations administratives et documente les limites de leur évaluation. L’union des voies obligatoires vérifiées et des voies possibles reproduit les 17 672 communes métropolitaines initialement classées. Elle n’identifie pas les décisions préfectorales individuelles ni la population dans les seules parties de communes classées en montagne.

Les comparaisons frontalières, larges et appariées, ainsi que le candidat au seuil de revenu des bassins, sont **non causales**. Tous les diagnostics défavorables sont conservés. Les résultats ne prouvent ni création nationale nette, ni emploi supplémentaire, ni inefficacité de FRR. `reports/final_quality_gate.json` décrit les contrôles matériels et internes effectivement achevés ; `submission/submission_record.md` décrit exclusivement les opérations HAL réellement observées. HAL est une archive ouverte, pas une revue à comité de lecture.

## Contenu

- `paper/main_fr.pdf`, `paper/appendix_fr.pdf` et leurs sources LaTeX : article et annexe technique.
- `data_sources.csv`, `data_dictionary.md`, `claims_audit.csv`, `references_verified.csv` : millésimes, empreintes, définitions et faits vérifiés.
- `data/processed/monthly_panel.parquet` : comptes communaux mensuels ; `bassin_rd_monthly_aggregates.parquet` : agrégats du champ fixe des bassins.
- Tables communales d’affectation, membres et candidats : codes administratifs publics, aucune donnée individuelle SIRENE.
- `results/tables`, `results/figures`, `paper/generated` : sorties et faits numériques générés, sans coefficients saisis dans le texte.
- `src`, `run_pipeline.py`, `requirements*.txt` : téléchargement figé, transformations, estimateurs et génération.
- `reports/review_*`, `docs/assignment_rd_protocol.md`, `docs/design_changes.md` : examens internes indépendants par IA et chronologie réelle. Ils ne sont pas présentés comme une expertise extérieure humaine ou une relecture humaine de langue maternelle française.

Le paquet public suit une liste positive dans `src/tables/build_public_package.py`, avec empreintes dans `public_manifest.csv`. Les stocks SIRENE, intermédiaires individuels, géométries lourdes, agrégats détaillés d’âge et de suivi des cohortes, dépendances binaires et informations d’authentification sont exclus. Les programmes permettent de reconstruire localement ces sorties.

## Reproduction

Python 3.11 a été effectivement utilisé. Installer les dépendances principales dans un environnement dédié et les versions RD dans un répertoire isolé ; les deux environnements n’emploient pas le même statsmodels/matplotlib :

```powershell
python -m pip install -r requirements.txt
python -m pip install --target .vendor_rd --no-deps -r requirements_rd.txt
python run_pipeline.py --download --rebuild --compile
```

Le téléchargement vérifie les octets et SHA-256 du millésime exact. Il refuse de substituer une livraison ultérieure. La disponibilité future des anciennes URL n’est pas garantie. Les instantanés de l’annexe juridique initiale dans `docs/sources/frr_2024` reproduisent l’extraction officielle lorsque Légifrance oppose un HTTP 403 au téléchargement ordinaire. Aucun code de traitement n’est tiré d’une copie non officielle.

La construction exploite les six fichiers nationaux SIRENE par projections/jointures DuckDB, sans charger les stocks entiers dans pandas. Prévoir plusieurs dizaines de Go disponibles pour les sources, intermédiaires et temporaires ; l’espace exact dépend des projections et de la configuration. Les sources EPCI et bassin sont extraites des ZIP officiels ; un défaut OOXML est contourné par lecture des valeurs sans altérer le fichier d’origine. Aucun rapprochement de communes par nom n’est utilisé.

```powershell
python run_pipeline.py --figures --compile
```

Cette seconde commande suffit avec les sorties locales déjà reconstruites. `--compile` seul utilise les figures et tables fournies. Le projet LaTeX est multi-fichier et utilise XeLaTeX/BibTeX déjà installés ; le pipeline ne les installe pas. Les chemins TeX peuvent être trouvés sur PATH ; le chemin Windows existant n’est qu’un repli. Aucune reconstruction sur une seconde machine n’est affirmée.

L’audit a réextrait vingt cellules depuis les stocks bruts (340 comptes et 180 attributs), puis vérifié les catégories de siège/âge (520 comparaisons), les 1 044 480 champs de la reconstruction juridique et les estimations V par une seconde implémentation. Ces succès portent sur les calculs contrôlés, pas sur toutes les erreurs possibles du registre ou les hypothèses causales.

## Choix de mesure et méthode

Fenêtre initiale : juillet–décembre 2024 ; référence des comparaisons communales : mêmes mois 2019–2022. FRR+ a une éligibilité rétroactive en janvier 2025 : les mois suivants ne sont pas assimilés à un régime initial homogène. Les 774 paires sont disjointes, choisies avant résultats par cardinalité maximale et codes déterministes, avec plus de 50 m de frontière commune. Les composantes relient les deux rôles administratifs.

Les ratios communaux utilisent la population fixe de 2021 ; le candidat bassin utilise celle de 2020. Le `log(1+nombre)` porte sur le dénombrement brut. Les entrées SIRET ne sont pas assimilées aux statistiques INSEE de créations économiques. Siège et état sont historiques ; les inconnues ne sont pas des zéros. Maintien à l’anniversaire n’est pas survie économique continue ; immatriculations moins fermetures n’est pas variation du stock actif.

Les candidats EPCI A/B/D/E manquent de support. V a 119/79 bassins autour de 21 600 euros à ±1 000, mais la couverture sélectionnée est discontinue, les 53 niveaux préalables sont incompatibles avec leur continuité sous HC3, et la dépendance est concentrée. Les quatre rayons restent disponibles. Les tests groupés de rang32/9 ne sont pas présentés comme un test complet des 53 restrictions. Aucun candidat n’a reçu de validation causale. Les protocoles sont des décisions locales séquentielles après les premières comparaisons, pas un pré-enregistrement externe.

## Licences et provenance

Voir `LICENSES.md` et `docs/public_release_rights.md`. Les contributions originales des PDF sont sous CC BY 4.0 ; le code original est sous MIT. Les comptages issus d’INSEE et les tables administratives conservent les attributions et conditions des sources. Les tables dérivées des contours sont sous ODbL 1.0. Les cartes portent une notice de base et de licence. Les contributions de tiers ne sont pas relicenciées uniformément par la licence du manuscrit.

Fond : [Contours administratifs, data.gouv.fr](https://www.data.gouv.fr/datasets/contours-administratifs), communes2024, généralisation5m, source IGN Admin Express, [ODbL1.0](https://opendatacommons.org/licenses/odbl/1-0/). Les scripts de transformation et contenus supplémentaires nécessaires sont fournis pour l’alternative de reconstruction du §4.6. Les comptages indépendants SIRENE ne deviennent pas automatiquement ODbL. Source SIRENE : Insee, livraison du1octobre2026, stock au30septembre2026 ; sources revenu/population : Insee2020, géographie2023 ; liste ZRR : ANCT ; FRR : DGCL/Légifrance ; montagne : DGALN-SIDAUH, COG2022.

L’absence d’identifiants individuels dans le paquet ne constitue pas une certification d’anonymat absolu. Aucun champ masqué n’est reconstitué. L’assistance substantielle de Codex est déclarée dans le manuscrit ; Kun Huang est le seul auteur humain responsable.
