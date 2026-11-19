"""Partial quote subtotal; missing BOM lines must never be treated as free."""
from pathlib import Path
import csv,json
from decimal import Decimal
H=Path(__file__).resolve().parent
rows=list(csv.DictReader((H/'product-price-anchors.csv').open(encoding='utf-8-sig')))
parts=['ESP32-S3-MINI-1-N4R2','HS20HS072RX','BQ24072TRGTR','TPS63802DLAR','TPS259470LRPWR']
out={'quote_date':'2026-09-28','illustrative_CNY_per_USD':7,'exchange_rate_is_live_quote':False,'scenarios':[],
 'excluded_unquoted':['other six power ICs','passives','battery','NFC alternative','connectors','PCB','assembly','enclosure','shipping/tax'],
 'complete_unit_cost':None,'budget_compliance':'not_demonstrated'}
for quantity,tier in [(5,'1'),(10,'10')]:
 prices={r['manufacturer_part']:Decimal(r['unit_price_usd']) for r in rows if r['quantity_break']==tier}
 subtotal=sum(prices[p] for p in parts)
 with_nfc=subtotal+prices['NFC_PN7160_I2C']
 out['scenarios'].append(dict(quantity=quantity,quoted_five_parts=parts,partial_USD=str(subtotal),
 partial_CNY_at_assumed_7=str(subtotal*7),with_reference_NFC_USD=str(with_nfc),
 with_reference_NFC_CNY_at_assumed_7=str(with_nfc*7)))
(H/'cost-summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
