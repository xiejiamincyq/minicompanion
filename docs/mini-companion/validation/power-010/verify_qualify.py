"""Static pin contract and TI truth table; explicitly excludes undefined rails."""
from pathlib import Path
from itertools import product
import json,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'system-final.xml');oldr,old=read(H.parent/'power-009/system-final.xml')
assert all(p.get(k)==v for k,v in old.items())
assert p==read(H/'before-format.xml')[1]
def contract(p):
 expected={'U5':['USB_READY','GND','USB_3V3','RESET_CT','USB_3V3','USB_3V3'],
 'U6':['USB_READY','GND','GND','CC_HIGH_QUALIFIED','USB_3V3','CC_OUT1'],
 'C11':['USB_3V3','GND'],'C12':['USB_3V3','GND'],'C13':['RESET_CT','GND'],
 'R11':['USB_3V3','USB_READY'],'R12':['CC_HIGH_QUALIFIED','GND'],
 'J7':['CC_HIGH_QUALIFIED','USB_READY','GND']}
 for ref,nets in expected.items():
  assert [p[ref,str(i)] for i in range(1,len(nets)+1)]==nets,ref
contract(p)
bad=dict(p);bad['U6','1'],bad['U6','6']=bad['U6','6'],bad['U6','1']
try:contract(bad)
except AssertionError:pass
else:raise AssertionError('Swapped mux inputs escaped')
v={c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
ov={c.attrib['ref']:c.findtext('value') for c in oldr.findall('./components/comp')}
assert {k:(ov[k],v[k]) for k in ov if v[k]!=ov[k]}=={'R9':('200k 1%','10k 1%')}
assert v['U5']=='TPS3808G33DBVR' and v['U6']=='SN74LVC1G97DBVR'
assert v['C13']=='180nF 5% 10V' and v['R11']=='100k 1%' and v['R12']=='10k 1%'
assert len(v)==40
# TI table 1, ordered In2/In1/In0, transcribed independently of the netlist.
table={(0,0,0):0,(0,0,1):0,(0,1,0):1,(0,1,1):1,(1,0,0):0,(1,0,1):1,(1,1,0):0,(1,1,1):1}
rows=[]
for ready,out1,out2 in product([0,1],repeat=3):
 y=table[out1,ready,0]
 assert y==int(ready==1 and out1==0)
 rows.append({'USB_READY':ready,'OUT1':out1,'OUT2':out2,'candidate':y})
e=json.loads((H/'erc.json').read_text(encoding='utf-8'));assert not any(s['violations'] for s in e['sheets'])
report={'status':'qualification_candidate_not_final_charger_control','components':len(v),'ERC_violations':0,'existing_pin_connections':'unchanged','existing_value_change':'R9 200k to 10k','pin_contract_and_mux_swap_fault':'pass','valid_rail_truth_table':rows,'G33_falling_threshold_V':[3.07*.985,3.07*1.015],'receiver_only_CC_pullup_drop_V':5e-6*10100,'RESET_pullup_drop_V':5.3e-6*101000,'limitations':['No logic guarantee for supply below 1.65V','180nF datasheet delays do not include selected capacitor corners','TUSB initialization worst-case not established','Default USB and BC1.2 not implemented; output not connected to charger EN']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
