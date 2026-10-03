"""Record preserved legal evidence and independent file-count checks."""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = []
    # The parent downloader's successful official files retain their exact URLs.
    rows = json.loads((ROOT / "data/external/zoning_manifest.json").read_text(encoding="utf-8"))
    for row in rows:
        path = ROOT / "data/raw" / row["file"]
        if row.get("status_code") != 200 or not path.exists():
            continue
        actual = sha256(path)
        if actual != row["sha256"]:
            raise RuntimeError(f"Hash mismatch: {path}")
        evidence.append({"file": str(path.relative_to(ROOT)), "source_urls": [row["url"]],
                         "sha256": actual, "bytes": path.stat().st_size,
                         "role": "official_source_from_parent_download_manifest"})
    for path in sorted((ROOT / "data/raw/legal").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        urls = set(re.findall(r'"ref_id"\s*:\s*"(https://[^"\s]+)"', text))
        # Search hits and historical text output include the original URLs in titles.
        urls.update(re.findall(r"\((https://[^\s)]+)\)", text))
        role = "official_web_tool_retrieval_snapshot"
        if "discovery" in path.name or "attempt" in path.name:
            role = "discovery_or_failed_access_log_not_primary_assignment"
        if path.name == "social_l24119_initial2024_web.txt":
            role = "current_2026_social_text_not_primary_2024_version_despite_filename"
        if path.name.startswith("frr_2024_legifrance_web_"):
            role = "primary_initial_2024_assignment_official_original_jorf"
        evidence.append({"file": str(path.relative_to(ROOT)), "source_urls": sorted(urls),
                         "sha256": sha256(path), "bytes": path.stat().st_size, "role": role})
    extras = {
        "BV2022_au_01-01-2023.zip": (
            "https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip",
            "official_historical_bassin_composition_COG2023"),
        "bv2022_composition_cog2023_extracted.csv": (
            "https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip",
            "derived_direct_OOXML_extraction_official_bassin_composition_COG2023"),
        "frr_aelb.xlsx": (
            "https://www.eau-loire-bretagne.fr/files/live/sites/aides-redevances/files/Aides-12prog/Outils%20de%20mise%20en%20oeuvre/FRR_communes_AELB.xlsx",
            "official_regional_only_not_national_assignment"),
        "ddt26_frr_2024.zip": (
            "https://atom.geo-ide.developpement-durable.gouv.fr/atomArchive/GetResource?id=b39c9b08-7914-4a19-a914-23fd2d413339&dataType=dataset",
            "official_regional_only_not_national_assignment"),
        "frr_2024_jo_intramuros_DISCOVERY_ONLY.pdf": (
            "https://files.appli-intramuros.com/files/news/attachments/1037/2024625172540191006_joe_20240620_0144_0051-fusionne.pdf",
            "non_official_mirror_crosscheck_only_no_codes_derived"),
        "dgcl_arcgis2024_app_data.json": (
            "https://www.arcgis.com/sharing/rest/content/items/2fae11a7ff1b4e60840d563d6d34444c/data?f=json",
            "official_linked_application_replaced_with_2025_layer_not_initial_2024"),
        "dgcl_arcgis2024_app_metadata.json": (
            "https://www.arcgis.com/sharing/rest/content/items/2fae11a7ff1b4e60840d563d6d34444c?f=json",
            "official_linked_application_metadata_not_initial_2024"),
        "dgcl_arcgis2024_webmap_data.json": (
            "https://www.arcgis.com/sharing/rest/content/items/70791b36ca57450db7cf10892eee67c8/data?f=json",
            "current_2025_layer_not_initial_2024"),
        "dgcl_arcgis_owner_catalog.json": (
            "https://www.arcgis.com/sharing/rest/search?q=owner:DGCL.SDCAT&f=json&num=100",
            "discovery_catalog_not_initial_2024"),
    }
    for name, (url, role) in extras.items():
        path = ROOT / "data/raw/legal" / name
        if path.exists():
            evidence.append({"file": str(path.relative_to(ROOT)), "source_urls": [url],
                             "sha256": sha256(path), "bytes": path.stat().st_size, "role": role})
    old = pd.read_excel(ROOT / "data/raw/zrr_2021.xls", sheet_name="Classement ZRR (COG 2021)",
                        header=None, dtype=str).iloc[6:].copy()
    old = old[old.iloc[:, 0].str.fullmatch(r"[0-9AB]{5}", na=False)]
    initial = pd.read_csv(ROOT / "data/processed/frr_2024_codes_verified.csv", dtype=str)
    current = pd.read_excel(ROOT / "data/raw/frr_2025.xlsx", dtype=str)
    initial_codes = set(initial.code_insee)
    current_codes = set(current.loc[current.iloc[:, 3].isin(
        ["FRR socle", "FRR+", "Classée FRR partiellement"]), current.columns[0]])
    raw = (ROOT / "data/raw/legal/frr_2025_annex1_additions_web.txt").read_text(encoding="utf-8")
    start = raw.index("ANNEXE I")
    end = raw.index("ANNEXE II", start + len("ANNEXE I"))
    additions = set(re.findall(r"\(([0-9AB]{5})\)", raw[start:end]))
    if len(additions) != 117 or additions & initial_codes:
        raise RuntimeError("Unexpected April 2025 additions")
    mvt = pd.read_csv(ROOT / "data/raw/movements_cog2026.csv", dtype=str)
    non_annex_new = current_codes - initial_codes - additions
    # Verify all remaining new codes have an observed post-2023 geography change.
    modern = mvt[mvt.DATE_EFF >= "2024-01-01"]
    changed_codes = set(modern.COM_AV) | set(modern.COM_AP)
    if not non_annex_new <= changed_codes:
        raise RuntimeError("Unexplained 2025 code additions beyond official annex")
    treatment_check = {"status": "not_yet_available"}
    treatment_path = ROOT / "data/processed/commune_treatment.csv"
    if treatment_path.exists():
        treatment = pd.read_csv(treatment_path, dtype=str)
        prior_full = set(old.loc[old.iloc[:, 2].str.startswith("C -", na=False), 0])
        prior_partial = set(old.loc[old.iloc[:, 2].str.startswith("P -", na=False), 0])
        never = treatment[treatment.treatment_group.eq("NEVER_TREATED")]
        new = treatment[treatment.treatment_group.eq("NEW_FRR")]
        contradictions = {
            "never_in_initial_frr": sorted(set(never.commune_code) & initial_codes),
            "never_prior_zrr_full": sorted(set(never.commune_code) & prior_full),
            "never_prior_zrr_partial": sorted(set(never.commune_code) & prior_partial),
            "never_2025_not_nonclassee": sorted(never.loc[
                never.status_2025.ne("Non classée"), "commune_code"]),
            "new_not_initial_frr": sorted(set(new.commune_code) - initial_codes),
            "new_prior_zrr_full": sorted(set(new.commune_code) & prior_full),
            "new_prior_zrr_partial": sorted(set(new.commune_code) & prior_partial),
        }
        if any(contradictions.values()):
            raise RuntimeError(f"Institutional treatment contradictions: {contradictions}")
        stable = treatment[treatment.analysis_stable.eq("True") & treatment.metropolitan.eq("True")]
        treatment_check = {"status": "coding_consistent_with_independent_official_sets",
            "file": str(treatment_path.relative_to(ROOT)), "sha256": sha256(treatment_path),
            "contradictions": contradictions,
            "all_group_counts": treatment.treatment_group.value_counts().to_dict(),
            "stable_metropolitan_group_counts": stable.treatment_group.value_counts().to_dict(),
            "scope": "Institutional coding only; not causal-design, outcome, or manuscript validation."}
    report = {
        "audit_date": "2026-10-03", "stage": "institutional_source_audit_before_manuscript_review",
        "initial_frr": {"codes": len(initial_codes), "partial": int(initial.partially_zoned.eq("1").sum()),
            "cog": 2023, "effective_date": "2024-07-01",
            "sha256_csv": sha256(ROOT / "data/processed/frr_2024_codes_verified.csv")},
        "old_zrr_cog2021": {"total_codes": len(old), "unique_codes": old.iloc[:, 0].nunique(),
            "simple_status_counts": old.iloc[:, 2].value_counts().to_dict(),
            "detailed_status_counts": old.iloc[:, 3].value_counts().to_dict(),
            "legal_continuity": "2017 classification modified in February 2018 plus 2017 exit beneficiary effects until 2024-06-30; individual geography must be stable"},
        "current_frr2025": {"table_status_counts": current.iloc[:, 3].value_counts().to_dict(),
            "current_core_codes_including_partial": len(current_codes),
            "initial_codes_missing_in_current": len(initial_codes - current_codes),
            "current_codes_not_in_initial": len(current_codes - initial_codes),
            "april_annex1_new_codes": len(additions),
            "other_new_codes_with_insee_geography_event": sorted(non_annex_new),
            "comparison_caution": "Gross code differences, not constant-geography treatment transitions."},
        "independent_treatment_coding_check": treatment_check,
        "limitations": [
            "No exhaustive official national local CFE/TFPB adoption table has been verified.",
            "Actual initial assignment path has not yet been reconstructed for each analysis commune.",
            "Later classification does not measure June 2024 information or policy anticipation.",
            "This audit does not validate a manuscript or causal identification."],
        "evidence_files": evidence,
    }
    dest = ROOT / "reports/legal_source_audit_manifest.json"
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(dest), "evidence_files": len(evidence),
        "initial_frr": len(initial_codes), "old_zrr_codes": len(old),
        "april_additions": len(additions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
