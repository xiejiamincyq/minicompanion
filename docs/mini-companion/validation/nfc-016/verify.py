"""Bus-switch wiring checks; not transient, firmware or hardware validation."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'final.xml');oldr,old=read(H.parent/'nfc-015/final.xml')
assert p==read(H/'before-format.xml')[1], 'Formatting altered nets'
assert all(p[k]==v for k,v in old.items()), 'Old boost circuit altered'
expected={'U2':['NFC_BUS_CONNECT','HOST_SDA','NFC_SDA','NFC_BUS_CONNECT','HOST_SCL','NFC_SCL',
 'GND','GND','GND','GND','GND','GND','GND','VLOGIC_SWITCHED'],
 'C3':['VLOGIC_SWITCHED','GND'],'R5':['NFC_BUS_CONNECT','GND'],
 'R6':['VLOGIC_SWITCHED','HOST_SDA'],'R7':['VLOGIC_SWITCHED','HOST_SCL'],
 'J4':['HOST_SDA','HOST_SCL','NFC_BUS_CONNECT','GND'],'J5':['NFC_SCL','NFC_SDA','NFC_5V','GND']}
def contract(pins):
 assert all(pins[ref,str(i+1)]==net for ref,ns in expected.items() for i,net in enumerate(ns))
 assert pins['U2','2']!=pins['U2','3'] and pins['U2','5']!=pins['U2','6']
contract(p)
for pin,net in [(('U2','3'),'HOST_SDA'),(('R5','2'),'VLOGIC_SWITCHED'),(('J5','3'),'VLOGIC_SWITCHED')]:
 bad=dict(p);bad[pin]=net
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError('Fault not detected')
values={c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
assert len(values)==18 and len(p)==56
assert values['U2']=='TMUX1511PWR' and values['R5']=='100k 1%'
assert values['R6']==values['R7']=='4.7k 1%'
assert not any(s['violations'] for s in json.loads((H/'erc.json').read_text(encoding='utf-8'))['sheets'])
rp=1/(1/4700+1/2200)
sink=3.222584/(4700*.99)+3.3/(2200*.99)
report={'status':'conditional_bus_disconnect_candidate','components':18,'pins':56,'old_pins_unchanged':len(old),
 'ERC_violations':0,'injected_faults_detected':3,
 'nominal_parallel_pullup_ohm':rp,'conditional_100pF_rise_ns':.8473*rp*100e-12*1e9,
 'conditional_total_sink_mA_at_zero_V':sink*1000,'conditional_switch_drop_mV':sink*4.5*1000,
 'assumptions':['Module pullups 2.2k, assumed 1 percent','Module 3.3V nominal only, not tolerance bound',
 '100pF is an example total capacitance, not measured','Switch RON 4.5 ohm used for estimate'],
 'limits':['Bus-connect must go low before NFC-enable; firmware not implemented',
 'No automatic detection of NFC rail collapse','No protection guarantee during partial supply or brownout',
 'Powered-off isolation applies at VDD=0 within datasheet signal limits, not galvanic isolation',
 'Module/MCU voltage corners, rise time and leakage not physically validated','No complete cost or mainboard integration']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
