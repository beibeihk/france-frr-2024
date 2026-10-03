# Dictionnaire des données SIRENE et règles de reconstruction

Version du 3 octobre 2026. Audit documentaire initial ; les variables dérivées ci-dessous constituent des règles à appliquer et à vérifier dans le programme de construction. Elles ne signifient pas que le panel final ou les tests par établissement ont déjà été validés.

## Sources et traçabilité

Les six fichiers Parquet nationaux sont le stock officiel INSEE d'octobre 2026 : `StockEtablissement`, `StockEtablissementHistorique`, `StockUniteLegale`, `StockUniteLegaleHistorique`, `StockEtablissementLiensSuccession` et `StockDoublons`. Les dessins de fichiers et notices PDF, version du 15 janvier 2026, sont archivés dans `data/external/sirene_dictionary/`.

Les PDF renvoient à la documentation détaillée de l'API Sirene 3.11. La page du portail est une application JavaScript ; télécharger son HTML seul ne suffit pas pour lire les définitions. Le fichier public [de configuration du portail](https://portail-api.insee.fr/assets/config.json) indique le service officiel de documentation, accessible sans compte ni clé. `src/construct/dictionary_fetch.py` archive l'index public, les pages pertinentes, les dates de mise à jour et les empreintes SHA-256 dans `api_documentation_manifest.json`. Ce programme ne consulte aucun dossier individuel.

Références documentaires principales :

- [Présentation du répertoire et de l'historique](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/fe6ff23b-806b-44cd-aff2-3b806bb4cd62/content).
- [Variables des unités légales](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/2ed989b6-001c-4b22-9989-b6001c6b224e/content).
- [Variables des établissements](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/754efef5-1e50-41d3-8efe-f51e5071d320/content).
- [Variables des liens de succession](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/4728fec0-3b9f-49ed-a8fe-c03b9ff9ed01/content).
- [Diffusion partielle](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/8279ad8c-c12d-4a2c-b9ad-8cc12dea2c39/content).
- [Définitions, notamment Siret et unité légale](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/ec062de3-0fe6-4fd5-862d-e30fe6dfd5c3/content).
- [Évolutions Sirene 3.11/Sirene 4](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/41bc4d65-fca4-436d-bc4d-65fca4136dcd/content).

## Unités d'observation et types

| Variable brute | Fichier | Type Parquet constaté | Définition et traitement |
|---|---|---|---|
| `siren` | UL, établissements, historiques | VARCHAR, 9 caractères | Identifiant d'une unité légale ; conserver les zéros initiaux. Une unité légale n'est pas nécessairement une entreprise statistique au sens de la LME. |
| `nic` | établissements, historique | VARCHAR, 5 caractères | Numéro interne d'un établissement. |
| `siret` | établissements, historique | VARCHAR, 14 caractères | Identifiant d'un établissement, égal à `siren || nic`. Conserver comme chaîne, jamais comme nombre flottant. |
| `dateCreationEtablissement` | stock établissements | DATE | Date déclarée de création de l'établissement. Non historisée. `1900-01-01` ou NULL représentent une date inconnue à exclure d'un comptage daté. |
| `dateCreationUniteLegale` | stock UL | DATE | Date déclarée lors des formalités de création de l'unité légale. Non historisée ; même règle de date inconnue. |
| `dateDebut` | stocks et historiques | DATE | Début d'une période de valeurs constantes des variables historisées. Ce n'est pas une date de naissance. |
| `dateFin` | historiques | DATE | Dernier jour de la période, égal à la veille du début de la suivante. NULL désigne la situation courante, y compris lorsqu'elle est fermée/cessée. |
| `etatAdministratifEtablissement` | stock et historique établissements | VARCHAR | `A` actif administrativement ; `F` fermé. Un établissement fermé peut être rouvert. NULL n'est ni actif ni fermé. |
| `etatAdministratifUniteLegale` | stock et historique UL | VARCHAR | `A` actif administrativement, y compris en sommeil avec tous ses établissements fermés ; `C` cessé. Réactivation possible, notamment pour les personnes physiques. |
| `caractereEmployeurEtablissement` | stock et historique établissements | VARCHAR | `O` employeur ; `N` non-employeur ; NULL information absente. Variable déclarative historisée. La fermeture ne remet pas automatiquement `O` à `N`. |
| `caractereEmployeurUniteLegale` | stock et historique UL | VARCHAR | Champ conservé mais plus géré dans Sirene 3.11 alimenté par Sirene 4 ; toujours NULL dans le stock examiné. Inutilisable pour une mesure d'emploi. |
| `activitePrincipaleEtablissement` et `nomenclatureActivitePrincipaleEtablissement` | stock et historique établissements | VARCHAR | APE et nomenclature correspondante. Classification de l'établissement, historisée depuis 2005. Ne pas remplacer l'APE à la naissance par l'APE courant. |
| `activitePrincipaleUniteLegale` et nomenclature | stock et historique UL | VARCHAR | APE de l'ensemble de l'unité légale ; concept distinct de l'APE de chaque établissement. |
| `activitePrincipaleNAF25Etablissement` / UL | stocks courants | VARCHAR | Code NAF25 informatif, non historisé ; ne pas utiliser pour classer les créations 2018–2026. La documentation annonce l'entrée en vigueur de NAF25 le 1er janvier 2027. |
| `categorieJuridiqueUniteLegale` | stock UL ; historique UL | BIGINT ; VARCHAR | Catégorie juridique. Normaliser en chaîne de quatre caractères avant comparaison ; utiliser la valeur historique au moment étudié. |
| `codeCommuneEtablissement` | stock établissements | VARCHAR, 5 caractères | Commune de localisation ; non historisée. Code BAN lors de la plus récente formalité de modification d'adresse. NULL pour l'étranger. Harmoniser les anciens codes avec les mouvements COG avant le rattachement au zonage FRR. |
| `statutDiffusionEtablissement` / UL | stocks courants | VARCHAR | `O` diffusible, `P` diffusion partielle. Ne pas confondre avec le `O` du caractère employeur. Statut courant, non historisé. |
| `etablissementSiege` | stock établissements | BOOLEAN | Qualité de siège courante, non historisée. Ne donne pas le siège à la création de l'unité légale. |
| `nicSiegeUniteLegale` | stock et historique UL | VARCHAR, 5 caractères | NIC du siège durant la période considérée. Permet d'identifier le siège à une date antérieure. |
| `trancheEffectifsEtablissement` / UL | stocks courants | VARCHAR | Tranche statistique non historisée, observée au 31 décembre de l'année millésime N et diffusée généralement à l'automne N+2. |
| `anneeEffectifsEtablissement` / UL | stocks courants | BIGINT | Année de référence de la tranche, pas l'année de diffusion. Conserver explicitement. |
| `unitePurgeeUniteLegale` | stock UL | BOOLEAN | Historiques des unités cessées avant fin 2002 purgés ; couverture des anciens établissements incomplète. Ne pas reconstruire leur trajectoire à partir de la seule ligne conservée. |
| `dateDernierTraitement*` | stocks | TIMESTAMP | Date de traitement/dernière mise à jour administrative, distincte de la date d'effet d'un événement. Ne sert pas à dater une création, fermeture, embauche ou succession. |

## Règles temporelles

Pour une date d'observation `t`, la sélection de l'historique est :

```sql
dateDebut <= t AND (dateFin >= t OR dateFin IS NULL)
```

Les deux bornes sont inclusives. Une période avec `dateFin = 2024-06-30` n'est pas valide au 1er juillet 2024. Une période courante `F` n'est pas une survie. Des périodes antérieures à la création et des premières valeurs NULL existent par construction ; la première `dateDebut` ne remplace jamais `dateCreation*`. Un changement d'enseigne, d'APE ou de caractère employeur crée une période sans nécessairement changer l'état administratif.

Pour compter un stock mensuel de fin de mois, sélectionner la période contenant le dernier jour du mois et ajouter `dateCreationEtablissement <= t`. Les dates `1900-01-01` sont traitées comme inconnues. Les intervalles indatables sont exclus de la reconstruction datée et leur nombre est publié. Si la mesure mensuelle vise plutôt « actif au moins un jour du mois », elle nécessite une intersection d'intervalles et doit porter un nom distinct.

Les historiques du stock 2026 sont des dates d'effet révisées disponibles au moment de l'extraction. Ils ne constituent pas une série de millésimes mensuels tels que les chercheurs les auraient observés en temps réel en 2024. Les révisions rétroactives et retards de déclaration doivent figurer dans les limites.

## Variables dérivées prévues pour l'étude

| Nom proposé | Construction admissible | Interprétation et limite |
|---|---|---|
| `establishment_registrations` | Nombre de SIRET distincts dont `dateCreationEtablissement` appartient au mois, quel que soit leur état courant en 2026. | Créations déclarées d'établissements ; ne pas sélectionner seulement les survivants du stock courant. |
| `employer_at_registration` | Parmi ces créations, caractère employeur `O` dans la période contenant la date de création, avec état établissement `A`. | Établissements déclarant être employeurs au démarrage ; pas un nombre d'emplois. Valeur NULL = inconnue. |
| `first_observed_employer_entry` | Première entrée documentée dans un état `A` et `O`, après une période observée `A` et `N`, et après la création. Fusionner les périodes consécutives où seul un autre attribut change. | Première transition administrative observée vers employeur, susceptible de retard de déclaration ; pas nécessairement première embauche économique. À distinguer d'un employeur à la création, d'une réembauche et d'une réouverture. |
| `active_establishment_stock` | Nombre de SIRET distincts administrativement `A` à la date mensuelle ; utiliser l'historique. | Stock administrativement actif ; ne prouve ni production, ni ventes, ni emploi. |
| `active_employer_stock` | Même sélection, avec caractère employeur `O` dans la même période. | Stock d'établissements actifs déclarés employeurs, pas effectif salarié. |
| `administrative_survival_12m` | Pour une cohorte de création, état `A` à la date de création + 12 mois, avec traitement explicite des réouvertures et des observations censurées. | Présence administrative à 12 mois. Ne pas qualifier de survie économique ; une mesure de survie continue doit vérifier l'absence de fermeture intermédiaire. |
| `legal_unit_registrations` | SIREN distincts selon `dateCreationUniteLegale`. Rattacher la naissance au `nicSiegeUniteLegale` historique contenant cette date, puis à son SIRET et à sa commune harmonisée. | Nouvelles unités légales ; l'absence de siège historique identifiable rend la naissance non localisable. Ne pas lui affecter la commune du siège courant. |
| `registration_without_recorded_continuity` | Créations d'établissements après exclusion/qualification des successions économiquement continues, selon une règle temporelle documentée. | Créations sans continuité enregistrée, pas « créations économiques pures » certaines. Les liens sont incomplets. |
| `recorded_headquarters_transfer` | Lien de succession avec `transfertSiege=true`, daté selon `dateLienSuccession` ; géographie du prédécesseur et du successeur harmonisée. | Transfert de l'établissement siège ou transfert de la qualité de siège ; ce dernier peut ne pas constituer une mobilité géographique. |

Une période `O` couvrant la naissance doit dater l'employeur à la naissance par `dateCreationEtablissement`, même si sa `dateDebut` est antérieure. En revanche, une première période observée `O` sans état `N` observé antérieurement ne permet pas d'affirmer une première embauche. Ne pas convertir une valeur NULL en `N`. Le caractère employeur conservé lors de la fermeture impose de combiner état et employeur dans les stocks et transitions.

L'APE est sélectionné à la naissance ou à la date de transition ; il faut conserver la nomenclature et publier la part non classable. Le champ de l'étude et les activités exclues suivent l'APE de l'époque et, si nécessaire, la catégorie juridique historique. Un APE statistique ne constitue pas à lui seul une preuve d'éligibilité fiscale individuelle.

## Succession, transferts et doublons

| Variable / cas | Définition officielle | Conséquence pour l'étude |
|---|---|---|
| `siretEtablissementPredecesseur`, `siretEtablissementSuccesseur` | SIRET avant/après la succession ; chaînes de 14 caractères dans le Parquet. | Jointure locale uniquement ; contrôler la disponibilité des deux extrémités et éviter toute publication des identifiants. |
| `dateLienSuccession` | Date d'effet de la succession. | Dater le flux par cette date, et comparer explicitement à la date de création du successeur. |
| `dateDernierTraitementLienSuccession` | Date d'enregistrement du lien. | Permet de documenter les décalages d'enregistrement ; ne pas l'utiliser comme date économique. |
| `continuiteEconomique` | Vraie quand au moins deux critères sont remplis : même SIREN, même APE, même lieu. Toujours vraie en cas de transfert de siège. | Une règle administrative de continuité, pas une observation des salariés, du chiffre d'affaires ou des équipements transférés. |
| `transfertSiege` | Transfert de l'établissement siège ou de sa qualité de siège. Faux pour les seuls établissements secondaires et pour une cession entre unités légales. | Ne pas traiter `false` comme absence de transfert d'activité ; des transferts d'établissements secondaires existent. |
| Relations multiples | Plusieurs prédécesseurs/successeurs possibles ; un établissement peut transférer une partie de son activité sans fermer. | Éviter une jointure many-to-many qui gonfle les créations. Agréger un indicateur au niveau SIRET avant de compter ; conserver séparément le nombre de liens. |
| Absence de lien | Couverture liée aux déclarations ; tous les liens ne sont pas connus de l'INSEE. Secteur public et unités purgées exclus du fichier de liens. | Absence de lien ≠ preuve d'absence de reprise. Indiquer la portée limitée de l'exclusion. |
| `siren`, `sirenDoublon` dans `StockDoublons` | `siren` est l'identifiant valide ; `sirenDoublon` celui créé à tort. | Direction correcte du rapprochement : doublon → valide. Contrôler chaînes/cycles et ne pas appeler ces doublons de nouvelles unités légales. |

Dans les Parquet, `transfertSiege` et `continuiteEconomique` sont déjà de type BOOLEAN. Ne jamais convertir un texte `"false"` avec une simple vérité logique de chaîne ; dans une source CSV, accepter explicitement les modalités `true`/`false` et traiter les autres comme erreurs. Un lien futur ou tardif ne doit pas éliminer silencieusement une naissance passée : la règle de proximité entre `dateLienSuccession` et `dateCreationEtablissement` doit être explicite et faire l'objet d'une variante de robustesse. Une exclusion « tout successeur observé » décrit une autre mesure, sensible à des événements ultérieurs.

## Géographie et diffusion partielle

La commune reste diffusée pour les établissements `P`. La diffusion partielle masque les identifiants personnels et l'adresse détaillée, y compris le code postal et les coordonnées, mais pas `codeCommuneEtablissement`. Garder `P` dans les résultats communaux lorsqu'une commune exploitable existe ; distinguer les véritables NULL, les territoires hors champ et les codes non appariés. Ne pas tenter de reconstituer les champs masqués.

Le changement d'adresse ferme normalement l'ancien établissement selon la définition SIRET de l'INSEE. Cela permet de rattacher un historique administratif à la commune de son SIRET, après harmonisation COG, mais ne rend pas la commune une variable historisée. Fusions/suppressions de communes, actualisations BAN et corrections restent à contrôler. La reconstruction d'une naissance d'unité légale nécessite son siège à la naissance, distinct du siège courant.

Les champs de noms, prénoms, enseignes, dénominations, rues et adresses détaillées sont exclus des projections analytiques et des sorties. Les fichiers contenant SIREN/SIRET demeurent localement dans `data/intermediate/`, ignoré par Git. Les sorties destinées à la publication sont agrégées par commune, mois et catégorie, avec le contrôle de divulgation applicable.

## Contrôles agrégés du stock d'octobre 2026

Contrôles réellement exécutés par `python src/construct/dictionary_fetch.py --audit-snapshot` ; requêtes et résultats archivés dans `snapshot_audit_aggregates.json`. Ils couvrent la France entière, avant la restriction au champ FRR, et ne sont pas des résultats de recherche.

| Contrôle | Résultat |
|---|---:|
| Établissements totaux | 44 282 364 |
| Diffusion `O`, dont commune non NULL | 38 508 105 ; 38 136 018 |
| Diffusion `P`, dont commune non NULL | 5 774 259 ; 5 768 121 |
| Commune égale à `[ND]` | 0 |
| Année de tranche salariés renseignée | 2024 uniquement ; 2 479 494 établissements |
| Année de tranche salariés NULL | 41 802 870 établissements |
| Établissements courants `A` et employeurs `O` | 2 435 435 |
| Établissements courants `F` conservant employeur `O` | 4 922 388 |
| UL avec caractère employeur NULL | 30 148 401, soit toutes les UL du fichier |
| Liens sans transfert de siège et sans continuité | 1 990 596 |
| Liens sans transfert de siège, avec continuité | 6 450 858 |
| Liens avec transfert de siège et continuité | 1 364 123 |
| Liens avec transfert de siège, sans continuité | 0 groupe observé |
| Périodes établissements | 96 657 561 |
| Début NULL / `1900-01-01` | 517 749 / 587 687 |
| Périodes courantes, dateFin NULL | 44 282 364 |
| Périodes avec dateFin < dateDebut | 0 |

Le millésime 2024 des tranches, observé dans le stock de 2026, confirme leur décalage statistique. Il ne permet pas une reconstruction d'effectifs salariés mensuels. La validation d'adjacence des intervalles, l'unicité des jointures, le classement aux dates d'événement et les contrôles manuels d'au moins 20 établissements demeurent requis avant toute validation finale du panel.


# Dictionnaire du panel agrégé et des fichiers d’analyse

Unité : commune INSEE × mois. Les comptes absents sont zéro seulement après construction d’un domaine équilibré de communes stables et jointure de comptes réellement agrégés. Une variable administrative individuelle manquante n’est jamais imputée comme non-employeur, fermeture ou activité connue.

| Champ | Définition et limite |
|---|---|
| commune_code | Code INSEE conservé en chaîne, zéros initiaux préservés. Pas un code postal. |
| month | Premier jour du mois civil, janvier 2019 à juin 2026. |
| establishment_births | Date de création d’établissement dans le mois, toute immatriculation du champ stable, état de naissance A/F/inconnu conservé. |
| legal_unit_births | Date de création d’unité légale dans le mois, située au siège historique à cette date. Les non-localisables ne sont pas des zéros. |
| individual_births | Sous-ensemble localisable de catégorie juridique historique 1000. |
| employer_births | Naissances d’établissement historiquement actif A et caractère employeur O au moment de création. Pas un effectif d’emploi. |
| known_employer_births | Naissances historiquement actives A avec caractère O ou N ; dénominateur connu de l’indicateur employeur. |
| unknown_naf_births | NAF manquante ou nomenclature différente de NAFRev2 à la naissance. |
| recorded_continuity_births | Lien officiel de succession à la même date de création, avec continuité économique vraie. |
| births_without_recorded_continuity | Complément du précédent, pas preuve de création économique originale. |
| commerce | NAF Rev.2 45–47. |
| accommodation_food | NAF Rev.2 55–56. |
| construction | NAF Rev.2 41–43. |
| manufacturing | NAF Rev.2 10–33. |
| professional_services | NAF Rev.2 69–75. |
| health | NAF Rev.2 86, santé humaine. |
| proximity_services | NAF Rev.2 95–96, définition opérationnelle étroite. |
| establishment_closures | Transitions historiques A→F dans le mois pour les établissements du domaine. |
| registration_minus_closure_balance | establishment_births − establishment_closures ; pas une variation nette du stock actif. |
| population_2021 | Population municipale préalable fixe, référence INSEE 2021 applicable début 2024. |
| density_2021 | Population fixe / surface du polygone officiel en km² ; mesure calculée, pas reconstitution des critères officiels d’assignation. |
| treatment_group | Nouvelle FRR initiale / ancienne ZRR maintenue / ancienne bénéficiaire / non-bénéficiaire des listes auditées / exclue. |
| analysis_stable | Filtre géographique et démographique ; n’implique pas appartenance aux groupes utilisés dans les estimations. |
| epci_2023, epci_2024 | Appartenance officielle ; les changements sont exclus du domaine stable. |
| classification_path | La voie juridique FRR déterminante n’est pas reconstruite. Les chemins anciens ZRR sont documentés ; absence de RD. |

`secondary_administrative_events.parquet` ajoute les transitions F→A d’établissements, A→C et C→A d’unités légales localisables au siège de la période d’événement. Les pertes de localisation sont diagnostiquées, pas recodées comme absence économique d’événement.

`administrative_retention_cohorts.parquet` utilise commune × mois de création × horizon (12/18 mois). `n_registered_cohort`, `n_censored`, `n_eligible`, `n_active_at_horizon`, `n_closed_at_horizon`, `n_unknown_horizon` distinguent les dénominateurs. L’état A à l’anniversaire peut suivre une réouverture. Les taux connus et bornes inconnues sont distincts ; aucune survie économique ou continue n’est affirmée. Le fichier `cohort_retention.csv` pondère les cohortes par leurs comptes, avec une composition d’entrants potentiellement affectée par la politique.

L’âge administratif d’un établissement est défini par sa date de création ; les anniversaires servent au suivi. Aucun âge moyen d’entreprise en activité, effectif historique positif, chiffre d’affaires, impôt perçu, montant d’exonération, profit ou droit fiscal individuel n’est imputé à partir des tranches courantes. Un indicateur de siège courant ne serait pas un indicateur de siège au moment de création.

`birth_structure.parquet` complète les naissances avec `headquarters_births`, `non_headquarters_births`, `unknown_headquarters_births` et les causes d’incertitude selon le NIC historique de l’unité légale à la date de création de l’établissement. L’âge déclaré de l’unité légale à cette date fournit les nombres connus/inconnus, jours et mois calendaires accomplis, sommes, carrés et moyennes parmi les connus. Chaque immatriculation est une contribution ; une unité ouvrant plusieurs établissements apparaît plusieurs fois. Les dates avant1800 sont des contrôles analytiques postérieurs à l’inspection, pas des sentinelles officielles ; elles restent comptées dans les créations, avec âge inconnu. Le siège d’une personne physique est une analogie administrative SIRENE, sans réalité juridique propre. Aucune moyenne d’âge d’entreprises actives ni analyse causale de composition n’est déduite de ce fichier.


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
