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
