"""Verify the requested editorial corrections in the saved sources only."""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    files = [ROOT / name for name in ["paper/main_fr.tex", "paper/appendix_fr.tex",
        "paper/generated/facts.tex", "claims_audit.csv",
        "reports/review_A_claim_mapping.csv", "reports/review_A_institutional_macro_values.json"]]
    main_text, app_text, facts_text = [path.read_text(encoding="utf-8") for path in files[:3]]
    lines = main_text.splitlines()
    def paragraph(prefix):
        found = [(i, line.split("\\footnote", 1)[0]) for i, line in enumerate(lines, 1)
                 if line.startswith(prefix)]
        assert len(found) == 1, (prefix, found)
        return found[0]
    p1 = paragraph("Dans le dispositif FRR socle")
    p2 = paragraph("La cotisation foncière des entreprises")
    p3 = paragraph("Le régime national exonère")
    p5 = paragraph("La situation territoriale avant réforme")
    p6 = paragraph("Le canal de droit commun")
    p7 = paragraph("La loi de finances pour 2025 ajoute")
    p9 = next((i, line) for i, line in enumerate(lines, 1) if "\\label{tab:transitions}" in line)
    abstract = main_text.split("\\begin{abstract}", 1)[1].split("\\end{abstract}", 1)[0]
    requirements = {
        "R01": (p1, ["1er juillet 2024", "31 décembre 2029", "régime réel", "moins de onze", "cinquante-neuvième", "75, 50 et 25"]),
        "R02": (p2, ["délibérations locales distinctes", "part de chaque collectivité", "établissement créé", "exonération de bénéfices", "cinq années", "année suivant la création", "75, 50 et 25", "immeuble rattaché", "conditions de la CFE", "l’exonération suit", "1er janvier suivant le rattachement", "demandes et déclarations", "18 septembre inclus", "impositions de 2025", "sous réserve des autres conditions"]),
        "R03": (p3, ["cotisations patronales d’assurances sociales et d’allocations familiales", "douze mois", "effectif total de l’entreprise", "au moins cinquante", "1,5 SMIC", "2,4 SMIC", "licenciement économique", "CDI", "CDD admissible d’au moins douze mois", "déclaration historique", "trente jours"]),
        "R05": (p5, ["16 mars 2017", "22 février 2018", "communes sorties", "2017", "XVI et XVII", "dispositifs de maintien", "30 juin 2024", "COG 2021", "1er juillet"]),
        "R06": (p6, ["données disponibles au 1er juillet 2023", "périmètre des EPCI arrêté au 1er janvier 2023", "ne signifient pas que toutes les variables économiques sont observées en 2023"]),
        "R07": (p7, ["auparavant classées en ZRR ou bénéficiant de ses effets", "article 99, IV", "rétroactivement au 1er juillet 2024", "VII-A", "propres clauses d’entrée en vigueur", "14 avril 2025", "décret de mise en œuvre", "arrêté de classement FRR+", "10 juillet 2025", "1er janvier 2025", "jusqu’en 2029", "sans leur conférer le statut FRR+", "jamais utilisées comme témoins"]),
        "R09": (p9, ["\\StableLaterCoreExcludedN{}", "aucun statut partiel", "aucune des trois comparaisons"]),
        "R10": ((10, abstract), ["communes nouvellement classées dans la liste initiale FRR"]),
    }
    checks = {}
    for key, ((number, text), phrases) in requirements.items():
        missing = [phrase for phrase in phrases if phrase not in text]
        assert not missing, (key, missing)
        checks[key] = {"passed": True, "main_tex_line": number, "scope": "Saved source wording reviewed against previously verified law; no new legal facts."}
    assert "La CFE commence" not in p2[1] and "la TFPB commence" not in p2[1]
    assert "communes nouvellement bénéficiaires" not in abstract
    # Verify actual macro expansions, rather than only the presence of macro names.
    definitions = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^{}]*)\}", facts_text))
    values = json.loads(files[-1].read_text(encoding="utf-8"))["institutional_macro_values"]
    for key, value in values.items():
        assert key in definitions, key
        assert int(definitions[key].replace(r"\,", "").replace(" ", "")) == value, key
    used = sorted(key for key in values if "\\" + key + "{}" in main_text + app_text)
    assert "\\FRRInitialN{}" in main_text and "\\FRRInitialN{}" in app_text
    assert "\\FRRInitialPartialN{}" in main_text
    assert "\\EPCIComponentsN{}" in main_text and "\\EDBComponentsN{}" in main_text
    assert "\\EDBMaxPairsN{}" in app_text and "\\BorderPairs{}" in app_text
    treatment = pd.read_csv(ROOT / "data/processed/commune_treatment.csv", dtype=str)
    stable = treatment[treatment.analysis_stable.eq("True") & treatment.metropolitan.eq("True")]
    excluded = stable[stable.treatment_group.eq("EXCLUDE_UNRESOLVED_OR_PARTIAL")]
    assert stable.partial.eq("False").all() and len(excluded) == values["StableLaterCoreExcludedN"]
    assert excluded.frr_2024.eq("False").all()
    assert excluded.status_2025.isin(["FRR socle", "FRR+"]).all()
    claims = pd.read_csv(ROOT / "claims_audit.csv", dtype=str)
    mapping = pd.read_csv(ROOT / "reports/review_A_claim_mapping.csv", dtype=str)
    institutional = claims[claims.claim.isin(mapping.claim)]
    assert len(institutional) == 43 and len(mapping) == 43 and institutional.claim.is_unique
    assert not institutional.paper_location.str.startswith("working_location: ").any()
    result = {"audit_date": "2026-10-03", "status": "requested_institutional_corrections_verified",
        "corrections": checks, "institutional_macro_definitions_verified": len(values),
        "institutional_macros_used_in_sources": used,
        "macro_presence_is_not_a_manuscript_claim": True,
        "claim_rows_refreshed": len(institutional), "other_claim_rows_preserved": len(claims) - len(institutional),
        "coverage_counts": mapping.manuscript_coverage.value_counts().to_dict(),
        "stable_excluded_later_core_count": len(excluded), "stable_partial_count": 0,
        "sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "limits": "No TeX edited; no new institutional facts; no coefficient, causal-design, human review or HAL clearance."}
    dest = ROOT / "reports/review_A_final_corrections.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"corrections_passed": len(checks), "macro_definitions_passed": len(values),
        "claims_refreshed": len(institutional), "coverage_counts": result["coverage_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
