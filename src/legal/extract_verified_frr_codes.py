"""Extract initial 2024 FRR assignment solely from official Legifrance text.

The web retrieval snapshots are preserved verbatim in data/raw/legal. The
non-official public-gazette PDF is used only for an independent equality check;
it never supplies an output code. COG vintage is 2023, as stated in the annex.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/legal"
OUTPUT = ROOT / "data/processed/frr_2024_codes_verified.csv"
SOURCE = "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    files = sorted(RAW.glob("frr_2024_legifrance_web_*.txt"))
    if not files:
        files = sorted((ROOT / "docs/sources/frr_2024").glob("frr_2024_legifrance_web_*.txt"))
    if not files:
        raise RuntimeError("Missing official text snapshots")
    codes, partial, lines = set(), set(), set()
    provenance = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        # Codes occur as parenthesised INSEE identifiers in the official annex.
        codes.update(re.findall(r"\(([0-9AB]{5})\)", text))
        partial.update(re.findall(r"\(([0-9AB]{5})\)\s*\[P\]", text))
        lines.update(int(n) for n in re.findall(r"L(\d+):", text))
        provenance.append({"file": str(path.relative_to(ROOT)),
                           "sha256": digest(path), "bytes": path.stat().st_size})
    missing = sorted(set(range(148, 343)) - lines)
    if missing:
        raise RuntimeError(f"Official annex retrieval has missing lines: {missing}")
    if len(codes) != 17717:
        raise RuntimeError(f"Unexpected initial FRR commune count: {len(codes)}")
    mirror = RAW / "frr_2024_jo_intramuros_DISCOVERY_ONLY.pdf"
    crosscheck = {"status": "not_run"}
    if mirror.exists():
        import fitz
        with fitz.open(mirror) as pdf:
            text = "\n".join(pdf[n].get_text() for n in range(61))
        other = set(re.findall(r"\(([0-9AB]{5})\)", text))
        if codes != other:
            raise RuntimeError("Official codes differ from independently preserved gazette")
        crosscheck = {"status": "exact_set_equality", "codes": len(other),
                      "file": str(mirror.relative_to(ROOT)), "sha256": digest(mirror),
                      "source_role": "discovery_and_crosscheck_only_not_primary_data"}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code_insee", "frr_initial_2024",
            "partially_zoned", "cog_vintage", "assignment_effective_date", "source_url"])
        writer.writeheader()
        for code in sorted(codes):
            writer.writerow({"code_insee": code, "frr_initial_2024": 1,
                "partially_zoned": int(code in partial), "cog_vintage": 2023,
                "assignment_effective_date": "2024-07-01", "source_url": SOURCE})
    manifest = {"source_url": SOURCE, "source_kind": "official_original_jorf_text",
        "nor": "TREB2414964A", "publication_date": "2024-06-20",
        "effective_date": "2024-07-01", "retrieved_utc_date": "2026-10-03",
        "cog_vintage": 2023, "commune_count": len(codes),
        "partially_zoned_count": len(partial), "partially_zoned_codes": sorted(partial),
        "required_annex_lines": [148, 342], "missing_required_lines": missing,
        "output": str(OUTPUT.relative_to(ROOT)), "output_sha256": digest(OUTPUT),
        "raw_official_snapshots": provenance, "independent_crosscheck": crosscheck,
        "caution": "Initial assignment; excludes later retrospective FRR additions and legacy beneficiaries. COG 2023 codes require a geography-vintage audit before merging."}
    RAW.mkdir(parents=True,exist_ok=True)
    target = RAW / "frr_2024_official_extraction_manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "communes": len(codes),
        "partial": len(partial), "sha256": digest(OUTPUT),
        "crosscheck": crosscheck["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
