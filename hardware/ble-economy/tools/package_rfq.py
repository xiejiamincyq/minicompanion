"""Assemble the supplier RFQ and verify BOM, placement, enclosure and source revisions."""
import csv
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "quote"
OUT.mkdir(exist_ok=True)

def read_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def read_csv(rel):
    with (ROOT / rel).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(rel):
    return sha((ROOT / rel).read_bytes())

def verify_sources():
    pcb = read_json("verification/a2_pcb_receipt.json")
    electrical = read_json("verification/a2_electrical_checks.json")
    board_cost = read_json("sourcing/cost_model_receipt.json")
    fab = read_json("manufacturing/manifest.json")
    board_hash = sha_file("project/mini_companion_a2.kicad_pcb")
    sch_hash = sha_file("project/mini_companion_a2.kicad_sch")
    xml_hash = sha_file("verification/a2_netlist.xml")
    assert board_hash == fab["pcb_sha256"] == pcb["pcb_sha256"] == board_cost["pcb_sha256_at_bom_generation"]
    assert sch_hash == fab["schematic_sha256"] == pcb["schematic_sha256"]
    assert xml_hash == fab["xml_sha256"] == pcb["xml_sha256"] == board_cost["netlist_sha256"]
    for name, digest in electrical["source_sha256"].items():
        assert sha_file(name.replace(chr(92), "/")) == digest, name
    for name, digest in fab["files"].items():
        assert sha_file("manufacturing/" + name) == digest, name
    assert read_json("verification/a2_saved_drc.json")["ignored_checks"] == []
    assert not any(sheet["violations"] for sheet in read_json("verification/a2_erc.json")["sheets"])
    assert (pcb["violations"], pcb["schematic_parity"], pcb["unconnected_items"]) == (0, 0, 0)
    assert pcb["assembly_components_bottom"] == 0 and pcb["drc_exclusions"] == 0
    assert min(map(float, pcb["via_drill_histogram_mm"])) >= 0.30

    bom = read_csv("sourcing/BOM_JLC_顶面.csv")
    refs = [ref.strip() for row in bom for ref in row["Designator"].split(",")]
    cpl = read_csv("manufacturing/top-position-jlc.csv")
    assert len(refs) == len(set(refs)) == len(cpl) == pcb["assembly_components_top"] == 38
    assert len(bom) == len({row["LCSC Part #"] for row in bom}) == board_cost["main_unique_skus"] == 26
    assert all(row["Layer"] == "Top" for row in cpl)
    assert set(refs) == {row["Designator"] for row in cpl} == set(pcb["placements"])
    jack = next(row for row in cpl if row["Designator"] == "J1")
    assert (float(jack["Mid X"]), float(jack["Mid Y"]), float(jack["Rotation"])) == (6.7, 22.5, 90)

    case = read_json("mechanical/geometry-check.json")
    offset = case["pcb_origin_xy_mm"]
    def placement(ref):
        row = pcb["placements"][ref]
        return [offset[0] + row["local_x_mm"], offset[1] + row["local_y_mm"]]
    assert [placement(f"SW{n}") for n in range(1,4)] == case["key_centres_xy_mm"]
    assert placement("SW4") == [72, 64.5] and pcb["placements"]["SW4"]["rotation_deg"] == 90
    assert placement("J1")[1] == case["mechanics"]["barrel_axis_yz_mm"][0]
    assert case["pcb_front_z_mm"] - 6.55 == case["mechanics"]["barrel_axis_yz_mm"][1]
    assert placement("D2") == [30.0,71.5]
    raw = (ROOT / "project/mini_companion_a2.kicad_pcb").read_text(encoding="utf8")
    mounts = []
    for footprint in re.split(r"\n\t\(footprint ", raw)[1:]:
        if not re.search(r'\(property "Reference" "H[1-4]"', footprint):
            continue
        pos = re.search(r"\n\t\t\(at ([\d.]+) ([\d.]+)", footprint)
        assert pos
        mounts.append([float(pos[1]) - 100 + offset[0], float(pos[2]) - 100 + offset[1]])
    assert sorted(mounts) == sorted(case["mechanics"]["small_board_mounts"])
    assert sum(case["intersection_mm3"].values()) < 0.0001
    quotes = read_json("verification/enclosure-web-quote.json")
    assert len(quotes["parts"]) == len(case["parts"]) == 4
    for part in quotes["parts"]:
        model = case["parts"][part["part"]]
        assert sha_file("mechanical/stl/" + part["part"] + ".stl") == model["sha256"] == part["sha256"]
        assert model["quantity_for_two"] == part["request"]["quantity"]
    return {"board_sha256":board_hash,"schematic_sha256":sch_hash,"netlist_sha256":xml_hash,
            "front_smd":len(refs),"front_skus":len(bom),"mounts_matched":len(mounts),
            "print_pieces_for_two":sum(p["quantity_for_two"] for p in case["parts"].values())}

def files_for_supplier():
    names = set()
    for path in (ROOT / "project").rglob("*"):
        if path.is_file() and (path.suffix in {".kicad_pro", ".kicad_sch", ".kicad_pcb", ".kicad_sym", ".kicad_mod", ".kicad_dru"}
                               or path.name in {"fp-lib-table","sym-lib-table","LICENSE.md"}):
            names.add(path.relative_to(ROOT).as_posix())
    for pattern in ("project/PCB设计说明.md","manufacturing/README.md","manufacturing/manifest.json","manufacturing/gerber/*","tools/verify_pcb.py","tools/export_manufacturing.py","manufacturing/*.csv","manufacturing/*.zip","manufacturing/drill-report.txt",
                    "mechanical/stl/*.stl","mechanical/geometry-check.json","mechanical/装配.md","mechanical/assembly-preview.png",
                    "verification/a2*.pdf","verification/enclosure-web-quote.json","verification/a2_electrical_checks.json","verification/a2_netlist.xml","design/electrical_contract.json","design/verify_electrical.py","design/capacitor_bias_evidence.json","verification/a2_erc.json","verification/a2_saved_drc.json","verification/a2_pcb_receipt.json",
                    "sourcing/BOM_JLC_顶面.csv","sourcing/外部询价与免焊线束要求.md",
                    "整机验收.md","使用与软件接口.md","design/电气设计与验收.md","quote/询价包说明.md"):
        paths = list(ROOT.glob(pattern))
        assert paths, pattern
        names.update(p.relative_to(ROOT).as_posix() for p in paths)
    return {("README.md" if n == "quote/询价包说明.md" else n):(ROOT/n).read_bytes() for n in sorted(names)}

def main():
    checks = verify_sources()
    data = files_for_supplier()
    manifest = {"purpose":"two complete prototypes, quotation only", "cross_checks":checks,
                "sha256":{n:sha(b) for n,b in sorted(data.items())}}
    data["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode()
    archive = OUT / "Mini-Companion-A2-RFQ.zip"
    with ZipFile(archive, "w") as z:
        for name, content in sorted(data.items()):
            entry = ZipInfo(name, (2026,11,19,0,0,0))
            entry.compress_type = ZIP_DEFLATED
            z.writestr(entry, content)
    with ZipFile(archive) as z:
        assert z.testzip() is None and sorted(z.namelist()) == sorted(data)
        assert all(z.read(n) == b for n,b in data.items())
    summary = {"archive":archive.name,"sha256":sha_file("quote/"+archive.name),
               "entries":len(data),"supplier_sources":checks}
    (OUT/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == "__main__":
    main()
