"""Extract a review BOM, excluding interface placeholders from production counts."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent
source=H/'system-final.xml'
root=ET.parse(source).getroot()
rows=[]
for c in root.findall('./components/comp'):
 ref=c.attrib['ref'];sheet=c.find('sheetpath').attrib['names']
 role='review_interface' if ref.startswith('J') and ref!='J102' else 'candidate_component'
 if ref=='J102':role='battery_connector_unselected'
 rows.append(dict(reference=ref,value=c.findtext('value'),sheet=sheet,quantity=1,role=role,
                  footprint=c.findtext('footprint') or '',unit_price_usd='',price_status='unquoted'))
assert len(rows)==74
assert sum(r['role']=='review_interface' for r in rows)==11
with (H/'candidate_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
summary=dict(source=str(source.relative_to(H.parents[3])),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 schematic_components=len(rows),review_interface_placeholders=11,remaining_candidate_positions=63,
 IC_count=sum(r['reference'].startswith('U') for r in rows),
 per_sheet=dict(Counter(r['sheet'] for r in rows)),
 excluded_from_scope=['ESP32 module','display assembly','NFC','battery pack','main-board support components','PCB','assembly','enclosure','shipping/taxes'],
 warning='63 is not a released manufacturing BOM; missing prices remain empty, never zero.')
(H/'inventory-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
