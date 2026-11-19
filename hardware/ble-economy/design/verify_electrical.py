"""Check the native KiCad XML against the electrical interface and calculate corners.

No CAD mutation. This is static evidence, never a substitute for prototype tests.
Run after exporting a2_netlist.xml from the saved schematic with KiCad CLI.
"""
from pathlib import Path
import hashlib, itertools, json, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / 'verification/a2_netlist.xml'
CONTRACT = ROOT / 'design/electrical_contract.json'
doc = ET.parse(XML).getroot()
components = {c.attrib['ref']: c for c in doc.findall('components/comp')}
nets = {}
for net in doc.findall('nets/net'):
    for node in net.findall('node'):
        pin = (node.attrib['ref'], node.attrib['pin'])
        assert pin not in nets, ('duplicate pin', pin)
        nets[pin] = net.attrib['name']

def conn(ref, pin, net):
    assert nets.get((ref, str(pin))) == net, (ref, pin, net, nets.get((ref, str(pin))))

def field(ref, name):
    f = components[ref].find(f'fields/field[@name="{name}"]')
    return '' if f is None else f.text or ''

expected = [c for c in json.loads(CONTRACT.read_text(encoding='utf-8'))['components'] if not c['ref'].startswith('#')]
assert set(components) == {c['ref'] for c in expected}
for c in expected:
    ref = c['ref']
    for key, name in [('mpn','MPN'),('lcsc','LCSC'),('domain','AssemblyDomain')]:
        assert field(ref, name) == c[key], (ref, name)
    assert (components[ref].findtext('footprint') or '') == c['footprint'], ref
    for pin, net in c['pins'].items():
        if net is None:
            actual = nets.get((ref, pin), '')
            assert not actual or actual.startswith('unconnected-'), (ref, pin, actual)
        else:
            conn(ref, pin, net)

# Independently reviewed physical contracts: these catch a wrong generator edit.
critical = {
    'U1': {1:'DC_PROTECTED',2:'CHG_ISET',3:'NTC_TS',4:'GND',5:'CHG_STAT',7:'CHG_VSET',8:'PACK_POS',9:'GND'},
    'U2': {1:'BOOST_FB',2:'RUN_EN',3:'PACK_POS',4:'GND',5:'BOOST_SW',6:'RUN_5V'},
    'U3': {1:'GND',2:'RUN_EN',3:'UVLO_VDD'},
    'Q1': {1:'PLUG_SENSE',2:'GND',3:'RUN_EN'},
    'Q2': {1:'CORE_SENSE_GATE',2:'GND',3:'NTC_TS'},
    'Q3': {1:'PMOS_GATE',2:'DC_PROTECTED',3:'DC_RAW'},
    'D3': {1:'DC_PROTECTED',2:'PMOS_GATE'},
    'D2': {1:'LED_ANODE',2:'CHG_STAT'},
    'J1': {1:'DC_RAW',2:'GND',3:'PLUG_SENSE'},
    'J2': {1:'PACK_POS',2:'GND',3:'NTC_TS',4:'GND'},
    'J4': {1:'RUN_5V',2:'GND'},
    'J5': {1:'GND',2:'KEY_A',3:'KEY_B',4:'KEY_C',5:'CORE_5V_SENSE'},
    'SW4': {1:'PACK_POS',2:'RUN_REQUEST','SH':'GND'},
}
for ref, pins in critical.items():
    for pin, net in pins.items(): conn(ref,pin,net)
assert nets.get(('SW4','3'),'').startswith('unconnected-')
for i, key in enumerate(['KEY_A','KEY_B','KEY_C'],1):
    assert {p for p, n in nets.items() if n == key} == {(f'SW{i}','1'),('J5',str(i+1))}
    conn(f'SW{i}',2,'GND')
assert {p for p,n in nets.items() if n == 'CORE_5V_SENSE'} == {('J5','5'),('R3','1')}
assert not ({'VBAT','BAT','3V3'} & set(nets.values())), 'Forbidden core power connection'
assert field('R1','LCSC') == 'C23147'
assert field('Q1','MPN') == field('Q2','MPN') == 'AO3400A'
assert field('D2','MPN') == 'KT-0603R'
assert field('TH1','MPN') == 'HNTC-103F3950FB-100B'
assert field('R6','MPN') == '0603WAF2203T5E' and field('R6','LCSC') == 'C22961'
assert field('R7','MPN') == '0603WAF3002T5E' and field('R7','LCSC') == 'C22984'
for el in doc.iter():
    if el.tag in {'source','uri'} and el.text:
        assert not re.match(r'^(?:[A-Za-z]:[\\/]|[\\/])',el.text), ('nonportable metadata',el.tag)

def ohms(ref):
    s=components[ref].findtext('value').split()[0]
    v=re.fullmatch(r'([0-9.]+)([kM]?)',s)
    assert v,s
    return float(v[1])*{'':1,'k':1000,'M':1000000}[v[2]]

# Full ambient drift allowance for ordinary 1% / 100ppm/K resistors: +/-2%.
# Vref limits are the PWM specification; PFM/light-load behavior needs measuring.
rtol=.02
vout=[v*(1+ohms('R6')*a/(ohms('R7')*b)) for v,a,b in itertools.product([.580,.610],[1-rtol,1+rtol],[1-rtol,1+rtol])]
vo_min,vo_max=min(vout),max(vout)
vnom=.595*(1+ohms('R6')/ohms('R7'))
assert ohms('R7')*(1+rtol)<300000 # TI section 8.2.2.1 recommendation.
divider_min_A=.580/(ohms('R7')*(1+rtol))
assert divider_min_A>100*20e-9 # 20 nA maximum FB leakage is specified at 25 C only.
divider={
    'top_ohm':ohms('R6'),'bottom_ohm':ohms('R7'),
    'nominal_output_load_A':.595/ohms('R7'),
    'added_output_load_vs_previous_750k_102k_A':.595/ohms('R7')-.595/102000,
    'maximum_bottom_ohm_with_tolerance':ohms('R7')*(1+rtol),
    'minimum_divider_current_A':divider_min_A,
    'ratio_to_FB_20nA_at_25C_limit':divider_min_A/20e-9,
    'nominal_PFM_reference_output_V':.601*(1+ohms('R6')/ohms('R7')),
    'source':'https://www.ti.com/lit/ds/symlink/tps61023.pdf',
    'review':'Section 8.2.2.1 recommends bottom <300k; no minimum resistance specified. Lower resistance trades extra load for noise immunity. Internal compensation and unchanged L/C do not by themselves prove dynamic stability. PFM reference has no guaranteed maximum; output ripple/overshoot and load steps remain physical acceptance items.'
}
fall=[]; rise=[]; off=[]; hysteresis=[]
for a,b,c,d,vt,iq,hys in itertools.product([.98,1.02],[.98,1.02],[.98,1.02],[.98,1.02],[3.08*.98,3.08*1.02],[0,1.2e-6],[.009,.015]):
    r12,r13,r14,r8=ohms('R12')*a,ohms('R13')*b,ohms('R14')*c,ohms('R8')*d
    # Off VOUT is NOT zero: R13 feeds it, and R8 discharges it. Other loads lower it.
    off.append(4.2/(r12+(1/(1/r14+1/(r13+r8))))*(1/(1/r14+1/(r13+r8)))*r8/(r13+r8))
    vr=vt*(1+hys)*(1+r12/r14+r12/(r13+r8))+iq*r12
    rise.append(vr)
    for vo in [vo_min,vo_max]:
        vf=vt*(1+r12/r13+r12/r14)-vo*r12/r13+iq*r12
        fall.append(vf);hysteresis.append(vr-vf)
assert min(fall)>3.0 and max(rise)<3.5
assert max(off)<.15
assert vo_max<5.5

# Manufacturer R-T min/typ/max transcription, C52204609 PDF p4.
table={0:(32045,32755,33477),1:(30465,31124,31795),2:(28973,29585,30206),3:(27562,28130,28707),4:(26229,26756,27290),5:(24967,25456,25952),40:(5228,5315,5402),41:(5020,5105,5191),42:(4821,4905,4989),43:(4631,4713,4796),44:(4449,4530,4612),45:(4276,4355,4435)}
def temp_at(r,idx):
    for (t,v),(tt,vv) in zip(sorted(table.items()),sorted(table.items())[1:]):
        if v[idx]>=r>=vv[idx]: return t+(tt-t)*(v[idx]-r)/(v[idx]-vv[idx])
    return None

bias=json.loads((ROOT/'design/capacitor_bias_evidence.json').read_text())['CL21A226MAQNNN']['deltaC_percent']
caps={
    'C2_typical_at_4V2_uF':22*(1+bias['4.2']/100),
    'C4_C5_typical_at_5V3_uF':44*(1+bias['5.3']/100),
    'C2_estimate_with_initial20pct_temp15pct_and_assumed10pct_age_uF':22*(1+bias['4.2']/100)*.8*.85*.9,
    'C4_C5_same_estimate_uF':44*(1+bias['5.3']/100)*.8*.85*.9,
    'limitation':'Typical manufacturer bias curve; 10% ageing is a design allowance, not a guaranteed lifetime model. Validate actual supply ripple/startup.'
}
assert caps['C2_estimate_with_initial20pct_temp15pct_and_assumed10pct_age_uF']>4.7
assert caps['C4_C5_same_estimate_uF']>10

result={
    'status':'STATIC_CHECKS_PASS_PHYSICAL_ACCEPTANCE_PENDING',
    'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [XML,ROOT/'project/mini_companion_a2.kicad_sch',CONTRACT]},
    'component_count':{'board':sum(field(r,'AssemblyDomain')=='main' for r in components),'offboard':sum(field(r,'AssemblyDomain')=='battery_probe' for r in components)},
    'boost_divider':divider,
    'boost':{'PWM_nominal_V':vnom,'PWM_static_corners_V':[vo_min,vo_max],'rated_design_load_A':.5,'battery_input_at_0V6A_output_3V0_input_80pct_assumed_efficiency_A':vo_max*.6/(3*.8),'limit':'0.5 A continuous design target; efficiency, startup and transient current are unmeasured. Not a hardware battery current limiter; pack PCM remains mandatory.'},
    'uvlo':{'falling_pack_V':[min(fall),max(fall)],'rising_pack_V':[min(rise),max(rise)],'same_corner_hysteresis_V':[min(hysteresis),max(hysteresis)],'off_RUN_5V_residual_max_from_feedback_V':max(off),'delay_ms':[130,270],'low_EN_sink_demand_max_A':4.2/(ohms('R9')*.98),'limit':'Steady-state resistor model; battery rebound, ramps and dynamic sequencing need scope validation.'},
    'charge':{'set_voltage_corners_V':[4.1*.992,4.1*1.008],'current_corners_A':[270/(ohms('R2')*1.02),330/(ohms('R2')*.98)],'fast_timer_hours':[9.5,10.5],'precharge_timer_minutes':[28.5,31.5],'input_acceptance':'4.75–5.25 V at J1 under 0.35 A; verify DC_PROTECTED >=4.60 V. 5V >=1A wall adapter only.'},
    'NTC':{'nominal_cold_trip_C':temp_at(1.04/38e-6,1),'nominal_hot_trip_C':temp_at(.188/38e-6,1),'zero_leak_initial_worst_cold_trip_C':temp_at(1.09/36.5e-6,0),'zero_leak_initial_worst_hot_trip_C':temp_at(.176/39.5e-6,2),'initial_cold_0C_voltage_min_V':36.5e-6*table[0][0],'initial_hot_45C_voltage_max_V':39.5e-6*table[45][2],'cold_0C_with_5uA_clamp_leak_V':(36.5e-6-5e-6)*table[0][0],'limitation':'No full lifetime/coupling guarantee. Actual two finished units must each inhibit at +2 C and +42 C in thermal fixture, including hot PCB state; room temperature must charge; open/short faults tested. Untested or failing units cannot be delivered.'},
    'capacitors':caps,
    'physical_tests_performed':False,
    'manufacturing_release':False,
}
out=ROOT/'verification/a2_electrical_checks.json'
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False))
