"""Verify saved KiCad sources and export unsubmitted files for supplier review.

Run this after the PCB editor has saved the final filled zones and after
refreshing sourcing/jlc_main_bom_rfq.csv from the same schematic.
The output directory must be new. Failed checks cannot overwrite earlier packs.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"
NAME = "mini_companion_integrated"
SCHEMATIC = PROJECT / (NAME + ".kicad_sch")
BOARD = PROJECT / (NAME + ".kicad_pcb")
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def indexed(rows, key, label):
    result = {}
    for row in rows:
        ref = row[key]
        if not ref or ref in result:
            raise ValueError(f"Empty or duplicate {label}: {ref}")
        result[ref] = row
    return result


def require_refs(actual, expected, label):
    if set(actual) != set(expected):
        raise ValueError(f"{label}: missing {sorted(set(expected) - set(actual))}; "
                         f"extra {sorted(set(actual) - set(expected))}")


def netlist_signature(path):
    """Ignore export time/order, retain every component field and pin/net contract."""
    xml = ET.parse(path)
    def canonical(element):
        return (element.tag, tuple(sorted(element.attrib.items())),
                (element.text or "").strip(), tuple(sorted(canonical(c) for c in element)))
    components = {}
    pins = {}
    for comp in xml.findall("./components/comp"):
        ref = comp.attrib["ref"]
        if ref in components:
            raise ValueError(f"Duplicate netlist component: {ref}")
        components[ref] = canonical(comp)
    for net in xml.findall("./nets/net"):
        for node in net.findall("node"):
            key = (node.attrib["ref"], node.attrib["pin"])
            if key in pins or key[0] not in components:
                raise ValueError(f"Duplicate or unknown netlist endpoint: {key}")
            pins[key] = (net.attrib["name"], canonical(node))
    return dict(sorted(components.items())), dict(sorted(pins.items()))


def validate_sourcing(netlist, sourcing, main_rows=None):
    """Pure read-only validation, also usable without running ERC/DRC or packaging."""
    receipt = json.loads((sourcing / "sourcing_validation.json").read_text(encoding="utf-8-sig"))
    if not receipt.get("data_validation_passed") or receipt.get("errors"):
        raise ValueError("Sourcing validation has not passed.")
    if receipt["netlist_sha256"] != sha(netlist):
        raise ValueError("Sourcing receipt does not match the saved final netlist.")
    parts = indexed([dict(ref=p.attrib["ref"], element=p) for p in
                     ET.parse(netlist).findall("./components/comp")], "ref", "netlist reference")
    by_ref = indexed(read_rows(sourcing / "bom_by_ref.csv"), "ref", "BOM reference")
    saved = {ref: row for ref, row in by_ref.items() if row["source"] == "saved_netlist"}
    require_refs(saved, parts, "Expanded BOM/netlist coverage")
    previous = indexed(read_rows(sourcing / "source_snapshot/baseline_bom_by_ref.csv"), "ref", "baseline reference")
    previous_mpn = {r["mpn"]: r for r in previous.values() if r["mpn"]}
    catalog = {r["mpn"]: r for r in json.loads(
        (sourcing / "primary_source_checks.json").read_text(encoding="utf-8"))["components"]}
    expected = {"main": set(), "external": set(), "excluded": set()}
    for ref, item in parts.items():
        part = item["element"]
        row = saved[ref]
        fields = {f.attrib["name"]: f.text or "" for f in part.findall("./fields/field")}
        props = {p.attrib["name"] for p in part.findall("property")}
        old = previous.get(ref, {})
        mpn = (fields.get("MPN") or fields.get("MP") or
               fields.get("Manufacturer Part Number") or old.get("mpn", ""))
        footprint = part.findtext("footprint", "")
        domain = fields.get("AssemblyDomain") or old.get("assembly_domain") or "main"
        libpart = part.find("libsource").attrib["part"]
        feature = (libpart.startswith(("TestPoint", "MountingHole")) or
                   mpn.startswith("SOLDER_PADS_") or "WirePads_" in footprint)
        category = "pcb_feature" if feature else "electronics"
        if "exclude_from_bom" in props and not feature:
            category = "excluded_component"
        if "exclude_from_board" in props and domain == "main" and not feature:
            domain = "offboard"
        role = ("excluded" if category != "electronics" else
                "main" if domain == "main" else "external")
        expected[role].add(ref)
        check = catalog.get(mpn, {})
        lcsc = fields.get("LCSC") or fields.get("LCSC Part") or fields.get("LCSC Part #") or ""
        if not lcsc and mpn == old.get("mpn"):
            lcsc = old.get("lcsc", "")
        lcsc = lcsc or check.get("lcsc", "")
        maker = (fields.get("Manufacturer") or fields.get("MANUFACTURER") or fields.get("MF") or
                 check.get("manufacturer") or previous_mpn.get(mpn, {}).get("manufacturer", ""))
        maker = {"Yageo": "YAGEO", "XKB": "XKB Connection"}.get(maker, maker)
        values = dict(mpn=mpn, manufacturer=maker, lcsc=lcsc, footprint=footprint,
                      value=part.findtext("value", ""), category=category, assembly_domain=domain,
                      qty_per_device="1", quantity_two="2")
        for key, value in values.items():
            if row[key] != value:
                raise ValueError(f"Expanded BOM differs from netlist/source identity: {ref}.{key}")
        if role == "main" and (not mpn or not maker or not footprint or
                               props.intersection({"dnp", "exclude_from_pos_files"})):
            raise ValueError(f"Main assembly component is incomplete or excluded from placement: {ref}")

    def grouped(rows, refs, label):
        flat = {}
        for row in rows:
            members = [r.strip() for r in row["Designator"].split(",")]
            if int(row["Quantity_Per_Board"]) != len(members) or int(row["Net_Quantity_Two"]) != 2 * len(members):
                raise ValueError(f"{label} quantity differs from designators: {members}")
            for ref in members:
                if not ref or ref in flat or ref not in saved:
                    raise ValueError(f"{label} empty, duplicate or unknown reference: {ref}")
                flat[ref] = row
                for col, key in [("Comment", "mpn"), ("Footprint", "footprint"),
                                 ("Manufacturer", "manufacturer"), ("LCSC Part #", "lcsc")]:
                    if row[col] != saved[ref][key]:
                        raise ValueError(f"{label} identity differs at {ref}.{col}")
        require_refs(flat, refs, label + " coverage")
        return flat

    if main_rows is None:
        main_rows = read_rows(sourcing / "jlc_main_bom_rfq.csv")
    grouped(main_rows, expected["main"], "Main BOM")
    for filename, refs in [("excluded_from_main_placement.csv", expected["excluded"]),
                           ("offboard_materials.csv", set(by_ref) - expected["main"] - expected["excluded"])]:
        rows = indexed(read_rows(sourcing / filename), "ref", filename)
        require_refs(rows, refs, filename + " coverage")
        for ref in rows:
            if rows[ref] != by_ref[ref]:
                raise ValueError(f"{filename} differs from expanded BOM at {ref}.")
    sides = indexed(read_rows(sourcing / "side_assembly_rfq.csv"), "ref", "side reference")
    require_refs(sides, expected["main"], "Side assignment coverage")
    for ref, row in sides.items():
        if row["side"] not in {"F.Cu", "B.Cu"} or row["quantity_two"] != "2":
            raise ValueError(f"Invalid side/quantity at {ref}.")
        for key in ("mpn", "lcsc", "footprint"):
            if row[key] != saved[ref][key]:
                raise ValueError(f"Side assignment identity differs at {ref}.{key}")
    side_counts = {}
    for side, filename in [("F.Cu", "jlc_front_bom_rfq.csv"), ("B.Cu", "external_back_bom_rfq.csv")]:
        refs = {ref for ref, row in sides.items() if row["side"] == side}
        grouped(read_rows(sourcing / filename), refs, filename)
        side_counts[side] = len(refs)
    counts = {"netlist_components": len(parts), "main_board_fitted_per_unit": len(expected["main"]),
              "main_grouped_bom_rows": len(main_rows), "pcb_features_or_excluded": len(expected["excluded"])}
    if any(receipt[key] != value for key, value in counts.items()):
        raise ValueError("Sourcing receipt component counts differ from the validated BOM.")
    require_refs(receipt["external_electrical_refs"], expected["external"], "Receipt external references")
    if receipt["board_side_analysis"]["main_components_by_side"] != side_counts:
        raise ValueError("Sourcing receipt side counts differ from the validated BOM.")
    return {"counts": counts, "roles": {k: sorted(v) for k, v in expected.items()},
            "sides": {ref: row["side"] for ref, row in sides.items()}}


def supplier_inputs():
    """Map every supplied source attachment to its path inside the RFQ archive."""
    files = {}
    for name in ["供应商资料包说明.md", "供应商询价草稿_未发送.md", "线束与探头代装要求.md",
                 "offboard_materials.csv", "jlc_main_bom_rfq.csv", "jlc_front_bom_rfq.csv",
                 "external_back_bom_rfq.csv", "side_assembly_rfq.csv", "bom_by_ref.csv",
                 "excluded_from_main_placement.csv", "缺料替代核对_20261119.md"]:
        files[ROOT / "sourcing" / name] = "assembly/" + name
    print_rows = read_rows(ROOT / "mechanical/design/PRINT_PARTS.csv")
    # The approved two-device assembly has four distinct plastic part types.
    expected_counts = {"button": (3, 6), "rear_shell": (1, 2), "front_shell": (1, 2), "power_slider": (1, 2)}
    print_parts = indexed(print_rows, "部件", "printed part")
    require_refs(print_parts, expected_counts, "Printed part types")
    for name, row in print_parts.items():
        if (int(row["每台件数"]), int(row["两台实际打印件数"])) != expected_counts[name]:
            raise ValueError(f"Incorrect printing quantity: {name}")
        if row["打印STL"] != "stl/PRINT_" + name + ".stl":
            raise ValueError(f"Incorrect printing file mapping: {name}")
    stls = sorted((ROOT / "mechanical/stl").glob("PRINT_*.stl"))
    if {p.name for p in stls} != {"PRINT_" + n + ".stl" for n in expected_counts}:
        raise ValueError("The printing set must contain exactly the four approved STL files.")
    for path in stls:
        files[path] = "enclosure/stl/" + path.name
    files[ROOT / "mechanical/design/PRINT_PARTS.csv"] = "enclosure/PRINT_PARTS.csv"
    files[ROOT / "mechanical/rear-access.png"] = "enclosure/rear-access.png"
    return files


def export(output):
    if output.exists():
        raise FileExistsError(f"Choose a new output folder: {output}")
    executable = shutil.which("kicad-cli") or os.environ.get("KICAD_CLI") or r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
    def run(*args):
        subprocess.run([executable, *map(str, args)], check=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        root = Path(scratch)
        pack = root / "pack"
        gerbers = root / "fab"
        pack.mkdir()
        gerbers.mkdir()
        bom = ROOT / "sourcing/jlc_main_bom_rfq.csv"
        supplied = supplier_inputs()
        saved_netlist = ROOT / "verification/usb_eco.xml"
        def source_hashes():
            sources = set(supplied) | {saved_netlist, Path(__file__).resolve(),
                ROOT / "sourcing/build_sourcing.py", ROOT / "sourcing/primary_source_checks.json",
                ROOT / "sourcing/sourcing_validation.json"}
            sources.update(p for p in (ROOT / "sourcing/source_snapshot").iterdir() if p.is_file())
            sources.update(p for p in PROJECT.rglob("*") if p.is_file() and
                (p.suffix in {".kicad_sch", ".kicad_pcb", ".kicad_pro", ".kicad_dru",
                              ".kicad_sym", ".kicad_mod"} or p.name in {"fp-lib-table", "sym-lib-table"}))
            return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(sources)}
        before = source_hashes()
        sourcing = validate_sourcing(saved_netlist, ROOT / "sourcing")
        receipt = json.loads((ROOT / "sourcing/sourcing_validation.json").read_text(encoding="utf-8-sig"))
        if receipt["board_side_analysis"]["sha256"] != sha(BOARD):
            raise ValueError("Refresh sourcing data from the final saved board before quoting.")
        run("sch", "erc", "--format", "json", "--severity-all", "--exit-code-violations",
            "-o", pack / "ERC.json", SCHEMATIC)
        run("pcb", "drc", "--format", "json", "--all-track-errors", "--schematic-parity",
            "--severity-all", "--exit-code-violations", "-o", pack / "DRC.json", BOARD)
        erc = json.loads((pack / "ERC.json").read_text(encoding="utf-8"))
        drc = json.loads((pack / "DRC.json").read_text(encoding="utf-8"))
        if (erc.get("ignored_checks") or drc.get("ignored_checks")
                or any(sheet["violations"] for sheet in erc["sheets"])
                or any(drc[field] for field in ("violations", "unconnected_items", "schematic_parity"))):
            raise ValueError("The saved design still has ignored checks or outstanding violations.")
        netlist = root / "quote-netlist.xml"
        run("sch", "export", "netlist", "--format", "kicadxml", "-o", netlist, SCHEMATIC)
        if netlist_signature(netlist) != netlist_signature(saved_netlist):
            raise ValueError("Live CLI component/pin signature differs from the final sourcing netlist; refresh it and the BOM.")
        run("sch", "export", "pdf", "-o", pack / "Schematic.pdf", SCHEMATIC)
        run("pcb", "export", "gerbers", "-l", LAYERS, "--check-zones", "--no-protel-ext",
            "-o", gerbers, BOARD)
        run("pcb", "export", "drill", "--excellon-separate-th", "-o", gerbers, BOARD)
        plots = list(gerbers.glob("*.gbr"))
        drills = list(gerbers.glob("*.drl"))
        if len(plots) != len(LAYERS.split(",")) or not drills:
            raise ValueError("Missing copper, mask, paste, legend, outline or drill files.")
        with zipfile.ZipFile(pack / "Gerber-Drill.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for item in sorted(gerbers.iterdir()):
                archive.write(item, item.name)
        raw_pos = root / "pos.csv"
        run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
            "--exclude-dnp", "-o", raw_pos, BOARD)
        wanted = sourcing["roles"]["main"]
        positions = [r for r in read_rows(raw_pos) if r["Ref"] in wanted]
        if len(positions) != len(wanted) or {r["Ref"] for r in positions} != set(wanted):
            raise ValueError(f"BOM/CPL mismatch: {set(wanted) - {r['Ref'] for r in positions}}")
        for row in positions:
            if sourcing["sides"][row["Ref"]] != {"top": "F.Cu", "bottom": "B.Cu"}[row["Side"]]:
                raise ValueError(f"Saved CPL side differs from split BOM: {row['Ref']}")
        with (pack / "CPL-review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in positions:
                writer.writerow([row["Ref"], row["PosX"], row["PosY"],
                                 {"top": "Top", "bottom": "Bottom"}[row["Side"]], row["Rot"]])
        shutil.copyfile(bom, pack / "BOM-review.csv")
        if sha(pack / "BOM-review.csv") != before[bom.relative_to(ROOT).as_posix()]:
            raise RuntimeError("Main BOM changed while copying; no supplier pack released.")
        if source_hashes() != before:
            raise RuntimeError("Source changed during verification and export; retry after saving.")
        manifest = {"purpose": "supplier review and pricing", "fabrication_approved": False,
                    "physical_tests": 0, "source_sha256": before, "assembly_placements": len(wanted),
                    "origin": "KiCad absolute; bottom seen in common board coordinates",
                    "rotation": "KiCad native; compare pin 1 and polarity with vendor preview",
                    "sourcing_validation": sourcing,
                    "netlist_signature_sha256": hashlib.sha256(repr(netlist_signature(netlist)).encode()).hexdigest(),
                    "files": {p.name: sha(p) for p in pack.iterdir()}}
        # The supplier packet contains pricing and assembly inputs, keeping internal
        # budget worksheets and local verification receipts in the project.
        supplier_files = {
            pack / "Gerber-Drill.zip": "PCBA/Gerber-Drill.zip",
            pack / "CPL-review.csv": "PCBA/CPL-review.csv",
            pack / "BOM-review.csv": "PCBA/BOM-review.csv",
            pack / "Schematic.pdf": "PCBA/Schematic.pdf",
        }
        supplier_files.update(supplied)
        packet = pack / "Mini-Companion-RFQ.zip"
        with zipfile.ZipFile(packet, "w", zipfile.ZIP_DEFLATED) as archive:
            for src, name in supplier_files.items():
                archive.write(src, name)
        with zipfile.ZipFile(packet) as archive:
            if archive.testzip() is not None:
                raise ValueError("Corrupt quote packet.")
            for src, name in supplied.items():
                if hashlib.sha256(archive.read(name)).hexdigest() != before[src.relative_to(ROOT).as_posix()]:
                    raise RuntimeError(f"Supplied attachment changed during packaging: {name}")
        if source_hashes() != before:
            raise RuntimeError("Source changed while packaging; no supplier pack released.")
        manifest["files"][packet.name] = sha(packet)
        (pack / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        pack.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New supplier-review output directory")
    export(parser.parse_args().output.resolve())
