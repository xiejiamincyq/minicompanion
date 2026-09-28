"""Planning sensitivity only: neither a production BOM nor battery validation."""
from pathlib import Path
import json, hashlib
H=Path(__file__).resolve().parent
previous=json.loads((H.parent/'power-013/cost-summary.json').read_text(encoding='utf-8'))
active_hours=2*20/60
standby_hours=48-active_hours
base_W=3.18*.200
nfc_W=5*.06765
active_mAh=(base_W+nfc_W)/.85/3.7*1000*active_hours
out={
 'date':'2026-09-29','status':'conditional_candidate_not_selected',
 'library_revision':'63c4caac1a07018ef73027e4b098d4fefe56c6f6',
 'schematic_sha256':hashlib.sha256((H/'m5-u216-schematic.pdf').read_bytes()).hexdigest(),
 'module_price_USD':7,'domestic_quote_CNY':None,'complete_unit_cost':None,
 'fx_assumption_CNY_per_USD':7,'cost_scenarios':[],
 'energy_assumptions':{'active_hours_over_48h':active_hours,'standby_hours':standby_hours,
  'non_NFC_active_W':base_W,'NFC_reading_example_W':nfc_W,'conversion_efficiency':.85,
  'battery_nominal_V':3.7,'usable_capacity_fraction':.8,'active_battery_mAh':active_mAh},
 'capacity_scenarios':[],
 'limits':['Module current is vendor example, not maximum','Whole-system standby must include MCU polling and conversion losses',
  'No 5V converter selected','No physical battery or RF test','No domestic quantity quote','Additional components and assembly excluded']}
for s in previous['scenarios']:
 total=round(float(s['partial_USD'])+7,4)
 out['cost_scenarios'].append({'quantity':s['quantity'],'partial_with_U216_USD':total,'partial_CNY_at_assumed_7':round(total*7,4)})
for cap in (500,800,1000):
 out['capacity_scenarios'].append({'nominal_mAh':cap,'max_standby_battery_mA_under_assumptions':(cap*.8-active_mAh)/standby_hours})
(H/'assessment.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
