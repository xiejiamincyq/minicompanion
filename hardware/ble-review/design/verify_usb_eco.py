"""Recheck saved USB ECO using official ERC/netlist and independent pin rules.

Run with Python 3: verify_usb_eco.py --refresh [--kicad-cli PATH].
This verifies CAD connectivity and arithmetic, not physical USB/charging safety.
"""
from pathlib import Path
import argparse, datetime, hashlib, itertools, json, math, subprocess
import xml.etree.ElementTree as ET

D=Path(__file__).resolve().parent
P=D.parent/'project'
V=D.parent/'verification'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def netlist(path):
    t=ET.parse(path)
    comps={}
    for c in t.findall('./components/comp'):
        fields={f.attrib['name']:f.text or '' for f in c.findall('./fields/field')}
        comps[c.attrib['ref']]={'value':c.findtext('value'),'footprint':c.findtext('footprint'),'mpn':fields.get('MPN',''),'lcsc':fields.get('LCSC','')}
    pins={}; nets={}
    for n in t.findall('./nets/net'):
        name=n.attrib['name'];nets[name]=[]
        for pin in n.findall('node'):
            key=pin.attrib['ref']+'.'+pin.attrib['pin']
            assert key not in pins,key
            pins[key]=name;nets[name].append(key)
    return comps,pins,nets

def bounds():
    # Worst independent resistor initial tolerance + 25ppm/C over 0..45C,
    # referred to 25C. Include both polarities of input leakage conservatively.
    tol=.001+25e-6*25
    def threshold(v,err,hyst,rt,rb,leak):
        fall=[];rise=[]
        for et,eb,ev,il in itertools.product((-tol,tol),(-tol,tol),(-err,err),(-leak,leak)):
            top,bottom=rt*(1+et),rb*(1+eb)
            fall.append(v*(1+ev)*(1+top/bottom)+il*top)
            rise.append(v*(1+ev)*(1+hyst)*(1+top/bottom)+il*top)
        return {'fall_min_v':min(fall),'fall_max_v':max(fall),'rise_max_v':max(rise)}
    vb=threshold(.405,.02,.03,100000,10000,25e-9)
    main=threshold(1.15,.01,.00825,15800,10000,100e-9)
    main['static_low_rail_margin_v']=3.071084386996552-main['rise_max_v']
    # Exact raw VBUS capacitors: C7101=2.2uF,C7102=1uF,C7107=.1uF,
    # all10%. Allow .1uF additional local/cable C. Upstream host hold-up excluded.
    raw_c=(2.2+1+.1)*1.1+.1
    rbleedmax=2700*1.0125
    # Bleed alone: conservative (existing R7111/monitor reduce discharge time).
    unplug_s=rbleedmax*raw_c*1e-6*math.log(5.5/vb['fall_min_v'])
    extra_ma=5.5/(2700*.9875)*1000 + 3.4/(10000*.99)*1000 + 5.5/(110000*(1-tol))*1000 + .012
    return {'scope':'0..45C component ambient, initial tolerance and TCR only; aging, solder drift, noise and physical transients not bounded',
      'vbus':vb,'main_rail':main,'raw_vbus_cap_upper_with_allowance_uf':raw_c,
      'unplug_local_rc_estimate_ms':unplug_s*1000,
      'unplug_limit_note':'RC estimate excludes upstream retained VBUS and has no guaranteed supervisor delay bound; first-board capture must be <=3ms',
      'r7309_max_w_at_20v':20**2/(2700*.9875),'r7309_w_at_5p5v':5.5**2/(2700*.9875),
      'extra_usb_current_budget_ma':extra_ma,'default_usb_steady_estimate_ma':85.47008547008546+5+2+extra_ma,
      'power_switch_off_model_v':(18.2e-6+5e-6+4.2/100e6)*10100,
      'power_switch_max_total_source_leak_ua_for_0p3v':.3/10100*1e6,
      'power_switch_note':'Baseline 18.2uA treated in worst sourcing direction, 5uA board/harness allowance, new-switch IR100Mohm estimate. Actual post-assembly leakage and worn contacts must be tested.',
      'current_note':'Uses baseline slow-charge maximum plus 5mA baseline auxiliary and 2mA reserve, then all ECO additions; inrush and suspend not verified'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true')
    ap.add_argument('--kicad-cli',default=r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe')
    args=ap.parse_args()
    contract=json.loads((D/'usb_eco_contract.json').read_text(encoding='utf-8'))
    for fn,h in contract['schematic_sha256'].items():assert sha(P/fn)==h,('candidate changed',fn)
    if args.refresh:
        subprocess.run([args.kicad_cli,'sch','export','netlist','--format','kicadxml','-o',str(V/'usb_eco.xml'),str(P/'mini_companion_integrated.kicad_sch')],check=True)
        subprocess.run([args.kicad_cli,'sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(V/'usb_erc.json'),str(P/'mini_companion_integrated.kicad_sch')],check=True)
    baseline=json.loads((V/'usb_baseline_contract.json').read_text(encoding='utf-8'))
    comps,pins,nets=netlist(V/'usb_eco.xml')
    assert len(comps)==113
    added={c['ref']:c for c in contract['new_components']}
    assert set(comps)-set(baseline['components'])==set(added)
    assert set(baseline['components'])-set(comps)==set()
    for ref,c in baseline['components'].items():assert comps[ref]==c,('unintended existing metadata change',ref)
    changes={ref+'.'+pin:net for ref,p in contract['existing_pin_changes'].items() for pin,net in p.items()}
    observed={key:(old,pins.get(key)) for key,old in baseline['pins'].items() if pins.get(key)!=old}
    assert set(observed)==set(changes),(set(observed)-set(changes),set(changes)-set(observed))
    for key,net in changes.items():
        if net is None:assert pins[key].startswith('unconnected-') and nets[pins[key]]==[key],key
        else:assert pins[key]==net,(key,pins[key],net)
    # Independent, datasheet-derived pin contracts; especially MR/SENSE are not interchangeable.
    critical={
      'U7301':{'1':'USB_DATA_EN','2':'GND','3':'USB_3V3','5':'USB_VBUS_SENSE','6':'USB_3V3'},
      'U7302':{'1':'USB_MAIN_SENSE','2':'GND','3':'USB_3V3','4':'USB_3V3','6':'USB_DATA_EN'},
      'D7301':{'1':'USB_DP_CONN','2':'USB_DM_CONN','3':'GND'},
      'U1101':{'9':'USB_DP_ISO','10':'USB_DP_CONN','11':'USB_DATA_EN','13':'USB_DM_ISO','14':'USB_DM_CONN','15':'USB_DATA_EN','16':'VLOGIC_SWITCHED'},
      'U101':{'4':'MCU_BOOT','23':'MCU_USB_DM','24':'MCU_USB_DP','44':'MCU_STRAP46'},
      'SW7301':{'2':'GND','3':'NTC_TS','5':'GND','6':'VBUS_INHIBIT_BASE'},
      'SW7302':{'1':'MCU_BOOT','2':'GND'},
      'SW7201':{'1':'PACK_POS','2':'POWER_REQUEST'},
      'J7201':{'1':'PACK_POS','2':'POWER_REQUEST','3':'GND'},
      'R7113':{'1':'POWER_REQUEST','2':'EN_RUN'},
      'R7114':{'1':'EN_RUN','2':'GND'},
    }
    for ref,pp in critical.items():
        for pin,net in pp.items():assert pins[ref+'.'+pin]==net,(ref,pin)
    for ref,c in added.items():
        assert comps[ref]=={k:c[k] for k in ('value','footprint','mpn','lcsc')},ref
        for pin,net in c['pins'].items():
            actual=pins[ref+'.'+pin]
            if net is None:assert actual.startswith('unconnected-') and nets[actual]==[ref+'.'+pin]
            else:assert actual==net,(ref,pin,actual,net)
    assert set(nets['USB_DATA_EN'])=={'R7306.2','R7307.1','U7301.1','U7302.6','U1101.11','U1101.15'}
    assert {x for x in nets['VBUS_RAW'] if x.split('.')[0].startswith('C')}=={'C7101.1','C7102.1','C7107.1'}
    erc=json.loads((V/'usb_erc.json').read_text(encoding='utf-8'))
    violations=[e for s in erc['sheets'] for e in s['violations']]
    assert not violations,violations
    latest_source=max(p.stat().st_mtime for p in P.glob('*.kicad_sch'))
    assert (V/'usb_eco.xml').stat().st_mtime>=latest_source,'Stale netlist: run --refresh'
    assert (V/'usb_erc.json').stat().st_mtime>=latest_source,'Stale ERC: run --refresh'
    b=bounds()
    assert b['main_rail']['rise_max_v']<3.071084386996552
    assert b['vbus']['rise_max_v']<4.75 and b['vbus']['fall_min_v']>4.35
    assert b['default_usb_steady_estimate_ma']<100 and b['r7309_max_w_at_20v']<.25
    (V/'usb_static_bounds.json').write_text(json.dumps(b,indent=2)+'\n',encoding='utf-8')
    files=list(P.glob('*.kicad_sch'))+list(P.glob('*.kicad_sym'))+[P/'sym-lib-table',P/'fp-lib-table',V/'usb_eco.xml',V/'usb_erc.json',D/'usb_eco_contract.json',V/'usb_baseline_contract.json',V/'usb_static_bounds.json',Path(__file__)]
    report={'state':'CAD_AND_STATIC_ARITHMETIC_VERIFIED_PHYSICAL_PENDING','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kicad':erc['kicad_version'],'schematic_refs':len(comps),'new_refs':len(added),'existing_pin_changes':observed,'unchanged_existing_pins':len(baseline['pins'])-len(changes),'erc_violations':len(violations),'physical_tests_executed':False,'pcb_drc':'owned by PCB integration evidence; not implied here','sha256':{str(p.relative_to(D.parent)):sha(p) for p in files}}
    (V/'usb_schematic_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('state','schematic_refs','new_refs','unchanged_existing_pins','erc_violations')}))
if __name__=='__main__':main()
