"""Query the public JLC3DP dimensional price endpoint for this revision. No order endpoint."""
import datetime
import json
from pathlib import Path
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
parts = json.loads((root/'mechanical/geometry-check.json').read_text())['parts']
url = 'https://www.jlc-3dp.cn/3dp/modelPrintParameter/getMaterialInfo'
out = {'source':url,'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'scope':'per-file dimensional online estimate; no model uploaded; no finish or delivery', 'parts':[]}
totals = {}
for name,mesh in parts.items():
    size = [round(v/10,2) for v in mesh['size_mm']]
    count = mesh['quantity_for_two']
    inp = dict(materialTypeId=None,quantity=count,sizeX=size[0],sizeY=size[1],sizeZ=size[2],modelVolume=round(mesh['volume_cm3'],2))
    req = Request(url,data=json.dumps(inp).encode(),headers={'Content-Type':'application/json','Referer':'https://www.jlc-3dp.cn/placeOrder','User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=25) as response:
        reply = json.load(response)
    assert reply['code']==200
    materials = {}
    for group in reply['data']:
        for row in (group.get('quotationMaterialVOList') or []):
            mat=row['materialName']
            if mat not in ('9000HE','Grey','9600') or row['disableFlag'] or row['manualQuotationFlag']: continue
            line = round(float(row['price'])*count,2)
            materials[mat] = dict(unit_cny=row['price'],line_cny=line,lead_hours=row['quotationDeliveryVO']['deliveryDate'])
            totals[mat]=round(totals.get(mat,0)+line,2)
    assert '9000HE' in materials and 'Grey' in materials, name
    out['parts'].append(dict(part=name,sha256=mesh['sha256'],request=inp,materials=materials))
out['total_cny_by_material'] = totals
(root/'verification/enclosure-web-quote.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(totals)
