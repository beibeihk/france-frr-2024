# Dictionnaire des variables d'affectation FRR initiale de 2024

Version du 4 octobre 2026. Documentation issue d'un contrôle par IA des sources et des calculs ; elle ne constitue pas une certification par un expert humain. Ce fichier porte sur les variables d'affectation territoriale. Aucun résultat d'activité économique n'a été lu pour ce contrôle.

## Sources, années et périmètres

L'article 73 de la LFI 2024, dans sa version initiale, fixe les données disponibles au 1er juillet de l'année précédant le classement, la population municipale pour la densité et le périmètre des EPCI au 1er janvier de cette année. Pour le classement initial de 2024, les dates correspondantes sont le **1er juillet 2023** et le **1er janvier 2023**. L'intervention de Dominique Faure au Sénat du 26 novembre 2023 précise l'emploi du recensement 2020 et de Filosofi 2020 : [compte rendu officiel](https://www.senat.fr/cra/s20231126/s20231126.pdf), page PDF 66, page imprimée 63.

| Fichier officiel nécessaire | Année des données | Géographie | Publication | Champs utilisés |
|---|---|---|---|---|
| [Filosofi 2020](https://www.insee.fr/fr/statistiques/6692392?sommaire=6692394), archive `insee_filosofi2020_geog2023_csv.zip` | 2020 | 2023-01-01 | 2023-04-24 | `CODGEO`, `MED20`, tables COM/EPCI/BV2022/DEP |
| [Séries historiques 2020](https://www.insee.fr/fr/statistiques/7632565), archive `base-cc-serie-historique-2020_csv.zip` | 2020 | 2023-01-01 | 2023-06-27 | `CODGEO`, `P20_POP`, `SUPERF` |
| [Loi Montagne 1985, DGALN-SIDAUH](https://www.data.gouv.fr/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022), `mountain_cog2022.xlsx` | Zonage juridique, pas un millésime de population | 2022-01-01 | Correction de ressource du 2022-03-23 | `Perimetre.INSEE_COM`, réglementation, historique des fusions |
| [Composition EPCI 2023](https://www.insee.fr/fr/statistiques/fichier/2510634/Intercommunalite_Metropole_au_01-01-2023.zip) | Composition territoriale | 2023-01-01 | Non établie indépendamment ici | `EPCI`, `NATURE_EPCI`, `CODGEO`, `DEP` |
| [Composition BV2022 en COG2023](https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip) | Zonage BV défini en 2022 | 2023-01-01 | Non établie indépendamment ici | Commune et bassin de vie |

Les fichiers de population et de revenu ont été publiés avant la date légale de disponibilité. `population_2021.xlsx`, utilisé ailleurs pour les taux descriptifs, n'est pas l'entrée du calcul d'affectation. Le fichier légal de population 2020 en COG2022 sert uniquement au contrôle du concept de population ; il n'est pas joint sans conversion au périmètre 2023.

`data_sources.csv` conserve les 53 sources antérieures et ajoute les trois premières archives comme `required_rebuild=true`, `retrieval=http_binary`. Les SHA256 et tailles sont calculés sur les fichiers effectivement conservés. Les téléchargements du revenu et du recensement ont respectivement été enregistrés le `2026-10-03T16:30:28.667850+00:00` et le `2026-10-03T16:35:57.829018+00:00`. Aucune heure de téléchargement de l'archive montagne n'a été retrouvée dans les journaux conservés : le champ reste vide. La date du fichier ou la date de publication ne remplace pas une heure de récupération.

Les deux archives INSEE sont soumises, sauf mention contraire, à la [Licence Ouverte 2.0 selon les mentions légales officielles](https://www.insee.fr/fr/information/2008466). La métadonnée officielle du jeu montagne indique `lov2`. Le compte rendu du Sénat est copié sous `docs/sources/assignment2024/`, inscrit comme preuve facultative et non comme donnée nécessaire à l'affectation. Sa licence spécifique n'est pas présentée comme vérifiée. Les couches ArcGIS actuelles FRR_plus et les autres pistes de découverte ne sont pas inscrites comme entrées d'affectation 2024.

## Tables de valeurs et identifiants

Les codes sont des chaînes : conserver les zéros initiaux et les codes `2A`/`2B`. `COM`, `EPCI`, `BV2022` et `DEP` identifient des niveaux différents ; la clé de revenu est `(level, code)`.

### `assignment2024_income.csv`

| Champ | Définition |
|---|---|
| `level`, `code` | Niveau et code officiel de la table de revenu |
| `med2020` | Valeur officielle native de `MED20`, en euros |
| `metadataGeography` | `2023-01-01` |
| `income_reference_year` | `2020` |
| `source_table`, `source_variable` | Table officielle et variable `MED20` |
| `income_unknown` | Absence ou suppression statistique de `MED20` dans une ligne publiée |

`MED20` est la médiane du niveau de vie : revenu disponible du ménage divisé par les unités de consommation, selon la [définition INSEE](https://www.insee.fr/fr/metadonnees/definition/c1890). Il ne s'agit ni d'un revenu fiscal moyen ni d'une moyenne des revenus médians des communes. Chaque niveau utilise son indicateur directement publié. **Aucune moyenne, pondérée ou non, des médianes communales ne reconstruit la médiane EPCI/BV/DEP.** Les valeurs publiées peuvent être arrondies et sont soumises au secret statistique.

La table contient 37 907 lignes : 34 874 COM, 1 240 EPCI, 1 695 BV2022 et 98 DEP. Après filtrage des COM sur les communes réelles, 3 599 valeurs publiées sont vides. Parmi les 34 945 communes du référentiel, 71 sont absentes de la table COM ; aucune n'est métropolitaine. Une ligne absente devient également inconnue après jointure gauche. Ni un zéro ni une moyenne ne remplace une donnée inconnue. Les 1 232 EPCI-FP, 1 681 BV et 96 départements métropolitains disposent tous d'un `MED20` publié.

### `assignment2024_commune_population_area.csv`

| Champ | Définition |
|---|---|
| `commune_code`, `department`, `epci_2023` | Appartenance communale officielle au 2023-01-01 |
| `P20_POP` | Population de 2020, exploitation principale du recensement |
| `SUPERF` | Superficie communale, en km², dans la géographie 2023 |
| `density2020` | `P20_POP / SUPERF`, habitants par km² |
| `metadataGeography`, `population_reference_year` | `2023-01-01`, `2020` |
| `source_table` | `base-cc-serie-historique-2020.CSV` |
| `is_actual_epci` | Appartenance à un véritable EPCI-FP, sans le marqueur `Sans objet` |

34 945 communes figurent dans la table, dont 34 816 en France métropolitaine. Les 45 arrondissements municipaux de Paris/Lyon/Marseille sont retirés des sommes, puisque les villes entières figurent déjà dans le référentiel. Les données de Mayotte, absentes du fichier de recensement, restent inconnues. Les trois sommes de populations légales des arrondissements municipaux égalent les populations entières de leurs villes dans `P20_POP`.

`ZZZZZZZZZ / NATURE_EPCI=ZZ` désigne l'absence d'EPCI, et non un EPCI commun aux îles. Les communes 22016, 29083, 29155 et 85113 relèvent de la règle propre aux communes isolées. `MED20` manque pour 29083, Île-de-Sein ; cette lacune est conservée. La densité connue de cette commune dépasse le seuil, de sorte que la conjonction de conditions A est fausse malgré le revenu inconnu.

### `assignment2024_territory_indicators.csv`

| Champ | Définition |
|---|---|
| `level`, `code` | EPCI, BV2022 ou DEP métropolitain |
| `population_2020` | Somme des populations des communes entières, composition 2023 |
| `area_km2` | Somme des superficies de ces mêmes communes |
| `density_2020` | `population_2020 / area_km2` |
| `median_income2020` | `MED20` natif du territoire, sans agrégation communale |
| `n_communes` | Nombre de communes dans la composition territoriale |
| `metadataGeography` | `2023-01-01` |

La table contient 3 009 unités : 1 232 EPCI-FP, 1 681 BV et 96 DEP. Les médianes de densité recalculées sont `63.569845464551264` pour EPCI et `70.84363836218742` pour BV ; elles reproduisent les affichages officiels 63,57 et 70,84. Les médianes de revenu sont 21 570, 21 600 et 21 665 euros ; le Q75 EPCI, par interpolation linéaire, est 22 822,5 euros. Les tests utilisent les médianes de densité recalculées en précision complète. La concordance numérique ne prouve pas que l'algorithme interne original ou les revenus non arrondis ont été récupérés.

## Table de chemins `assignment2024_commune_paths.csv`

Cette table contient 34 816 communes métropolitaines. Les colonnes élémentaires de population, revenu, densité et appartenance sont définies ci-dessus. Les préfixes `epci_`, `bassin_` et `department_` identifient le territoire dont l'indicateur provient ; `commune_income2020` demeure le revenu natif COM.

| Champ | Règle et interprétation |
|---|---|
| `actual_epci` | EPCI-FP réel ; les îles sans EPCI sont exclues de cette règle |
| `population_below30000` | Population de la **commune cible** strictement <30 000 ; pas une condition sur toutes les communes du bassin |
| `eligible_A_epci` | Population communale <30 000, EPCI densité ≤médiane et revenu ≤21 570 |
| `eligible_A_isolated_commune` | Même plafond communal, densité et revenu propres à la commune sans EPCI, comparés aux seuils A |
| `isolated_A_income_unknown` | Revenu manquant pour une commune isolée dont toutes les autres conditions A sont satisfaites |
| `department_qualifies` | DEP densité **<35**, revenu ≤21 665 |
| `eligible_C_department` | DEP qualifié et population de la commune <30 000 |
| `bassin_indicators_unknown` | Au moins un indicateur de densité/revenu BV manque |
| `bassin_potential` | Conditions numériques BV compatibles avec l'éligibilité, ou exclusion conservatrice des BV inconnus |
| `eligible_B_potential` | `bassin_potential` et population de la commune <30 000 ; **aucune proposition préfectorale n'est observée** |
| `mountain_any_commune2022` | Code communal mentionné dans le périmètre Loi Montagne COG2022, couverture éventuellement partielle |
| `mountain_membership_unknown` | Dans le script actuel, code 2023 absent du référentiel COM 2022 ; ce test seul ne prouve pas la stabilité d'une commune portant le même code |
| `mountain_population_upper` | Population entière si la commune a une couverture montagne ou une appartenance inconnue ; zéro dans les autres cas vérifiés |
| `epci_mountain_possible` | Somme de ces populations majorantes / population entière de l'EPCI ≥0,5 |
| `eligible_D_potential` | Plafond communal, EPCI réel, part montagne **majorante** ≥0,5, même seuil de densité A, revenu ≤22 822,5 |
| `listed_initial2024` | Présence dans l'arrêté initial officiel du 19 juin 2024, et non dans les ajouts de 2025 |
| `assignment_audit_status` | Comparaison des conditions nécessaires et chemins seulement possibles avec cette liste initiale |

La montagne majorante n'est pas une estimation de population légalement classée. La métadonnée officielle admet des parties de communes et maintient, après fusion, la qualification des seules parties déjà classées. Le fichier n'observe pas cette population infra-communale. `eligible_D_potential` ne doit donc pas être renommé `eligible_D`, et un membre montagne ne démontre pas que l'EPCI satisfait exactement le seuil de 50 %. Le contrôle indépendant des mouvements 2022→2023 a repéré 10 cibles de changement de périmètre/code ; aucune de leurs anciennes communes n'est listée montagne. Le maintien d'un code n'est pas, en général, un substitut à ce contrôle de mouvements.

La logique **unknown AND** est distincte d'une imputation : `false AND unknown = false` ; `true AND unknown = unknown`. Une règle est certainement satisfaite seulement si toutes ses conditions sont connues et vraies. Pour les écrans conservateurs, une règle incertaine peut conduire à exclure une observation candidate ; cette exclusion ne devient pas une preuve d'éligibilité. Le script principal BV traite actuellement toute absence d'indicateur comme potentiellement admissible, même si l'autre indicateur connu dépasse son seuil : c'est un écran plus large que la conjonction possible exacte. Les données BV actuelles sont complètes ; aucune différence numérique ne résulte de cette convention. L'audit indépendant emploie la conjonction possible exacte et retrouve les mêmes résultats.

Les chemins A et C sont les conditions déterministes, sous le plafond de population. B dépend encore d'une proposition du préfet de région et d'un arrêté ; D dépend du partage réel de population montagne. Les noms `potential` doivent être conservés, y compris lorsqu'une commune figure dans la liste initiale. Il n'existe pas ici de champ observé donnant la raison administrative de chaque classement.

## Statuts et contrôle de recouvrement

| Statut | Interprétation | Nombre actuel |
|---|---|---:|
| `verified_mandatory_path_listed` | A ou C déterministe et commune effectivement listée | 14 316 |
| `mandatory_path_missing_from_list` | A/C déterministe mais commune absente de la liste | 0 |
| `isolated_commune_income_unknown` | A isolé reste incertain après les autres conditions | 0 |
| `listed_without_reconstructed_possible_path` | Commune listée sans chemin A/C ni chemin B/D possible | 0 |
| `listed_only_potential_B_or_D` | Commune listée mais seulement B/D possible dans cette reconstruction | 3 356 |
| `not_listed_potential_discretionary_or_mountain_path` | Commune non listée malgré un chemin B/D possible | 0 |
| `not_listed_no_path` | Commune non listée et aucun chemin reconstruit | 17 144 |

A EPCI concerne 13 421 communes et A isolé une commune ; C en concerne 3 871. Le recouvrement A∩C est 2 977, donc A∪C comporte **14 316**, et non la somme brute des effectifs. Les conditions numériques B concernent 14 613 communes et D majorant 3 043 ; ces ensembles se recouvrent entre eux et avec A/C. Les 16 combinaisons observées sont conservées dans `reports/review_C_assignment_path_overlaps.csv`.

Les 17 672 communes listées métropolitaines plus 45 communes listées hors métropole correspondent aux 17 717 entrées de l'arrêté national. Le contrôle indépendant repart des archives officielles, sans appeler le script principal : **30 champs ×34 816 communes =1 044 480 valeurs comparées, zéro différence**. Les SHA256 du script principal et de son fichier de chemins figurent dans `reports/review_C_assignment_paths.json` et `.md`.

Cette compatibilité numérique de la liste avec les chemins nécessaires et possibles ne révèle pas les propositions préfectorales, ne mesure pas la part montagne exacte et ne constitue pas une validation causale. L'absence de conflits ne garantit ni support local suffisant, ni continuité au seuil, ni tendances parallèles.
