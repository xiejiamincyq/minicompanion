"""Independent pin contract, unchanged parent circuitry and conditional budget."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'power-006'))
from verify_system import read
root,p=read(HERE/'system-final.xml')
_,old=read(HERE.parent/'power-007/system-final.xml')
assert all(p.get(k)==v for k,v in old.items()),'Parent circuit changed'
def contract(p):
 expected={1:'BL_ISET',4:'LED_K',5:'LED_K',6:'LED_K',7:'GND',8:'LED_A',9:'BL_C2P',10:'BL_C1P',11:'BL_C1N',12:'BL_C2N',13:'VLOGIC_SWITCHED',14:'GND',15:'BL_PWM',16:'BL_PWM',17:'GND'}
 for pin,net in expected.items():
  assert p['U2',str(pin)]== (net if net in ['GND','VLOGIC_SWITCHED'] else 'backlight/'+net),(pin,net)
 for ref,nets in {'C4':['VLOGIC_SWITCHED','GND'],'C5':['LED_A','GND'],'C6':['BL_C1P','BL_C1N'],'C7':['BL_C2P','BL_C2N'],'R6':['BL_ISET','GND'],'R7':['BL_PWM','GND'],'J3':['LED_A','LED_K'],'J4':['BL_PWM','GND']}.items():
  for pin,net in enumerate(nets,1):assert p[ref,str(pin)]==(net if net in ['GND','VLOGIC_SWITCHED'] else 'backlight/'+net),(ref,pin)
 for pin in [2,3]: assert p['U2',str(pin)].startswith('unconnected-')
contract(p)
bad=dict(p);bad['J3','1'],bad['J3','2']=bad['J3','2'],bad['J3','1']
try:contract(bad)
except AssertionError:pass
else:raise AssertionError('LED polarity fault escaped')
v={c.attrib['ref']:c.findtext('value') for c in root.findall('./components/comp')}
assert v['R6']=='8.06k 1%' and v['R7']=='10k'
assert len(v)==22
erc=json.loads((HERE/'erc.json').read_text(encoding='utf-8'))
assert not any(s['violations'] for s in erc['sheets'])
nom=3*.6*260/8060
low=3*.580*230/(8060*1.01);high=3*.620*280/(8060*.99)
report={'status':'review_only','components':len(v),'ERC_violations':0,'parent_pin_contract':'unchanged','backlight_pin_contract':'pass','LED_polarity_fault_detected':True,'nominal_LED_mA':nom*1000,'conditional_LED_mA_range':[low*1000,high*1000],'nominal_1p5x_rail_mA':(1.5*nom+.0021)*1000,'engineering_rail_reserve_mA':110,'limitations':['Current calculation uses datasheet table conditions; not a full voltage/temperature guarantee','Capacitor effective values, footprint mechanical audit, PWM/rail transient and shutdown behavior pending','No PCB routing or physical measurements']}
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
