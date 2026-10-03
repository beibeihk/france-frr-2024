"""Append verified institutional claims, preserving existing audit rows."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "claims_audit.csv"
FIELDS = ["claim", "paper_location", "source_url", "source_type", "verified", "notes"]
L24 = "https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000048727426?isSuggest=true"
FRR = "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820"
OLD = "https://static.data.gouv.fr/resources/zones-de-revitalisation-rurale-zrr/20210907-124104/diffusion-zonages-zrr-cog2021.xls"
L25 = "https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000051168986"
A25 = "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051469445"
TAB25 = "https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/Liste%20communes%20FRR_juillet2025.xlsx"
FAQ = "https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/FAQ%20FRR_MAJ%20juillet2025.pdf"
SOC = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048846858/2025-02-28"


def main():
    rows = []
    def add(claim, section, url, kind, notes):
        rows.append(dict(zip(FIELDS, [claim, "working_location: " + section, url, kind,
                                     "true", "Institutional audit 2026-10-03; " + notes])))
    add("Le plan général France Ruralités est annoncé le 15 juin 2023.", "§2 calendrier",
        "https://www.ecologie.gouv.fr/presse/france-ruralites-plan-ambitieux-davantage-dequite-territoriale",
        "official_contemporaneous_announcement", "General plan announcement; not publication of commune assignment. Raw announcement_and_legislative_timing_verified_web.txt.")
    add("La loi de finances pour 2024 est définitivement adoptée le 21 décembre 2023.", "§2 calendrier",
        "https://www.assemblee-nationale.fr/dyn/actualites-accueil-hub/projet-de-loi-de-finances-pour-2024-lecture-definitive-adoption-du-projet-de-loi-apres-le-rejet-d-une-motion-de-censure",
        "official_legislative_procedure", "Assembly article49.3 final-adoption chronology opened and verified; distinguish promulgation.")
    add("La loi de finances pour 2024 est promulguée le 29 décembre et publiée le 30 décembre 2023.", "§2 calendrier",
        "https://www.senat.fr/dossier-legislatif/pjlf2024.html", "official_legislative_procedure",
        "Legislative dossier specifies law2023-1322 and JO303/2023-12-30; opened and verified.")
    add("La première liste FRR est publiée le 20 juin 2024 et prend effet le 1er juillet 2024.", "§2.2 classement initial",
        FRR, "official_law_original", "Arrêté19June2024 NOR TREB2414964A; JORF20June2024 texte51; article2. 34 raw official web snapshots.")
    add("L'annexe initiale FRR utilise le COG au 1er janvier 2023.", "§2.2 classement initial",
        FRR, "official_law_original", "Annex introductory line146; not COG2024 or the current administrative geography.")
    add("La liste initiale FRR contient 17 717 codes communaux distincts.", "§2.2 classement initial",
        FRR, "official_law_original_independent_extraction", "Exact official-code extraction; frr_2024_codes_verified.csv SHAaf57dd2bcf24fb4d70aeecbac1f0a8c363288f4843338b8b9c8a00f72dfe87c9; independent gazette-copy equality; copy never supplies codes.")
    add("Vingt communes de La Réunion sont partiellement zonées dans la liste initiale FRR.", "§2.2 classement initial",
        FRR, "official_law_original_independent_extraction", "20 [P] flags in original Annex, line340; partially_zoned field; not20 whole communes eligible.")
    add("La voie EPCI de droit commun exige une population communale inférieure à 30 000 habitants.", "§2.3 critères",
        L24, "official_law_original", "New CGI44quindeciesA II-A; other criteria and alternative routes also apply; cannot define assignment with population alone.")
    add("La voie EPCI de droit commun impose des seuils nationaux médians de densité et de revenu disponible médian.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA II-A 1°/2°; medians over metropolitan EPCI; no unverified numerical cutoff quoted.")
    add("Une voie départementale prévoit une densité inférieure à 35 habitants par km² et une condition de revenu.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA II-C; density is strictly below35; commune population<30000 and department income condition remain.")
    add("La voie montagne comporte au moins 50 % de population en montagne et un plafond de revenu au 75e centile.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA II-D; also EPCI density<=nationalmedian and commune population<30000.")
    add("Le droit initial permet un classement complémentaire proposé à l'échelle du bassin de vie.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA II-B; regional prefect proposal/public-interest condition; basin density and income criteria. Actual per-commune path not reconstructed.")
    add("Le droit initial prévoit une révision du classement tous les six ans.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA IV; later2025 extensions distinguished from scheduledrevision.")
    add("L'assignation initiale utilise les données disponibles au 1er juillet 2023 et le périmètre EPCI du 1er janvier 2023.", "§2.3 critères",
        L24, "official_law_original", "CGI44quindeciesA IV; dates are availability/perimeter cutoffs, not all variables' observation years.")
    add("L'ancien classement ZRR pertinent repose sur l'arrêté de mars 2017 modifié en février 2018.", "§2.1 ancien ZRR",
        "https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034298773/2018-04-01", "official_law_historical",
        "Historical Annex; original COG2017; ANCT conversionCOG2021 preserved separately. Not the July2024 replacementAnnex.")
    add("Les effets conservés du classement ZRR pour les communes sortantes en 2017 sont prorogés au 30 juin 2024.", "§2.1 ancien ZRR",
        L24, "official_law_original", "Article73 XVI/XVII amend mountain law2016 article7 and LFI2018 article27; both categories included.")
    add("La DGFiP confirme que les listes ZRR révisées en 2018 couvrent la période du 1er juillet 2017 au 30 juin 2024.", "Annexe audit ZRR",
        "https://bofip.impots.gouv.fr/bofip/4219-PGP.html/identifiant=BOI-IF-CFE-10-30-40-40-20260708",
        "official_retrospective_tax_commentary", "§30 explicitly describes classification+retainedeffects for fullperiod; used as corroboration, not original2024assignment source.")
    add("Le fichier ANCT en COG 2021 contient 17 694 communes entièrement bénéficiaires et 36 partiellement bénéficiaires.", "Annexe audit ZRR",
        OLD, "official_open_data_independent_count", "ZRR_SIMP C-/P- counts, all categories including retainedeffects; legalcontinuity requires stable geography. Scriptbuild_legal_audit_manifest.py.")
    add("L'arrêté ZRR du 19 juin 2024 remplace les annexes à compter du 1er juillet 2024.", "§2.1 transition",
        "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746830", "official_law_original",
        "Articles1/2; replacement Annex must not be used as complete pre-July2024ZRR list.")
    add("L'exonération de bénéfices FRR socle concerne les entreprises créées ou reprises du 1er juillet 2024 au 31 décembre 2029.", "§2.4 avantages",
        L24, "official_law_original", "CGI44quindeciesA I-B; industrial/commercial/artisanal/professionalnoncommercial activity; not all SIRENE registrations eligible.")
    add("L'exonération de bénéfices FRR socle requiert un régime réel et moins de onze salariés.", "§2.4 avantages",
        L24, "official_law_original", "CGI44quindeciesA I-B and V-B1°; also location/activity restrictions; taxregime not observedinSIRENE.")
    add("L'exonération de bénéfices s'étend au terme du 59e mois suivant le mois de création ou de reprise.", "§2.4 avantages",
        L24, "official_law_original", "CGI44quindeciesA I-B; commonlydescribedasfiveyears; literal statutoryduration retained.")
    add("Les trois périodes de douze mois suivantes ouvrent des exonérations de bénéfices de 75 %, 50 % puis 25 %.", "§2.4 avantages",
        L24, "official_law_original", "CGI44quindeciesA I-E; statute taxablefractions1/4,1/2,3/4, convertedintoexemptfractions.")
    add("Le régime initial comporte une tolérance de 25 % de chiffre d'affaires hors zone pour l'activité sédentaire.", "§2.4 avantages",
        L24, "official_law_original", "CGI44quindeciesA V-B2°; out-of-zoneprofitportion taxable; VI separately governs nonsedentaryactivity. Do not reverseapply2026oldZRRchange.")
    add("Les exonérations CFE et TFPB prévues par les articles 1466 G et 1383 K requièrent une délibération locale.", "§2.4 avantages",
        L24, "official_law_original", "Affirmative commune/EPCI deliberation for its taxshare; designationalone is not take-up or localadoption.")
    add("La CFE des créations éligibles bénéficie de cinq ans d'exonération puis de trois abattements de 75 %, 50 % et 25 %.", "§2.4 avantages",
        L24, "official_law_original", "CGI1466G I; beginsyearfollowingcreation; claim restricted to eligiblecreatedestablishments, not undocumentedextensioninterpretation.")
    add("La TFPB est liée à un établissement éligible à la CFE et suit les mêmes proportions et durée.", "§2.4 avantages",
        L24, "official_law_original", "CGI1383K I/II; propertyattachmentandownlocaldeliberation/declarationrequired; beginsJan1followingattachment.")
    add("La fenêtre spéciale de délibération de 2024 se termine le 18 septembre inclus pour l'application dès 2025.", "§2.4 avantages",
        FAQ, "official_ministry_FAQ_historical_explanation", "FAQJuly2025 p16 confirms90days afteroriginalarrêtépublication; legalbasisLFI2024article73XX-F. Notgeneric30Septemberdeadline.")
    add("La règle sociale initiale interdit que l'embauche porte l'effectif total à au moins cinquante salariés.", "§2.4 avantages",
        SOC, "official_law_historical", "CSS L241-19 II, versioninforce2024-07-01to2026-01-01; accuratelegalthresholdoverridesadministrativeshorthandfirst50employee.")
    add("L'exonération sociale dure douze mois, avec un taux plein jusqu'à 1,5 SMIC et nul à partir de 2,4 SMIC.", "§2.4 avantages",
        SOC, "official_law_historical", "CSS L241-19 I/III; employerassurancessociales/familyallowances, notallsocialcharges; no2026eurosbackdated.")
    add("La règle sociale initiale exige l'absence de licenciement économique au cours des douze mois précédents.", "§2.4 avantages",
        SOC, "official_law_historical", "CSS L241-19 II; employerconditionnotobservedincreationcounts.")
    add("La règle sociale initiale prévoit un CDI ou un CDD éligible d'au moins douze mois et une déclaration sous trente jours.", "§2.4 avantages",
        SOC, "official_law_historical", "CSS L241-19 III/IV; CDDtemporaryincreaseinactivity; latereportingreducesexemptionperiod;2026currentproceduresdifferent.")
    add("La loi de finances pour 2025 accorde les effets FRR aux anciens bénéficiaires ZRR non reclassés, rétroactivement au 1er juillet 2024.", "§2.5 mises à jour",
        L25, "official_law_original", "Article99 IV and VII-A; includesoldretainedeffects; initial2027deadlineextendedlater; publication/informationtimingdistinct.")
    add("L'annexe I de l'arrêté du 14 avril 2025 comporte 117 codes supplémentaires.", "§2.5 mises à jour",
        A25, "official_law_original_independent_extraction", "OfficialAnnexI codecount verified; allabsentfrominitial17717; COG2023exceptexplicitIngrandesexception. Effective dates varybylawclause.")
    add("Le tableau DGCL de juillet 2025 contient 17 789 codes classés FRR, dont vingt partiels, et 2 145 bénéficiaires, dont onze partiels.", "Annexe versions du zonage",
        TAB25, "official_open_data_independent_count", "Exact tableclassificationcounts; currentgeography, notlegalCOG2023count. Core13313socle+4456plus+20part; beneficiary2134+11part.")
    add("Le tableau DGCL de juillet 2025 contient 4 456 codes FRR+.", "§2.5 mises à jour",
        TAB25, "official_open_data_independent_count", "CountforDGCLJuly2025geography; neverequatewithotherCOGvintagewithoutcrosswalk.")
    add("Le décret et l'arrêté FRR+ sont publiés le 10 juillet 2025, avec effet juridique au 1er janvier 2025.", "§2.5 mises à jour",
        "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051871894 | https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051871914",
        "official_law_original", "Décret2025-628 article4 andclassificationarrêtéarticle2; publicationversusretrospectiveeffectdistinguished.")
    add("L'indice FRR+ combine les évolutions de revenu fiscal moyen, population et emploi des 25–54 ans entre 2009 et 2020.", "§2.5 mises à jour",
        "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051871894", "official_law_original",
        "Décret2025-628 articles1/2+Annex; productofgrowthratios; lowerofEPCI/bassinindex; ruralcommunesonly.")
    add("La loi de finances pour 2026 prolonge jusqu'en 2029 les effets FRR des communes bénéficiaires.", "§2.5 mises à jour",
        "https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000053508415", "official_law_original",
        "Article48 changes2027to2029 inLFI2025article99IV; doesnotconferFRR+status orchangeinitial2024announcedlist.")
    add("La sélection FRR combine des voies EPCI, départementales, montagne et bassin de vie.", "§4 limites d'identification",
        L24, "official_law_original", "CGI44quindeciesA II-AtoE; routesareverifiedinlaw,butindividualassignmentpathisnotreconstructed; noRDDpermitted.")
    add("L'article 73 rattache aussi des dispositions de dotations locales et de service postal au classement FRR.", "§2.4 ensemble des mesures",
        L24, "official_law_original", "Article 73 III modifies CGCT L.2334-21; XII modifies the postal-service law. A territorial designation can activate several channels; no claim about actual receipt or local spending is made.")
    # These counts are sample-construction facts, not policy-decree counts or effects.
    from json import loads
    audit = loads((ROOT / "reports/review_A_final_coding_border_audit.json").read_text(encoding="utf-8"))
    add(f"L'échantillon stable comporte {audit['new_stable']} communes NEW_FRR et {audit['never_stable']} NEVER_TREATED.", "§3 construction de l'échantillon",
        FRR + " | " + OLD, "reproducible_sample_count_from_official_inputs",
        "Independenttreatmentcheck+transitionmatrix; countsderivedaftergeographyandEPCIrestrictions, notoriginalAnnexcounts; review_A_final_coding_border_audit.json containsfilehashes.")
    add(f"La sélection de frontière contient {audit['pairs']} paires et {audit['distinct_communes_selected']} communes distinctes.", "§3 échantillon de frontière",
        "https://object.data.gouv.fr/contours-administratifs/2024/geojson/communes-5m.geojson.gz",
        "reproducible_sample_count_from_official_inputs", "Everyselectedpairindependentlyrecheckedagainstoriginalpolygons; nocommunerepeated; edgesareselectionartifactsnotrandomassignment.")
    existing = []
    if DEST.exists():
        with DEST.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != FIELDS:
                raise RuntimeError("Existing claims_audit.csv schema differs; refuse to overwrite")
            existing = list(reader)
    known = {(row["claim"], row["source_url"]) for row in existing}
    additions = [row for row in rows if (row["claim"], row["source_url"]) not in known]
    # Atomic replacement preserves every existing row and appends only new claims.
    temporary = DEST.with_suffix(".csv.institutional.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing + additions)
    temporary.replace(DEST)
    print(f"Preserved {len(existing)} existing rows; appended {len(additions)} institutional claims; {DEST}")


if __name__ == "__main__":
    main()
