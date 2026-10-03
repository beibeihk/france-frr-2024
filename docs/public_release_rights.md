# Droits de réutilisation et périmètre du paquet public

Revue C effectuée par une IA le **4 octobre 2026**, heure de Hong Kong. Cette revue documente les conditions publiées par les sources officielles et leur application au paquet envisagé. Elle ne constitue ni une certification juridique d’anonymisation, ni une validation scientifique du manuscrit, ni la preuve d’un dépôt dans HAL. Aucun compte, courrier, formulaire d’autorisation ou téléversement n’a été utilisé.

## Périmètre examiné

Le paquet envisagé comprend le PDF original de l’auteur, le code original, les URL et empreintes des sources, les dictionnaires de données, les tableaux administratifs communaux d’affectation et le panel de **comptages commune × mois**. Le manifeste final déterminera les fichiers effectivement distribués.

Le schéma actuel de `monthly_panel.parquet` contient 19 colonnes : deux clés géographiques et temporelles, puis des comptages ou un solde de comptages. Celui de `commune_treatment.csv` contient 19 colonnes administratives et géographiques ; il ne contient actuellement aucune superficie calculée à partir des contours. Les noms de communes sont des noms géographiques publics.

Les fichiers bruts SIRENE, les bases intermédiaires individuelles, les identifiants SIREN/SIRET, les noms de personnes, les adresses fines et les coordonnées de contact sont exclus. Les fichiers `birth_structure.parquet`, avec ses moments et extrema d’âge, et `administrative_retention_cohorts.parquet` sont également écartés du périmètre provisoire par minimisation ; leurs programmes restent reproductibles à partir des sources officielles. Cette décision ne prétend pas établir une interdiction générale de publier de tels agrégats. Les géométries Parquet ne sont pas prévues dans le paquet.

Cette vérification porte sur les schémas des fichiers candidats et les conditions des sources. Elle ne remplace pas l’inventaire final du paquet ni un examen de tous ses journaux et fichiers annexes.

## Conditions des sources

| Catégorie effectivement utilisée | Source officielle et licence constatée | Application au paquet |
|---|---|---|
| SIRENE, stocks et historiques publics | [Métadonnées INSEE sur data.gouv.fr](https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/) : `lov2`, Licence Ouverte 2.0 | Comptages statistiques avec provenance INSEE ; aucun fichier individuel redistribué. Les obligations de protection des personnes restent applicables. |
| INSEE, Filosofi 2020, recensement 2020, compositions et nomenclatures | [Conditions INSEE](https://www.insee.fr/fr/information/2008466), mises à jour le 13 avril 2026 : Licence Ouverte 2.0 sauf indication contraire | Mention « Source : Insee », millésime et mise à jour connue ; interprétation fidèle. La réutilisation commerciale est permise. Les logos et captures d’écran du site ne sont pas inclus. |
| Ancien classement ZRR de l’ANCT | [Jeu ANCT](https://www.data.gouv.fr/datasets/zones-de-revitalisation-rurale-zrr/) : `fr-lo`, Licence Ouverte / Open Licence | Attribution ANCT et version du classement. Les métadonnées ne précisent pas explicitement le numéro de version de la licence ; ne pas présenter ce code comme une mention explicite de la version 2.0. |
| Liste et documentation FRR de la DGCL sur le portail national | [Mentions légales du portail](https://www.collectivites-locales.gouv.fr/mentions-legales), pied de page : `etalab-2.0`, sauf propriété intellectuelle de tiers explicitement mentionnée | Attribution DGCL, titre et date du fichier. La licence d’un jeu régional publié par une DDT ne sert pas à établir celle de la liste nationale. |
| Communes de la loi Montagne, COG 2022 | [Métadonnées ministérielles](https://www.data.gouv.fr/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022) : `lov2` | Attribution Ministère de la Cohésion des territoires / DGALN-SIDAUH, COG 2022 et ressource mise à jour le 23 mars 2022 ; conserver les limites relatives aux communes partiellement classées. |
| Fond communal réellement téléchargé | [Contours administratifs, producteur data.gouv.fr](https://www.data.gouv.fr/datasets/contours-administratifs) : `odc-odbl`, **ODbL 1.0** | Appliquer les règles propres aux cartes et bases géographiques dérivées détaillées ci-dessous. Ne pas lui substituer une licence supposée d’un autre produit IGN. |

La [Licence Ouverte 2.0](https://www.data.gouv.fr/pages/legal/licences/etalab-2.0) permet notamment la reproduction, l’adaptation, la redistribution et l’exploitation commerciale, avec attribution et référence à la mise à jour. Elle n’autorise pas à suggérer une validation du projet par le producteur et ne dispense pas des règles concernant les données personnelles.

La ressource Montagne a été créée dans le catalogue le 10 mars 2022 (`created_at`) et mise à jour le 23 mars 2022 (`last_modified`). Son objet de métadonnées ne fournit pas de champ `published` : la date du 23 mars ne constitue donc pas une date officielle de publication établie. Cette précision corrige uniquement la qualification de la date ; le fichier source et ses valeurs sont inchangés.

### SIRENE et diffusion partielle

L’[avis officiel de l’API SIRENE](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/2cab50f0-0033-4763-ab50-f0003387636a/content) précise que les informations personnelles des unités ayant demandé la diffusion partielle ne doivent être ni entièrement rediffusées ni employées pour la prospection. Le statut `P` a remplacé l’ancien statut `N` le 21 mars 2023.

Le [dictionnaire officiel des établissements](https://api-apimanager.insee.fr/portal/environments/DEFAULT/apis/2ba0e549-5587-3ef1-9082-99cd865de66f/pages/754efef5-1e50-41d3-8efe-f51e5071d320/content) définit `codeCommuneEtablissement` comme un code communal public de cinq caractères ou une valeur nulle, sans modalité `[ND]`. Plusieurs champs d’adresse et d’identité sont au contraire explicitement masqués en diffusion partielle. Aucun champ masqué n’est reconstitué ni publié par le paquet envisagé.

**Interprétation circonscrite :** conserver les observations `P` dans des comptages communaux, à partir des variables effectivement publiques et sous Licence Ouverte, est compatible avec les droits de transformation constatés. Les sources consultées ne donnent toutefois pas une autorisation spéciale nommant ce panel commune × mois. L’agrégation ne doit donc pas être décrite comme une certification de conformité universelle ou d’anonymat absolu.

### Filosofi et secret statistique

La [publication Filosofi 2020](https://www.insee.fr/fr/statistiques/6692392?sommaire=6692394) indique que les résultats sont soumis au secret statistique et que la plupart des indicateurs ne sont pas sommables. Le projet utilise les valeurs `MED20` **natives du niveau géographique concerné**. Les cellules absentes ou masquées restent inconnues : aucune valeur supprimée n’est déduite, et aucune moyenne pondérée des médianes communales ne remplace une médiane intercommunale.

## Contours 2024, cartes et bases géographiques dérivées

La ressource utilisée est **« Communes 2024 5m (format GeoJSON compressé GZ) »**, identifiant `c1986a3e-cfa1-42a6-b8b6-ddfa3893f7e8`, [URL du fichier](https://object.data.gouv.fr/contours-administratifs/2024/geojson/communes-5m.geojson.gz). Le fichier local comporte 89 858 695 octets et son SHA256 est `2425dbf02c647480125615ca72d1a16e60abd6de154f21c86eb8a28d79f6ae5b`. Le millésime géographique est 2024 et la généralisation 5 m ; les métadonnées de la ressource indiquent une modification le 17 avril 2025.

Le producteur est data.gouv.fr. Sa page cite **IGN Admin Express** et, pour les COM, OpenStreetMap, sauf les sources officielles propres à la Polynésie française et à la Nouvelle-Calédonie. Pour les cartes métropolitaines du projet, attribuer le fond à data.gouv.fr et sa source IGN ; ne pas attribuer leur géométrie métropolitaine à OSM. Si le périmètre s’étend aux COM, reprendre les mentions pertinentes de ces sources.

Application du [texte ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) :

- Une carte publiée est un *Produced Work* : la notice doit nommer la base et renvoyer à sa licence (§ 4.3). La composition originale du PDF peut relever de CC BY 4.0, avec cette mention des droits tiers.
- Par prudence, les tables de contiguïté, de frontières, de paires géographiques et les superficies calculées à partir des contours sont traitées comme des bases dérivées, à distribuer sous ODbL (§ 4.4).
- Le § 4.6 permet d’offrir soit la base dérivée lisible par machine, soit **toutes** les modifications ou leur méthode, y compris les contenus ajoutés. L’absence de géométries Parquet est donc possible si le code public, ses paramètres et les données ajoutées permettent réellement la reconstruction complète, gratuitement. Un lien de téléchargement seul ne remplit pas cette alternative.
- Les bases indépendantes de comptages SIRENE ou d’affectation administrative ne deviennent pas automatiquement ODbL parce qu’elles accompagnent une carte (§ 4.5). Conserver leurs licences et provenances propres. Une table enrichie de dérivés géométriques doit expliciter la portée ODbL ; séparer les composantes facilite cette distinction.

Notice proposée pour les figures métropolitaines, avec liens vers la base et la licence :

> Fond de carte : data.gouv.fr, Contours administratifs, communes 2024, généralisation 5 m (source IGN Admin Express), ODbL 1.0. Traitements et visualisation : auteur du projet.

Le générateur de `data_sources.csv` a été corrigé pour cette source : `ODbL1.0; attribution; derived geographic databases share alike`, avec l’URL du texte de la licence. Le contrôle conserve 57 lignes ; seuls les deux champs autorisés de cette ligne ont changé. Voir `reports/review_C_source_license_correction.json`.

## Droits sur les productions originales et options HAL

La licence du PDF concerne les contributions originales dont l’auteur détient les droits ; elle ne remplace pas les conditions des bases tierces. Les tableaux et cartes sont produits par les programmes du projet, avec attribution des données d’origine. Ce constat n’affirme pas un droit d’auteur exclusif sur tout contenu produit avec une IA. Le code original reçoit une licence de logiciel déclarée dans le paquet ; les dépendances conservent leurs propres licences et ne sont pas automatiquement redistribuées.

La [documentation publique HAL consultée aujourd’hui](https://doc.hal.science/aspects-juridiques/conditions-de-reutilisation/) indique qu’à partir de février 2026 les fichiers déposés doivent avoir une condition de réutilisation. Elle propose les six licences Creative Commons, la Licence Ouverte Etalab et Copyright ; CC BY est recommandée par le CCSD. Cette recommandation n’établit pas une obligation générale de choisir CC BY. Le code logiciel relève de licences dédiées. **CC BY 4.0 pour le PDF original**, en conservant les mentions des sources et les exceptions de droits tiers, est cohérente avec l’option envisagée ; aucun choix n’a été enregistré dans un formulaire HAL durant cette revue.

## Limites consignées et contrôle du paquet final

La [CNIL](https://www.cnil.fr/fr/technologies/lanonymisation-de-donnees-personnelles) distingue les risques d’individualisation, de corrélation et d’inférence. L’absence d’identifiants individuels réduit l’exposition mais ne prouve pas, à elle seule, l’anonymat. Les petits comptages géographiques peuvent permettre des inférences avec des sources extérieures. Aucun test exhaustif de réidentification ni seuil réglementaire de cellule minimale n’a été établi par cette revue ; aucun seuil n’est inventé.

Avant distribution, le manifeste effectif doit correspondre au périmètre décrit, les figures doivent porter leurs notices, et l’alternative de reconstruction ODbL doit comprendre toutes les modifications et tous les contenus nécessaires. Ces points sont des vérifications matérielles du paquet, et non une nouvelle procédure d’autorisation humaine créée par cette revue.

L’accès au produit IGN actuel a retourné une page dynamique dont la licence n’était pas lisible dans la réponse reçue. Cela n’affaiblit pas la licence explicite du jeu **Contours administratifs réellement utilisé**. Une tentative d’accès aux CGU de l’API Légifrance a retourné HTTP 403 ; ces conditions non lues ne sont pas extrapolées aux copies du site. Cette revue n’accorde donc pas une licence générale aux archives intégrales de textes, aux publications bibliographiques ou à tout fichier brut hors du manifeste envisagé.

Les preuves officielles consultées, les URL finales, les horodatages réels UTC et locaux, les tailles et les SHA256 sont consignés dans `docs/sources/public_release_rights/official_access_log.json` et dans `reports/review_C_public_release_rights.json`. La date locale est le 4 octobre 2026 même lorsque l’horodatage UTC correspond encore au 3 octobre. Aucun horodatage manquant n’a été remplacé par une date supposée.
