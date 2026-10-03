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
