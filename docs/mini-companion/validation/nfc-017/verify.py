"""Verify static UV candidate wiring and divider bounds, not transient safety."""
from pathlib import Path
import itertools,json,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'final.xml'); _,old=read(H.parent/'nfc-016/final.xml')
assert p==read(H/'before-format.xml')[1]
assert all(p[k]==('HOST_NFC_BUS_REQ' if k==('J4','3') else v) for k,v in old.items())
expected={'U3':['VLOGIC_SWITCHED','NFC_BUS_CONNECT','NFC_BUS_CONNECT','NFC_SENSE','GND','HOST_SENSE'],
 'R8':['HOST_NFC_BUS_REQ','NFC_BUS_CONNECT'],'R9':['VLOGIC_SWITCHED','HOST_SENSE'],
 'R10':['HOST_SENSE','GND'],'R11':['NFC_5V','NFC_SENSE'],'R12':['NFC_SENSE','GND'],
 'C4':['VLOGIC_SWITCHED','GND']}
def contract(pins):
 assert all(pins[ref,str(i+1)]==v for ref,ns in expected.items() for i,v in enumerate(ns))
 assert pins['J4','3']!=pins['U2','1']==pins['U2','4']==pins['U3','2']==pins['U3','3']
contract(p)
faults=[(('U3','3'),'HOST_NFC_BUS_REQ'),(('U3','4'),'HOST_SENSE'),(('R8','1'),'NFC_BUS_CONNECT'),(('R12','2'),'NFC_5V')]
for k,v in faults:
 bad=dict(p);bad[k]=v
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError('Fault not detected')
values={c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
assert len(values)==25 and len(p)==74
for ref,v in {'U3':'TPS3780ADBVR','R8':'10k 1%','R9':'15.8k 0.1%','R10':'10k 0.1%','R11':'29.4k 0.1%','R12':'10k 0.1%','C4':'100nF'}.items():assert values[ref]==v
lib=next(v for v in r.findall('./libparts/libpart') if v.attrib['part']=='TPS3780ADBVR')
pins={v.attrib['num']:v.attrib for v in lib.findall('./pins/pin')}
assert pins['2']['type']==pins['3']['type']=='open_collector'
assert [pins[str(i)]['name'] for i in range(1,7)]==['VDD','OUT1','OUT2','SENSE2','GND','SENSE1']
assert not any(s['violations'] for s in json.loads((H/'erc.json').read_text(encoding='utf-8'))['sheets'])
def bounds(top,threshold):
 vals=[threshold*t*(1+top*a/(10000*b))+leak*top*a for t,a,b,leak in itertools.product([.99,1.01],[.999,1.001],[.999,1.001],[-15e-9,15e-9])]
 return [min(vals),max(vals)]
rails={name:{'rise_V':bounds(top,1.194),'fall_V':bounds(top,1.188)} for name,top in [('host',15800),('nfc',29400)]}
assert rails['host']['rise_V'][1]<3.137544
assert rails['nfc']['rise_V'][1]<4.834
sink=3.222584/(10000*.99)
assert sink<.0004
report={'components':25,'pins':74,'ERC_violations':0,'injected_faults_detected':len(faults),
 'rails':rails,'request_max_sink_mA':sink*1000,
 'limits':['Threshold leakage uses +/-15nA specification at tested sense conditions; characterize intermediate bias',
 'GPIO VOH and SEL VIH corners remain to be validated; GPIO pin not assigned',
 '10us falling and 570us startup are typical, not guaranteed maxima',
 'Module internal 3.3V not sensed; not a complete brownout/backfeed guarantee',
 'No physical measurements, layout, mainboard integration or full cost approval']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
