"""Rebuild A2 sourcing only from this worktree's current netlist.

No network, no CAD mutation. Price observations are not purchase commitments.
Run: python hardware/ble-economy/sourcing/build_sourcing.py
"""
from pathlib import Path
from collections import defaultdict
from decimal import Decimal
import csv
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def dump_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def loss_count(unit_price, pin_count, library):
    if library == 'base':
        return 0
    if unit_price is None or pin_count is None:
        return None
    p = Decimal(str(unit_price))
    if pin_count > 8 or p >= 1:
        return 0
    limits = [(Decimal('.1'), 10), (Decimal('.2'), 8), (Decimal('.5'), 4), (Decimal('1'), 2)] if pin_count <= 2 else [(Decimal('.2'), 5), (Decimal('.5'), 4), (Decimal('1'), 2)]
    return next(n for limit, n in limits if p < limit)


def main():
    source = ROOT / 'verification/a2_netlist.xml'
    board = ROOT / 'project/mini_companion_a2.kicad_pcb'
    for p in (source, board):
        if not p.is_file():
            raise SystemExit(f'缺少本版必需输入，停止，不回退到旧版本: {p}')
    prices = json.loads((HERE / 'price_evidence.json').read_text('utf-8'))
    tree = ET.parse(source).getroot()
    groups = defaultdict(list)
    by_ref = []
    for comp in tree.findall('components/comp'):
        fields = {f.get('name'): f.text or '' for f in comp.findall('fields/field')}
        row = {'Ref': comp.get('ref'), 'Value': comp.findtext('value'), 'MPN': fields.get('MPN'),
               'LCSC': fields.get('LCSC'), 'Manufacturer': fields.get('Manufacturer'),
               'Footprint': comp.findtext('footprint') or fields.get('Footprint'),
               'AssemblyDomain': fields.get('AssemblyDomain')}
        if not row['MPN'] or not row['LCSC']:
            raise SystemExit(f'采购字段缺失，拒绝静默导出: {row}')
        by_ref.append(row)
        groups[(row['AssemblyDomain'], row['LCSC'], row['MPN'], row['Footprint'])].append(row)

    grouped, missing, net_cost, loss_cost = [], [], Decimal(0), Decimal(0)
    extension_count = 0
    main_skus = 0
    for (domain, code, mpn, footprint), comps in sorted(groups.items()):
        obs = prices['parts'].get(code, {})
        if obs.get('mpn') and obs['mpn'] != mpn:
            raise SystemExit(f'MPN/C号与核验记录矛盾: {code}: {mpn} != {obs["mpn"]}')
        unit = obs.get('smt_unit_1plus_cny')
        library = obs.get('library', 'unknown')
        n = len(comps) * 2
        loss = loss_count(unit, obs.get('pins_for_loss'), library) if domain == 'main' else None
        if domain == 'main':
            main_skus += 1
            extension_count += library == 'expand'
            if unit is None or loss is None:
                missing.append(code)
            else:
                net_cost += n * Decimal(str(unit))
                loss_cost += (n + loss) * Decimal(str(unit))
        grouped.append({'References': ','.join(c['Ref'] for c in comps), 'MPN': mpn, 'LCSC': code,
                        'Manufacturer': comps[0]['Manufacturer'], 'Footprint': footprint,
                        'Domain': domain, 'PerBoard': len(comps), 'NetQtyTwo': n,
                        'Library': library, 'SMT1plusCNY': '' if unit is None else unit,
                        'PublishedLossQty': '' if loss is None else loss,
                        'QtyBeforeMachineMinimum': '' if loss is None else n + loss,
                        'MaterialSubtotalBeforeMachineMinimum': '' if unit is None or loss is None else str((n + loss) * Decimal(str(unit))),
                        'StockObserved': obs.get('smt_stock', ''),
                        'Status': obs.get('status', 'NEEDS_VERIFICATION'),
                        'Source': obs.get('smt_url', obs.get('retail_url', ''))})

    dump_csv(HERE / 'BOM_逐位号.csv', by_ref)
    dump_csv(HERE / 'BOM_合并采购.csv', grouped)
    dump_csv(HERE / 'BOM_JLC_顶面.csv', [
        {'Comment': r['MPN'], 'Designator': r['References'], 'Footprint': r['Footprint'], 'LCSC Part #': r['LCSC']}
        for r in grouped if r['Domain'] == 'main'])
    receipt = {
        'status': 'QUOTE_MODEL_NOT_ORDER_NOT_MANUFACTURING_RELEASE',
        'netlist_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'pcb_sha256_at_bom_generation': hashlib.sha256(board.read_bytes()).hexdigest(),
        'main_components_per_board': sum(r['AssemblyDomain'] == 'main' for r in by_ref),
        'offboard_components_per_unit': sum(r['AssemblyDomain'] != 'main' for r in by_ref),
        'main_unique_skus': main_skus, 'economic_extension_skus': extension_count,
        'unpriced_main_skus': missing,
        'known_main_net_material_cny_two': str(net_cost),
        'known_main_material_with_published_loss_before_machine_minimum_cny': str(loss_cost),
        'economic_engineering_plus_feeding_cny': 50 + 20 * extension_count,
        'economic_nitrogen_cny_two': 5.2,
        'physical_smd_pads_per_board_at_design_review': 115,
        'solder_joint_model_cny_two': 2.3,
        'xray_model_cny_two_wson_devices': 20,
        'standard_engineering_stencil_plus_all_sku_feeding_cny': 150 + 50 + 8 * main_skus,
        'notes': [
            '本表不是完整报价：最小上机量、两个缺价SKU、X-ray、焊点、包装、工艺边、邮费另计。',
            '扩展料损耗按公开小量表试算；官方规定单价基于立创商城，最终使用列可覆盖本模型。',
            '标准型用全SKU上料收费作保守可比模型；实际基础料是否计费应以整单匹配核准。',
            '标准型最小70x70；68x35单板加到80x75外框已在线估价5片30元，具体拼边/铣桥/接单仍待工厂核准。',
            '115点/片和WSON X-ray是费用模型；最终订单识别点数、收费项目及最小收费优先。',
            '板外NTC仅归属线束采购，绝不自动送机器贴装。']}
    (HERE / 'cost_model_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps(receipt, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
