"""Pin contract and conditional DC calculations, not hardware validation."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'final.xml')
assert p==read(H/'before-format.xml')[1], 'Cosmetics changed connectivity'
expected={'U1':['NFC_FB','NFC_ENABLE','VLOGIC_SWITCHED','GND','NFC_SW','NFC_5V'],
 'L1':['VLOGIC_SWITCHED','NFC_SW'],'C1':['VLOGIC_SWITCHED','GND'],'C2':['NFC_5V','GND'],
 'R1':['NFC_5V','NFC_FB'],'R2':['NFC_FB','GND'],'R3':['NFC_ENABLE','GND'],'R4':['NFC_5V','GND'],
 'J1':['VLOGIC_SWITCHED','GND'],'J2':['NFC_ENABLE','GND'],'J3':['NFC_5V','GND']}
def contract(pins):
 assert pins=={(ref,str(i+1)):net for ref,ns in expected.items() for i,net in enumerate(ns)}
contract(p)
for pin,badnet in [(('U1','3'),'SYS_RAW'),(('R2','2'),'NFC_5V'),(('R3','2'),'VLOGIC_SWITCHED')]:
 bad=dict(p);bad[pin]=badnet
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError('Fault not detected')
values={c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
assert len(values)==11 and values['R1']=='75k 0.1%' and values['R2']=='10.2k 0.1%'
erc=json.loads((H/'erc.json').read_text(encoding='utf-8'))
assert not any(s['violations'] for s in erc['sheets'])
vmin=.580*(1+75000*.999/(10200*1.001))
vmax=.610*(1+75000*1.001/(10200*.999))
active_h=2/3;standby_h=48-active_h
active_mAh=(3.18*.2/.85+5*.06765/(.85*.85))/3.7*1000*active_h
report={'status':'independent_candidate_only','components':11,'review_connectors':3,'pins':len(p),
 'ERC_violations':0,'injected_faults_detected':3,'nominal_PWM_V':.595*(1+75000/10200),
 'PWM_reference_and_resistor_only_V':[vmin,vmax],
 'conditional_25C_FB_leakage_magnitude_V':20e-9*75000*1.001,
 'NFC_input_A_at_3_137544V_85pct':{str(i):5*i/(3.137544*.85) for i in [.06765,.15,.3]},
 'two_stage_active_battery_mAh':active_mAh,
 'standby_max_mA_500mAh_under_assumptions':(500*.8-active_mAh)/standby_h,
 'standby_max_mA_800mAh_under_assumptions':(800*.8-active_mAh)/standby_h,
 'converter_IC_quote_USD_at_5_and_10_units':.2487,
 'limits':['PWM calculation excludes PFM ripple and transients','20nA leakage limit is 25C only; not a full-temperature bound',
 'Input current scenarios are not module maximum ratings','Enable policy and GPIO unassigned',
 'No I2C isolation or module connected','Effective capacitance, inductor, footprints, thermals and startup not released',
 'Domestic quote and full cost unknown','No physical test']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
