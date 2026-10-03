"""Independent institutional checks of treatment coding and selected borders.

Does not read outcomes. Bassin membership is parsed directly from official
OOXML because the original workbook has styles rejected by openpyxl.
"""
from pathlib import Path
import gzip
import hashlib
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASIN_URL = "https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def basin_composition():
    path = ROOT / "data/raw/legal/BV2022_au_01-01-2023.zip"
    with zipfile.ZipFile(path) as outer:
        with zipfile.ZipFile(io.BytesIO(outer.read("BV2022_au_01-01-2023.xlsx"))) as book:
            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            strings = ["".join(t.text or "" for t in si.iterfind(".//x:t", ns))
                for si in ET.fromstring(book.read("xl/sharedStrings.xml")).findall("x:si", ns)]
            rows = []
            for row in ET.fromstring(book.read("xl/worksheets/sheet3.xml")).findall(".//x:row", ns):
                if int(row.attrib["r"]) <= 6:
                    continue
                vals = {}
                for cell in row.findall("x:c", ns):
                    value = cell.find("x:v", ns)
                    value = "" if value is None else value.text
                    if cell.attrib.get("t") == "s":
                        value = strings[int(value)]
                    vals[re.sub(r"\d", "", cell.attrib["r"])] = value
                if re.fullmatch(r"[0-9AB]{5}", vals.get("A", "")):
                    rows.append(vals)
    frame = pd.DataFrame(rows).rename(columns={"A": "commune_code", "B": "commune_name",
        "C": "bassin_2022_cog2023", "D": "bassin_name", "E": "commune_type",
        "F": "department", "G": "region"})
    assert frame.commune_code.is_unique
    output = ROOT / "data/raw/legal/bv2022_composition_cog2023_extracted.csv"
    frame.to_csv(output, index=False)
    return frame, {"source_url": BASIN_URL, "raw_sha256": digest(path),
        "extraction_sha256": digest(output), "communes": len(frame), "cog": 2023}


def components(pairs, cols):
    graph = nx.Graph()
    members = []
    for _, row in pairs.iterrows():
        nodes = set(prefix + str(row[column]) for prefix, column in cols)
        first = sorted(nodes)[0]
        graph.add_node(first)
        graph.add_edges_from((first, node) for node in nodes - {first})
        members.append(first)
    groups = sorted(nx.connected_components(graph), key=lambda group: min(group))
    labels = {node: n for n, group in enumerate(groups) for node in group}
    pair_labels = [labels[node] for node in members]
    sizes = pd.Series(pair_labels).value_counts()
    return pair_labels, {"components": len(groups), "maximum_pairs": int(sizes.max()),
        "largest_five_pair_counts": sizes.nlargest(5).tolist(),
        "pair_size_concentration_inverse": float(sizes.sum() ** 2 / sizes.pow(2).sum()),
        "size_diagnostic_is_not_formal_effective_cluster_count": True}


def main():
    treatment = pd.read_csv(ROOT / "data/processed/commune_treatment.csv", dtype=str)
    matrix = pd.read_csv(ROOT / "tables/treatment_transition_matrix.csv", dtype=str)
    pairs = pd.read_csv(ROOT / "data/processed/border_pairs.csv", dtype=str)
    edges = pd.read_csv(ROOT / "data/processed/border_edges.csv", dtype=str)
    official = pd.read_csv(ROOT / "data/processed/frr_2024_codes_verified.csv", dtype=str)
    old = pd.read_excel(ROOT / "data/raw/zrr_2021.xls", sheet_name="Classement ZRR (COG 2021)",
                        header=None, dtype=str).iloc[6:]
    prior = set(old.loc[old.iloc[:, 2].str.startswith(("C -", "P -"), na=False), 0])
    initial = set(official.code_insee)
    assert treatment.commune_code.is_unique
    stable = treatment[treatment.analysis_stable.eq("True") & treatment.metropolitan.eq("True")]
    universes = {"all_DGCL_2025_codes": treatment, "stable_metropolitan": stable}
    for _, row in matrix.iterrows():
        got = universes[row.universe].treatment_group.eq(row.transition).sum()
        assert got == int(row.n_communes), (row.universe, row.transition, got)
    new = set(treatment.loc[treatment.treatment_group.eq("NEW_FRR"), "commune_code"])
    never = set(treatment.loc[treatment.treatment_group.eq("NEVER_TREATED"), "commune_code"])
    assert new <= initial and not new & prior and not never & (initial | prior)
    assert treatment.loc[treatment.commune_code.isin(never), "status_2025"].eq("Non classée").all()
    lookup = stable.set_index("commune_code")
    for frame in [pairs, edges]:
        assert frame.treated_code.map(lookup.treatment_group).eq("NEW_FRR").all()
        assert frame.control_code.map(lookup.treatment_group).eq("NEVER_TREATED").all()
        assert frame.control_code.map(lookup.population_2021).astype(float).lt(30000).all()
        assert frame.shared_boundary_m.astype(float).gt(50).all()
        for role in ["treated", "control"]:
            assert frame[role + "_code"].map(lookup.epci_2023).eq(frame[role + "_epci"]).all()
            assert frame[role + "_code"].map(lookup.department).eq(frame[role + "_department"]).all()
    assert pairs.treated_code.is_unique and pairs.control_code.is_unique
    assert not set(pairs.treated_code) & set(pairs.control_code)
    all_edges = set(zip(edges.treated_code, edges.control_code))
    assert set(zip(pairs.treated_code, pairs.control_code)) <= all_edges
    assert len(all_edges) == len(edges)
    # Independently verify all selected shared boundaries in the original official polygons.
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform
    needed = set(pairs.treated_code) | set(pairs.control_code)
    transformer = Transformer.from_crs(4326, 2154, always_xy=True)
    geoms = {}
    with gzip.open(ROOT / "data/raw/communes_2024_5m.geojson.gz", "rt", encoding="utf-8") as handle:
        geo = json.load(handle)
    for feature in geo["features"]:
        code = str(feature["properties"].get("code", ""))
        if code in needed:
            geoms[code] = transform(transformer.transform, shape(feature["geometry"]))
    assert needed <= set(geoms)
    errors = []
    for _, row in pairs.iterrows():
        length = geoms[row.treated_code].boundary.intersection(geoms[row.control_code].boundary).length
        assert length > 50
        errors.append(abs(length - float(row.shared_boundary_m)))
    assert max(errors) < 1e-6
    del geo, geoms
    basins, basin_source = basin_composition()
    mapping = basins.set_index("commune_code").bassin_2022_cog2023
    pairs["treated_bassin"] = pairs.treated_code.map(mapping)
    pairs["control_bassin"] = pairs.control_code.map(mapping)
    assert pairs[["treated_bassin", "control_bassin"]].notna().all().all()
    epci_cols = [("E:", "treated_epci"), ("E:", "control_epci")]
    dept_cols = [("D:", "treated_department"), ("D:", "control_department")]
    basin_cols = [("B:", "treated_bassin"), ("B:", "control_bassin")]
    ec, ed = components(pairs, epci_cols)
    dc, dd = components(pairs, dept_cols)
    jc, jd = components(pairs, epci_cols + dept_cols)
    bc, bd = components(pairs, epci_cols + dept_cols + basin_cols)
    basin_joint = {}
    for i, (_, row) in enumerate(pairs.iterrows()):
        for key in [row.treated_bassin, row.control_bassin]:
            basin_joint.setdefault(key, set()).add(jc[i])
    crossing = sorted(key for key, groups in basin_joint.items() if len(groups) > 1)
    pairs["cluster_E"] = [f"E{group + 1:03d}" for group in ec]
    pairs["cluster_D"] = [f"D{group + 1:03d}" for group in dc]
    pairs["cluster_ED"] = [f"ED{group + 1:03d}" for group in jc]
    pairs["cluster_EDB"] = [f"EDB{group + 1:03d}" for group in bc]
    pair_mapping = ROOT / "reports/review_A_joint_dependency_pair_mapping.csv"
    mapping_columns = ["pair_id", "treated_code", "control_code", "treated_epci", "control_epci",
        "treated_department", "control_department", "treated_bassin", "control_bassin",
        "cluster_E", "cluster_D", "cluster_ED", "cluster_EDB"]
    pairs[mapping_columns].to_csv(pair_mapping, index=False)
    membership = []
    for label, group in pairs.groupby("cluster_EDB", sort=True):
        row = {"cluster_EDB": label, "pairs": len(group), "communes": 2 * len(group),
            "ED_components_contained": group.cluster_ED.nunique(),
            "treated_codes": "|".join(sorted(group.treated_code)),
            "control_codes": "|".join(sorted(group.control_code))}
        for name, columns in [("EPCI", ["treated_epci", "control_epci"]),
                              ("department", ["treated_department", "control_department"]),
                              ("bassin", ["treated_bassin", "control_bassin"])]:
            members = sorted(set(group[columns[0]]) | set(group[columns[1]]))
            row[name + "_count"] = len(members)
            row[name + "_members"] = "|".join(members)
        membership.append(row)
    membership_frame = pd.DataFrame(membership).sort_values(["pairs", "cluster_EDB"],
        ascending=[False, True])
    membership_path = ROOT / "reports/review_A_joint_dependency_components.csv"
    membership_frame.to_csv(membership_path, index=False)
    structure = {"EPCI_selected_union": len(set(pairs.treated_epci) | set(pairs.control_epci)),
        "departments_selected_union": len(set(pairs.treated_department) | set(pairs.control_department)),
        "basins_selected_union": len(set(pairs.treated_bassin) | set(pairs.control_bassin)),
        "basins_treated_role": pairs.treated_bassin.nunique(),
        "basins_control_role": pairs.control_bassin.nunique(),
        "basins_in_both_roles": len(set(pairs.treated_bassin) & set(pairs.control_bassin)),
        "same_bassin_pairs": int(pairs.treated_bassin.eq(pairs.control_bassin).sum()),
        "basins_crossing_ED_components": len(crossing),
        "EDB_single_pair_components": int(membership_frame.pairs.eq(1).sum()),
        "EDB_components_combining_multiple_ED_components": int(membership_frame.ED_components_contained.gt(1).sum()),
        "largest_EDB_component_share": float(membership_frame.pairs.max() / len(pairs)),
        "largest_five_EDB_component_share": float(membership_frame.pairs.nlargest(5).sum() / len(pairs)),
        "all_communes_covered_by_official_basin_mapping": True,
        "output_files": {str(path.relative_to(ROOT)): digest(path) for path in [pair_mapping, membership_path]}}
    result = {"audit_date": "2026-10-03", "status": "institutional_coding_and_border_geometry_checks_passed",
        "scope": "No outcome or statistical coefficient validation; no assignment-path reconstruction.",
        "source_hashes": {str(path.relative_to(ROOT)): digest(path) for path in [
            ROOT / "data/processed/commune_treatment.csv", ROOT / "tables/treatment_transition_matrix.csv",
            ROOT / "data/processed/border_pairs.csv", ROOT / "data/processed/border_edges.csv"]},
        "all_communes": len(treatment), "stable_metropolitan_communes": len(stable),
        "transition_matrix_rows_verified": len(matrix), "pairs": len(pairs), "edges": len(edges),
        "distinct_communes_selected": len(needed), "no_commune_repeated": True,
        "all_selected_pairs_geometry_verified": True, "maximum_boundary_length_error_metres": max(errors),
        "new_stable": int(stable.treatment_group.eq("NEW_FRR").sum()),
        "never_stable": int(stable.treatment_group.eq("NEVER_TREATED").sum()),
        "never_below_30000": int((stable.treatment_group.eq("NEVER_TREATED") & stable.population_2021.astype(float).lt(30000)).sum()),
        "treated_border_candidates": edges.treated_code.nunique(),
        "control_border_candidates": edges.control_code.nunique(),
        "same_epci_pairs": int(pairs.treated_epci.eq(pairs.control_epci).sum()),
        "same_department_pairs": int(pairs.treated_department.eq(pairs.control_department).sum()),
        "dependency_components": {"EPCI": ed, "department": dd, "EPCI_department": jd,
            "EPCI_department_bassin": bd}, "bassin_source": basin_source,
        "dependency_membership_structure": structure,
        "basins_crossing_epci_department_components": crossing,
        "restriction": "Joint EPCI-department grouping alone does not contain all shared bassin membership; additional regional/spatial dependence can also remain."}
    output = ROOT / "reports/review_A_final_coding_border_audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pairs": len(pairs), "transition_rows": len(matrix),
        "max_boundary_length_error_m": max(errors), "basins_crossing_joint": len(crossing),
        "components": result["dependency_components"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
