"""Archive public INSEE API documentation without authentication or unit records.

The official portal is an SPA. Its public assets/config.json identifies the
Gravitee documentation endpoint used below. No SIREN/SIRET query is made.
"""
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures
import hashlib
import json
import requests
import argparse
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/external/sirene_dictionary"
PORTAL = "https://portail-api.insee.fr"
API_ID = "2ba0e549-5587-3ef1-9082-99cd865de66f"
SELECT = {1, 6, 7, 91, 92, 105, 106, 107, 126, 132, 141, 142, 143, 144}


def get(url):
    response = requests.get(url, timeout=(15, 90))
    response.raise_for_status()
    return response


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    config = get(PORTAL + "/assets/config.json").json()
    base = config["baseURL"] + "/apis/" + API_ID + "/pages"
    index = get(base + "?size=-1").json()
    (OUT / "api_portal_config.json").write_text(json.dumps(config, indent=2), encoding="utf8")
    (OUT / "api_pages_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf8")
    pages = [p for p in index["data"] if p["order"] in SELECT]

    def fetch(page):
        url = page["_links"]["content"]
        r = get(url)
        data = r.content
        name = f"api_{page['order']:03d}_{page['id']}.md"
        (OUT / name).write_bytes(data)
        return {"file": name, "page_id": page["id"], "name": page["name"],
                "url": url, "portal_url": PORTAL + "/catalog/api/" + API_ID + "/doc",
                "page_updated_at": page["updated_at"], "status_code": r.status_code,
                "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat()}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        manifest = list(pool.map(fetch, pages))
    (OUT / "api_documentation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
    for row in manifest:
        print(row["file"], row["size_bytes"], row["sha256"])


def audit_snapshot():
    """Only publish national aggregates. Never project names or detailed addresses."""
    sys.path.insert(0, str(ROOT / ".vendor"))
    import duckdb
    conn = duckdb.connect()
    conn.execute("SET threads=2")
    conn.execute("SET memory_limit='1GB'")
    def stock(name):
        return "read_parquet('" + str(ROOT / "data/raw" / ("stock-" + name + "-parquet.parquet")).replace("\\", "/") + "')"
    queries = {
        "establishment_diffusion": "SELECT statutDiffusionEtablissement AS diffusion, count(*) AS n, count(codeCommuneEtablissement) AS n_commune, count(*) FILTER (WHERE codeCommuneEtablissement='[ND]') AS n_commune_nd FROM " + stock("stocketablissement") + " GROUP BY 1 ORDER BY 1",
        "establishment_band_year": "SELECT anneeEffectifsEtablissement AS reference_year, count(*) AS n FROM " + stock("stocketablissement") + " GROUP BY 1 ORDER BY 1 NULLS LAST",
        "establishment_state_employer": "SELECT etatAdministratifEtablissement AS administrative_state, caractereEmployeurEtablissement AS employer, count(*) AS n FROM " + stock("stocketablissement") + " GROUP BY 1,2 ORDER BY 1,2 NULLS LAST",
        "ul_employer": "SELECT caractereEmployeurUniteLegale AS employer, count(*) AS n FROM " + stock("stockunitelegale") + " GROUP BY 1 ORDER BY 1 NULLS LAST",
        "succession_flags": "SELECT transfertSiege AS headquarters_transfer, continuiteEconomique AS economic_continuity, count(*) AS n FROM " + stock("stocketablissementlienssuccession") + " GROUP BY 1,2 ORDER BY 1,2",
        "establishment_history_dates": "SELECT count(*) AS n, count(*) FILTER (WHERE dateDebut IS NULL) AS start_null, count(*) FILTER (WHERE dateDebut=DATE '1900-01-01') AS start_unknown, count(*) FILTER (WHERE dateFin IS NULL) AS current_intervals, count(*) FILTER (WHERE dateFin<dateDebut) AS reversed_intervals FROM " + stock("stocketablissementhistorique"),
    }
    results = {"snapshot": "2026-10 official stock", "audit_generated_at_utc": datetime.now(timezone.utc).isoformat(), "queries": queries}
    for name, query in queries.items():
        cursor = conn.execute(query)
        columns = [d[0] for d in cursor.description]
        results[name] = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(name, json.dumps(results[name], ensure_ascii=True))
    (OUT / "snapshot_audit_aggregates.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-snapshot", action="store_true")
    args = parser.parse_args()
    if args.audit_snapshot:
        audit_snapshot()
    else:
        main()
