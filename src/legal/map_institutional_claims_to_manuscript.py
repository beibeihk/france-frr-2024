"""Locate institutional source claims in the manuscript without editing TeX.

Coverage is recorded separately from factual verification: an audited fact that
is absent from the manuscript must not be presented as a manuscript statement.
Existing non-institutional claim rows are preserved.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ["claim", "paper_location", "source_url", "source_type", "verified", "notes"]
# Unique prefix, semantic locator, matching paragraph opener, coverage, revision.
MAP = [
    ("Le plan général France Ruralités", "main §3.1, paragraph 1", "Le plan France Ruralités", "explicit", ""),
    ("La loi de finances pour 2024 est définitivement", "not asserted; related main §3.1, paragraph 1 and §3.3, paragraph 3", "Le plan France Ruralités", "source_audit_only", ""),
    ("La loi de finances pour 2024 est promulguée", "not asserted; related main §3.1, paragraph 1 and §3.3, paragraph 3", "Le plan France Ruralités", "source_audit_only", ""),
    ("La première liste FRR", "main §3.1, paragraph 1", "Le plan France Ruralités", "explicit", ""),
    ("L'annexe initiale FRR", "main §3.1, paragraph 1", "Le plan France Ruralités", "summarized_as_COG2023", ""),
    ("La liste initiale FRR", "main §3.1, paragraph 1; table 1 note; appendix §1, paragraph 3", "Le plan France Ruralités", "explicit", "R08"),
    ("Vingt communes de La Réunion", "main §3.1, paragraph 1", "Le plan France Ruralités", "explicit", "R08"),
    ("La voie EPCI de droit commun exige", "main §3.1, paragraph 2", "Le canal de droit commun", "explicit", ""),
    ("La voie EPCI de droit commun impose", "main §3.1, paragraph 2", "Le canal de droit commun", "paraphrased", "R06"),
    ("Une voie départementale", "not asserted; route mentioned in main §3.1, paragraph 2", "Le canal de droit commun", "source_audit_only", ""),
    ("La voie montagne", "not asserted; route mentioned in main §3.1, paragraph 2", "Le canal de droit commun", "source_audit_only", ""),
    ("Le droit initial permet un classement complémentaire", "main §3.1, paragraph 2; regional proposal detail not asserted", "Le canal de droit commun", "summarized_route_only", ""),
    ("Le droit initial prévoit une révision", "not asserted; related main §3.1, paragraph 2", "Le canal de droit commun", "source_audit_only", ""),
    ("L'assignation initiale utilise", "main §3.1, paragraph 2; exact reference dates not asserted", "Le canal de droit commun", "partial_ambiguous_dates", "R06"),
    ("L'ancien classement ZRR", "main §3.3, paragraph 1", "La référence avant réforme", "paraphrased_years_only", "R05"),
    ("Les effets conservés du classement ZRR", "main §3.3, paragraph 1", "La référence avant réforme", "partial_scope_ambiguous", "R05"),
    ("La DGFiP confirme", "not asserted; source corroboration in review_A_institutional.md §2; related main §3.3, paragraph 1", "La référence avant réforme", "source_audit_only", ""),
    ("Le fichier ANCT en COG 2021 contient", "not asserted; related main §3.3, paragraph 1 and appendix §1, paragraph 3", "La référence avant réforme", "source_audit_only", "R08"),
    ("L'arrêté ZRR du 19 juin", "main §3.3, paragraph 1", "La référence avant réforme", "explicit", ""),
    ("L'exonération de bénéfices FRR socle concerne", "main §3.2, paragraph 1; eligibility window initially omitted", "Dans FRR socle", "partial_eligibility_window_omitted", "R01"),
    ("L'exonération de bénéfices FRR socle requiert", "main §3.2, paragraph 1", "Dans FRR socle", "explicit", ""),
    ("L'exonération de bénéfices s'étend", "main §3.2, paragraph 1", "Dans FRR socle", "explicit", ""),
    ("Les trois périodes de douze mois", "main §3.2, paragraph 1", "Dans FRR socle", "explicit", ""),
    ("Le régime initial comporte une tolérance", "not asserted; related main §3.2, paragraph 1", "Dans FRR socle", "source_audit_only", ""),
    ("Les exonérations CFE et TFPB", "main §3.2, paragraph 2", "La CFE et la taxe foncière", "explicit", "R02"),
    ("La CFE des créations éligibles", "main §3.2, paragraph 2; taper percentages not asserted", "La CFE et la taxe foncière", "partial_duration_only", "R02"),
    ("La TFPB est liée", "main §3.2, paragraph 2; property attachment link and tax-year rule not asserted", "La CFE et la taxe foncière", "partial_link_omitted", "R02"),
    ("La fenêtre spéciale de délibération", "main §3.2, paragraph 2", "La CFE et la taxe foncière", "explicit", "R02"),
    ("La règle sociale initiale interdit", "main §3.2, paragraph 3", "Le régime de cotisations patronales", "explicit", "R03"),
    ("L'exonération sociale dure", "main §3.2, paragraph 3", "Le régime de cotisations patronales", "explicit", "R03"),
    ("La règle sociale initiale exige", "main §3.2, paragraph 3; dismissal condition mentioned without type or twelve-month period", "Le régime de cotisations patronales", "partial_conditions_summarized", "R03"),
    ("La règle sociale initiale prévoit", "main §3.2, paragraph 3; contract and declaration details not asserted", "Le régime de cotisations patronales", "partial_conditions_summarized", "R03"),
    ("La loi de finances pour 2025 accorde", "main §3.3, paragraph 2", "La loi de finances pour 2025", "partial_retroactive_clause_summarized", "R07"),
    ("L'annexe I de l'arrêté du 14 avril", "not asserted; related main §3.3, paragraph 2", "La loi de finances pour 2025", "source_audit_only", "R08"),
    ("Le tableau DGCL de juillet 2025 contient 17", "not asserted; related main §3.3, paragraph 2 and table 1", "La loi de finances pour 2025", "source_audit_only", "R08"),
    ("Le tableau DGCL de juillet 2025 contient 4", "not asserted; related main §3.3, paragraph 2", "La loi de finances pour 2025", "source_audit_only", "R08"),
    ("Le décret et l'arrêté FRR+", "main §3.3, paragraph 2", "La loi de finances pour 2025", "explicit", ""),
    ("L'indice FRR+", "not asserted; related main §3.3, paragraph 2", "La loi de finances pour 2025", "source_audit_only", ""),
    ("La loi de finances pour 2026 prolonge", "main §3.3, paragraph 2", "La loi de finances pour 2025", "explicit", ""),
    ("La sélection FRR combine", "main §3.1, paragraph 2 and §5.4, paragraph 1", "Le canal de droit commun", "explicit", ""),
    ("L'article 73 rattache", "main §3.2, paragraph 4; precise non-tax provisions not asserted", "Le traitement empirique", "partial_non_tax_bundle_summarized", "R04"),
    ("L'échantillon stable comporte", "main §3.3, table 1, stable-column rows 1 and 4; broad control count in §5.1 differs by population filter", "\\begin{table}[htbp]\\centering\\small\\caption{Transitions", "explicit_generated_table", "R09"),
    ("La sélection de frontière contient", "main §5.1, paragraph 2; appendix §6, paragraph 1; distinct commune count implied by two unique endpoints", "Les voisins adjacents", "explicit_pairs_commune_count_inferable", ""),
]


def main():
    paths = [ROOT / "paper/main_fr.tex", ROOT / "paper/appendix_fr.tex"]
    main_lines = paths[0].read_text(encoding="utf-8").splitlines()
    dest = ROOT / "claims_audit.csv"
    with dest.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == FIELDS
        rows = list(reader)
    mapping = []
    for number, (prefix, location, opener, coverage, revision) in enumerate(MAP, 1):
        found = [row for row in rows if row["claim"].startswith(prefix)]
        assert len(found) == 1, (prefix, len(found))
        row = found[0]
        line_numbers = [n for n, line in enumerate(main_lines, 1) if line.startswith(opener)]
        if not line_numbers:
            alternatives = {
                "Dans FRR socle": ("FRR socle", "exonération nationale d’impôt"),
                "La CFE et la taxe foncière": ("foncière", "délibérations locales"),
                "Le régime de cotisations patronales": ("régime", "cotisations patronales"),
                "La référence avant réforme": ("situation territoriale avant réforme", "maintien"),
            }
            if opener in alternatives:
                fragments = alternatives[opener]
                line_numbers = [n for n, line in enumerate(main_lines, 1)
                                if all(fragment in line for fragment in fragments)]
        assert len(line_numbers) == 1, (opener, line_numbers)
        lineno = line_numbers[0]
        paragraph = main_lines[lineno - 1].split("\\footnote", 1)[0]
        if number == 20 and re.search(r"31\s+décembre\s+2029", paragraph):
            coverage = "explicit"
            location = "main §3.2, paragraph 1"
        if number == 14 and "1er juillet 2023" in paragraph and "1er janvier 2023" in paragraph:
            coverage = "explicit"
            location = "main §3.1, paragraph 2"
        if number == 16 and "maintien" in paragraph and "sorties" in paragraph and "2017" in paragraph:
            coverage = "explicit"
            location = "main §3.3, paragraph 1"
        if number == 15 and "16 mars 2017" in paragraph and "22 février 2018" in paragraph:
            coverage = "explicit"
            location = "main §3.3, paragraph 1"
        if number == 26 and all(value in paragraph for value in ["75", "50", "25"]):
            coverage = "explicit"
            location = "main §3.2, paragraph 2"
        if number == 27 and "rattach" in paragraph and "1er janvier" in paragraph:
            location = "main §3.2, paragraph 2; property tax-year rule stated; CFE eligibility link not explicit"
            if "établissement" in paragraph and "conditions" in paragraph:
                coverage = "explicit"
                location = "main §3.2, paragraph 2"
        if number == 31 and "licenciement économique" in paragraph and "douze mois" in paragraph:
            coverage = "explicit"
            location = "main §3.2, paragraph 3"
        if number == 32 and all(value in paragraph for value in ["CDI", "CDD", "douze", "trente"]):
            coverage = "explicit"
            location = "main §3.2, paragraph 3"
        if number == 33 and "VII-A" in paragraph and "maintien" in paragraph:
            coverage = "explicit"
            location = "main §3.3, paragraph 2"
        if number == 41 and "dotations" in paragraph and "postal" in paragraph:
            coverage = "explicit"
            location = "main §3.2, paragraph 4"
        row["paper_location"] = f"{location} [paper/main_fr.tex:{lineno}]"
        # Preserve original evidence notes and replace only our coverage suffix.
        row["notes"] = row["notes"].split(" | Manuscript mapping ")[0] + (
            f" | Manuscript mapping 2026-10-03: {coverage}; "
            f"fact verification is distinct from manuscript coverage; revision={revision or 'none'}.")
        mapping.append({"claim_id": f"A{number:02d}", "claim": row["claim"],
            "paper_location": row["paper_location"], "manuscript_coverage": coverage,
            "revision_id": revision})
    temporary = dest.with_suffix(".csv.location.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(dest)
    with (ROOT / "reports/review_A_claim_mapping.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapping[0]))
        writer.writeheader()
        writer.writerows(mapping)
    totals = {}
    for row in mapping:
        totals[row["manuscript_coverage"]] = totals.get(row["manuscript_coverage"], 0) + 1
    scope = {"audit_date": "2026-10-03", "claims_located": len(mapping),
        "original_csv_rows_preserved": len(rows), "manuscript_coverage_counts": totals,
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in paths},
        "restriction": "Verified source facts absent from the manuscript remain source_audit_only; no TeX was edited."}
    (ROOT / "reports/review_A_manuscript_scope.json").write_text(
        json.dumps(scope, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(scope, ensure_ascii=False))


if __name__ == "__main__":
    main()
