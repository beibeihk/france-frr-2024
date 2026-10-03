"""Supply auditable institutional counts for the manuscript macro generator."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    initial_path = ROOT / "data/processed/frr_2024_codes_verified.csv"
    old_path = ROOT / "data/raw/zrr_2021.xls"
    current_path = ROOT / "data/raw/frr_2025.xlsx"
    audit_path = ROOT / "reports/review_A_final_coding_border_audit.json"
    manifest_path = ROOT / "reports/legal_source_audit_manifest.json"
    treatment_path = ROOT / "data/processed/commune_treatment.csv"
    initial = pd.read_csv(initial_path, dtype=str)
    old = pd.read_excel(old_path, sheet_name="Classement ZRR (COG 2021)", header=None,
                        dtype=str).iloc[6:]
    old = old[old.iloc[:, 0].str.fullmatch(r"[0-9AB]{5}", na=False)]
    current = pd.read_excel(current_path, dtype=str)
    counts = current.iloc[:, 3].value_counts()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    legal = json.loads(manifest_path.read_text(encoding="utf-8"))
    treatment = pd.read_csv(treatment_path, dtype=str)
    stable = treatment[treatment.analysis_stable.eq("True") & treatment.metropolitan.eq("True")]
    excluded = stable[stable.treatment_group.eq("EXCLUDE_UNRESOLVED_OR_PARTIAL")]
    assert stable.partial.eq("False").all()
    assert len(excluded) == 116 and excluded.frr_2024.eq("False").all()
    assert excluded.status_2025.isin(["FRR socle", "FRR+"]).all()
    values = {
        "FRRInitialN": initial.code_insee.nunique(),
        "FRRInitialPartialN": int(initial.partially_zoned.eq("1").sum()),
        "OldZRRFullN": int(old.iloc[:, 2].str.startswith("C -", na=False).sum()),
        "OldZRRPartialN": int(old.iloc[:, 2].str.startswith("P -", na=False).sum()),
        "FRRAdditionsAprN": legal["current_frr2025"]["april_annex1_new_codes"],
        "FRRCoreJulyN": int(counts[["FRR socle", "FRR+", "Classée FRR partiellement"]].sum()),
        "FRRCorePartialJulyN": int(counts["Classée FRR partiellement"]),
        "FRRBenefJulyN": int(counts[["FRR bénéficiaire", "FRR bénéficiaire partiellement"]].sum()),
        "FRRBenefPartialJulyN": int(counts["FRR bénéficiaire partiellement"]),
        "FRRPlusJulyN": int(counts["FRR+"]),
        "StableNeverN": audit["never_stable"],
        "StableLaterCoreExcludedN": len(excluded),
        "BorderCommuneN": audit["distinct_communes_selected"],
        "EPCIComponentsN": audit["dependency_components"]["EPCI"]["components"],
        "EDComponentsN": audit["dependency_components"]["EPCI_department"]["components"],
        "EDBComponentsN": audit["dependency_components"]["EPCI_department_bassin"]["components"],
        "EDBMaxPairsN": audit["dependency_components"]["EPCI_department_bassin"]["maximum_pairs"],
    }
    result = {"audit_date": "2026-10-03", "institutional_macro_values": values,
        "geography": {"FRRInitial": "Original Annex COG2023", "OldZRR": "ANCT COG2021, all retained effects",
            "FRRJuly": "DGCL July2025 table geography", "StableNever": "Stable analytical domain before population<30000 control restriction"},
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [initial_path, old_path, current_path, audit_path, manifest_path, treatment_path]},
        "stable_domain_excluded_check": {"partial_count": 0, "excluded_count": len(excluded),
            "excluded_status_counts": excluded.status_2025.value_counts().to_dict(),
            "all_excluded_absent_from_initial_frr": True},
        "caution": "StableNeverN (14611) is not the broad control macro ControlN (14361 after population filter). No TeX or main artifact script was edited."}
    dest = ROOT / "reports/review_A_institutional_macro_values.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(values, ensure_ascii=False))


if __name__ == "__main__":
    main()
