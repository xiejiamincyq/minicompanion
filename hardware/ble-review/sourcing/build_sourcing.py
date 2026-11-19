"""Rebuild an auditable RFQ BOM from a saved KiCad XML netlist, never CAD.

Usage: python build_sourcing.py
Quotes in source_snapshot are historical evidence, not current order prices.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "source_snapshot"
OUTPUT = HERE
CURRENT_NETLIST = HERE.parent / "verification" / "usb_eco.xml"
CURRENT_PCB = HERE.parent / "project" / "mini_companion_integrated.kicad_pcb"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows, fields=None):
    with (OUTPUT / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sort_ref(ref):
    return [(int(v) if v.isdigit() else v) for v in re.split(r"(\d+)", ref)]


def build(netlist, pcb=None):
    previous = {row["ref"]: row for row in read_csv(SNAPSHOT / "baseline_bom_by_ref.csv")}
    previous_by_mpn = {row["mpn"]: row for row in previous.values() if row["mpn"]}
    checks = json.loads((HERE / "primary_source_checks.json").read_text(encoding="utf-8"))
    catalog = {row["mpn"]: row for row in checks["components"]}
    xml = ET.parse(netlist)
    pin_nets = {(node.attrib["ref"], node.attrib["pin"]): net.attrib["name"]
                for net in xml.findall("./nets/net") for node in net.findall("node")}
    off_switch_nc = pin_nets.get(("SW7201", "3"), "").startswith("unconnected-")
    rows = []
    errors = []
    if netlist.resolve() == CURRENT_NETLIST.resolve() and not off_switch_nc:
        errors.append("Current POWER harness requires SW7201.3 NC; cannot export stale three-wire design")
    changes = []
    seen = set()
    for comp in xml.findall("./components/comp"):
        ref = comp.attrib["ref"]
        if ref in seen:
            errors.append(f"Duplicate reference: {ref}")
        seen.add(ref)
        old = previous.get(ref, {})
        fields = {f.attrib["name"]: f.text or "" for f in comp.findall("./fields/field")}
        props = {p.attrib["name"]: p.attrib.get("value", "") for p in comp.findall("property")}
        footprint = comp.findtext("footprint", "")
        value = comp.findtext("value", "")
        mpn = fields.get("MPN") or fields.get("MP") or fields.get("Manufacturer Part Number") or old.get("mpn", "")
        domain = fields.get("AssemblyDomain") or old.get("assembly_domain") or "main"
        feature = (ref.startswith(("TP", "H")) or mpn.startswith("SOLDER_PADS_") or "WirePads_" in footprint)
        excluded = "exclude_from_bom" in props
        category = "pcb_feature" if feature else "electronics"
        if excluded and not feature:
            category = "excluded_component"
        if "exclude_from_board" in props and domain == "main" and not feature:
            domain = "offboard"
        cnum = fields.get("LCSC") or fields.get("LCSC Part") or fields.get("LCSC Part #") or ""
        # Old supplement is valid only for the same exact MPN. Never transfer SKU across an ECO.
        if not cnum and mpn == old.get("mpn"):
            cnum = old.get("lcsc", "")
        check = catalog.get(mpn, {})
        if not cnum:
            cnum = check.get("lcsc", "")
        if cnum and check.get("lcsc") and cnum != check["lcsc"]:
            errors.append(f"SKU mismatch: {ref}: {cnum} vs verified {check['lcsc']}")
        maker = fields.get("Manufacturer") or fields.get("MANUFACTURER") or fields.get("MF") or check.get("manufacturer") or previous_by_mpn.get(mpn, {}).get("manufacturer", "")
        maker = {"Yageo":"YAGEO", "XKB":"XKB Connection"}.get(maker, maker)
        if category == "electronics" and not mpn:
            errors.append(f"Missing exact MPN: {ref}")
        if category == "electronics" and not maker:
            errors.append(f"Missing manufacturer: {ref}")
        row = dict(ref=ref, category=category, assembly_domain=domain, value=value, mpn=mpn,
                   manufacturer=maker, lcsc=cnum, footprint=footprint, qty_per_device=1,
                   quantity_two=2, unit="piece", source="saved_netlist",
                   stock_status=check.get("stock_status", "未取得本轮国内库存/采购报价"),
                   smt_catalog_status=check.get("smt_catalog_status", "待嘉立创按精确型号匹配"),
                   source_url=check.get("url", ""),
                   note="随PCB制作，不单买元件" if feature else old.get("requirement_note", ""))
        rows.append(row)
        if old and (mpn != old.get("mpn") or footprint != old.get("footprint")):
            changes.append({"ref": ref, "old_mpn": old.get("mpn"), "new_mpn": mpn,
                            "old_footprint": old.get("footprint"), "new_footprint": footprint})
        elif not old:
            changes.append({"ref": ref, "old_mpn": None, "new_mpn": mpn,
                            "old_footprint": None, "new_footprint": footprint})
    for ref, old in previous.items():
        if ref.startswith("EXT_"):
            # External supply/assembly scope is separate from the main-board placement BOM.
            row = {k: old.get(k, "") for k in rows[0]}
            row.update(source="baseline_external_scope_pending_final_mechanical_review",
                       stock_status="待完整报价", smt_catalog_status="板外采购或装配工序",
                       source_url="", note=old.get("requirement_note", ""))
            external_check = catalog.get(row["mpn"], {})
            if external_check:
                row.update(lcsc=external_check.get("lcsc", row["lcsc"]),
                           manufacturer=external_check.get("manufacturer", row["manufacturer"]),
                           stock_status=external_check["stock_status"],
                           smt_catalog_status=external_check["smt_catalog_status"],
                           source_url=external_check["url"])
            if ref == "EXT_CONSUMABLES":
                row["note"] = "代工商提供焊料/助焊剂/清洁剂并计入加工费；此行用于确认范围，不重复采购用户零售整包耗材"
            if ref == "EXT_PCB_ORDER":
                row["note"] = "按整批裸板报价（可评估5片只贴2片），整批费用计入两台；工艺边、钢网和双面SMT另列或注明已含，不能重复叠加材料现金旧账。"
            if ref == "EXT_PACK":
                row["note"] = "原厂FLYOUNG带PCM保护包；P+/P−接J610.1/.2，不接裸电芯。整包持续充放电上限1.5A，保留原厂引线；本轮精确MPN规格书已核，C5154898沿用历史采购记录，供方须再确认当前SKU/库存。"
            if ref == "EXT_SWITCH_HARNESS" and off_switch_nc:
                row.update(value="J7201 two-conductor POWER harness", mpn="TBD_TWO_WIRE_SWITCH_HARNESS",
                           unit="set of 2 wires", source="current_netlist_off_nc_external_scope",
                           note="两套共4根线；J7201.1→SW7201.1 PACK_POS，J7201.2→SW7201.2 POWER_REQUEST；SW7201.3悬空绝缘，J7201.3 GND空焊盘不接线。长度/线材/绝缘及代装价待最终装配图。")
            rows.append(row)
        elif ref not in seen:
            changes.append({"ref": ref, "old_mpn": old.get("mpn"), "new_mpn": None,
                            "old_footprint": old.get("footprint"), "new_footprint": None})
    rows.sort(key=lambda r: sort_ref(r["ref"]))
    write_csv("bom_by_ref.csv", rows)
    main = [r for r in rows if r["source"] == "saved_netlist" and r["category"] == "electronics" and r["assembly_domain"] == "main"]
    grouped = defaultdict(list)
    for row in main:
        grouped[(row["mpn"], row["manufacturer"], row["lcsc"], row["footprint"])].append(row)
    grouped_rows = []
    for (mpn, maker, cnum, footprint), members in sorted(grouped.items()):
        grouped_rows.append({"Comment": mpn, "Designator": ",".join(r["ref"] for r in members),
                             "Footprint": footprint, "LCSC Part #": cnum,
                             "Manufacturer": maker, "Quantity_Per_Board": len(members),
                             "Net_Quantity_Two": len(members) * 2,
                             "Purchase_Quantity_With_Process_Loss": "",
                             "Quote_Total_Two_CNY": "", "Status": "询价BOM；未锁库存；非生产放行"})
    write_csv("jlc_main_bom_rfq.csv", grouped_rows)
    board_receipt = None
    if pcb:
        # Read only saved KiCad text. Top-level footprint blocks have exactly one-tab indentation.
        board_text = pcb.read_text(encoding="utf-8-sig")
        board_parts = {}
        for block in re.finditer(r'^\t\(footprint "([^"\n]+)"\n(.*?)^\t\)', board_text, re.M | re.S):
            body = block.group(2)
            ref_match = re.search(r'^\t\t\(property "Reference" "([^"\n]+)"', body, re.M)
            layer_match = re.search(r'^\t\t\(layer "([FB]\.Cu)"\)', body, re.M)
            if ref_match and layer_match:
                ref = ref_match.group(1)
                if ref in board_parts:
                    errors.append(f"Duplicate board reference: {ref}")
                board_parts[ref] = {"footprint": block.group(1), "side": layer_match.group(1)}
        if not board_parts:
            errors.append("No saved board footprints parsed; side BOM is invalid")
        side_rows = []
        for row in main:
            placement = board_parts.get(row["ref"])
            if not placement:
                errors.append(f"Main BOM reference missing on saved board: {row['ref']}")
                continue
            if placement["footprint"] != row["footprint"]:
                errors.append(f"Footprint differs between netlist and PCB: {row['ref']}")
            side_rows.append({"ref":row["ref"],"side":placement["side"],"mpn":row["mpn"],
                              "lcsc":row["lcsc"],"footprint":placement["footprint"],
                              "quantity_two":2,"status":"当前保存态询价分工；非CPL；生产未放行"})
        write_csv("side_assembly_rfq.csv", side_rows,
                  ["ref","side","mpn","lcsc","footprint","quantity_two","status"])
        side_counts = {}
        for side, filename in [("F.Cu", "jlc_front_bom_rfq.csv"), ("B.Cu", "external_back_bom_rfq.csv")]:
            refs_on_side = {r["ref"] for r in side_rows if r["side"] == side}
            side_counts[side] = len(refs_on_side)
            group_on_side = []
            for group in grouped_rows:
                refs = [ref for ref in group["Designator"].split(",") if ref in refs_on_side]
                if refs:
                    part = dict(group)
                    part.update(Designator=",".join(refs), Quantity_Per_Board=len(refs), Net_Quantity_Two=len(refs)*2)
                    group_on_side.append(part)
            write_csv(filename, group_on_side, list(grouped_rows[0]))
        board_receipt = {"file":str(pcb.resolve()),"sha256":digest(pcb),
                         "main_components_by_side":side_counts,
                         "every_main_ref_has_one_side":len(side_rows)==len(main),
                         "purpose":"询价分工；不是贴片坐标；PCB布线/ERC/DRC由设计验收负责"}
    main_refs = [ref for row in grouped_rows for ref in row["Designator"].split(",")]
    if sorted(main_refs) != sorted(r["ref"] for r in main):
        errors.append("Grouped BOM lost or duplicated a main-board reference")
    for row in main:
        if not row["footprint"]:
            errors.append(f"Main-board item missing footprint: {row['ref']}")
    feature_rows = [r for r in rows if r["category"] in ("pcb_feature", "excluded_component")]
    write_csv("excluded_from_main_placement.csv", feature_rows)
    offboard = [r for r in rows if r["category"] not in ("pcb_feature", "excluded_component") and r not in main]
    write_csv("offboard_materials.csv", offboard)
    ledger = read_csv(SNAPSHOT / "historical_purchase_two_20261113.csv")
    historical = sum(Decimal(r["new_cash_two_cny"]) for r in ledger)
    expected = Decimal("499.726904")
    if historical != expected:
        errors.append(f"Historical ledger sum {historical} differs from {expected}")
    budget = json.loads((HERE / "budget_inputs.json").read_text(encoding="utf-8"))
    totals = [line["quoted_two_cny"] for line in budget["current_quote_lines"]]
    budget["current_complete_total_two_cny"] = str(sum(Decimal(str(n)) for n in totals)) if all(n is not None for n in totals) else None
    budget["historical_cash_two_cny"] = str(historical)
    budget["published_fee_sensitivity"] = {
        "kind": "旧材料现金加官方双面SMT收费示例；非当前报价、非完整费用区间",
        "historical_material_and_fabrication_cash": str(historical),
        "example_setup_two_sides": "300", "example_stencil_two_sides": "100",
        "subtotal_old_pcb_30": str(historical + Decimal(400)),
        "subtotal_old_pcb_100": str(historical + Decimal(470)),
        "still_excludes": ["焊点/上料/检验/双面加工实际附费", "外包线束和NTC探头加工", "总装/功能检查", "全部运费", "ECO净增减和时效价格变化"],
        "source_url": "https://www.jlc.com/portal/server_guide_4018.html"
    }
    (OUTPUT / "budget_model.json").write_text(json.dumps(budget, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "date_china": "2026-11-19", "deliverable": "RFQ_ONLY_NOT_ORDER_OR_FAB_RELEASE",
        "netlist_file": str(netlist.resolve()), "netlist_sha256": digest(netlist),
        "board_side_analysis": board_receipt,
        "power_harness": {"switch_pin3_is_nc": off_switch_nc,
                          "j7201_pin1": pin_nets.get(("J7201", "1")),
                          "j7201_pin2": pin_nets.get(("J7201", "2")),
                          "j7201_pin3_unwired_pad": pin_nets.get(("J7201", "3")),
                          "wire_count_per_device": 2 if off_switch_nc else 3},
        "source_snapshot_sha256": {p.name: digest(p) for p in sorted(SNAPSHOT.glob("*")) if p.is_file()},
        "netlist_components": len(seen), "main_board_fitted_per_unit": len(main),
        "main_grouped_bom_rows": len(grouped_rows),
        "external_electrical_refs": [r["ref"] for r in offboard if r["source"] == "saved_netlist"],
        "pcb_features_or_excluded": len(feature_rows),
        "main_refs_without_lcsc_id": [r["ref"] for r in main if not r["lcsc"]],
        "changes_from_20261113": changes,
        "checks": {"all_netlist_refs_unique": len(seen) == len(xml.findall("./components/comp")),
                   "grouped_quantities_and_refs_exact": sorted(main_refs) == sorted(r["ref"] for r in main),
                   "historical_cash_reconciles": historical == expected,
                   "unknown_current_quotes_remain_null": budget["current_complete_total_two_cny"] is None},
        "errors": errors, "data_validation_passed": not errors,
        "current_stock_verified": False, "supplier_quote_received": False,
        "physical_tests_performed": 0, "production_ready": False,
    }
    (OUTPUT / "sourcing_validation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("netlist_components", "main_board_fitted_per_unit", "main_grouped_bom_rows", "main_refs_without_lcsc_id", "data_validation_passed", "errors")}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", type=Path, default=CURRENT_NETLIST)
    parser.add_argument("--pcb", type=Path, default=CURRENT_PCB, help="Saved PCB for read-only side BOM split")
    parser.add_argument("--output-dir", type=Path, default=HERE, help="Separate output directory required for a historical comparison")
    args = parser.parse_args()
    OUTPUT = args.output_dir.resolve()
    if args.netlist.resolve() != CURRENT_NETLIST.resolve() and OUTPUT == HERE:
        parser.error("非当前网表必须显式指定独立 --output-dir；禁止历史输入覆盖当前询价文件")
    for required in (args.netlist, args.pcb):
        if not required.is_file():
            parser.error(f"找不到当前输入文件，未回退历史版本：{required}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build(args.netlist, args.pcb)
