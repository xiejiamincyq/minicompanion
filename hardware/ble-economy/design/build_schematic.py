"""Reproducible A2 schematic source. Native KiCad CLI checks remain authoritative.

Only schematic/symbol files are written. Board and project settings belong to
the independent PCB writer. Stable UUIDs preserve PCB associations on refresh.
"""
from pathlib import Path
import copy, json, re, uuid

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'project'
P.mkdir(parents=True, exist_ok=True)
SYS = Path(r'C:\Program Files\KiCad\10.0\share\kicad\symbols')
class A(str): pass
def parse(s):
    stack=[]; root=None
    for t in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s):
        if t=='(':
            n=[]
            if stack: stack[-1].append(n)
            else: root=n
            stack.append(n)
        elif t==')': stack.pop()
        else: stack[-1].append(json.loads(t) if t.startswith('"') else A(t))
    assert not stack
    return root
def dump(x,d=0):
    if isinstance(x,A): return str(x)
    if not isinstance(x,list): return json.dumps(str(x),ensure_ascii=False)
    if not any(isinstance(v,list) for v in x): return '('+' '.join(dump(v) for v in x)+')'
    out='('; first=True
    for v in x:
        if isinstance(v,list): out+='\n'+'  '*(d+1)+dump(v,d+1)
        else: out+=('' if first else ' ')+dump(v)
        first=False
    return out+')'
def ch(x,k): return [n for n in x if isinstance(n,list) and n and n[0]==k]
def one(x,k): return next(iter(ch(x,k)),None)
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'mini-companion-a2/'+s))
Q=lambda s:json.dumps(str(s),ensure_ascii=False)
def prop(k,v,x=0,y=0,hide=False):
    return parse(f'(property {Q(k)} {Q(v)} (at {x} {y} 0) (effects (font (size 1.1 1.1)) {"(hide yes)" if hide else ""}))')
def standard(lib,name):
    t=parse((SYS/(lib+'.kicad_sym')).read_text(encoding='utf-8'))
    return copy.deepcopy(next(n for n in ch(t,'symbol') if n[1]==name))
def box(name,pins,prefix='U'):
    # pin tuples: number, name, electrical type, x, y, orientation
    t=parse(f'(symbol {Q(name)} (pin_names (offset 0.4)) (in_bom yes) (on_board yes))')
    t += [prop('Reference',prefix,0,11),prop('Value',name,0,-11)]
    t.append(parse(f'(symbol {Q(name+"_0_1")} (rectangle (start -10.16 7.62) (end 10.16 -7.62) (stroke (width 0.254) (type default)) (fill (type background))))'))
    un=[A('symbol'),name+'_1_1']
    for num,nm,ty,x,y,ang in pins:
        un.append(parse(f'(pin {ty} line (at {x} {y} {ang}) (length 5.08) (name {Q(nm)} (effects (font (size 1 1)))) (number {Q(num)} (effects (font (size 1 1)))))'))
    t.append(un);return t
syms={n:standard('Device',n) for n in ['R','C','L','D_Zener','LED','Thermistor_NTC']}
syms['Q_NPN_BEC']=box('Q_NPN_BEC',[('1','BASE','input',-15.24,0,0),('2','EMITTER','passive',15.24,-5.08,180),('3','COLLECTOR','passive',15.24,5.08,180)],'Q')
syms['Q_NMOS_GSD']=box('Q_NMOS_GSD',[('1','GATE','input',-15.24,0,0),('2','SOURCE','passive',15.24,-5.08,180),('3','DRAIN','passive',15.24,5.08,180)],'Q')
syms['Q_PMOS_GSD']=box('Q_PMOS_GSD',[('1','GATE','input',-15.24,0,0),('2','SOURCE','passive',15.24,-5.08,180),('3','DRAIN','passive',15.24,5.08,180)],'Q')
syms['KT-0603R']=standard('Device','LED')
syms['KT-0603R'][1]='KT-0603R'
for sub in ch(syms['KT-0603R'],'symbol'):
    sub[1]=sub[1].replace('LED_','KT-0603R_')
    for pin in ch(sub,'pin'):
        number=one(pin,'number');number[1]={'1':'2','2':'1'}[number[1]]
syms['SW_Push']=standard('Switch','SW_Push')
for n in [2,4,5]: syms[f'Conn_01x0{n}']=standard('Connector_Generic',f'Conn_01x0{n}')
# Exact selected footprints, not inherited generic filters that reject valid parts.
filters={'KT-0603R':'KT-0603R','L':'FTC404030S1R0MGCA'}
for n in [2,4,5]:
    filters[f'Conn_01x0{n}']=f'JST_PH_B{n}B-PH-SM4-TB_1x0{n}-1MP_P2.00mm_Vertical'
for name,pattern in filters.items():
    f=next((p for p in ch(syms[name],'property') if p[1]=='ki_fp_filters'),None)
    if f is None:syms[name].append(prop('ki_fp_filters',pattern,hide=True))
    else:f[2]=pattern
syms['PWR_FLAG']=standard('power','PWR_FLAG')
syms['BQ25170DSGR']=box('BQ25170DSGR',[
 ('1','IN','power_in',-15.24,5.08,0),('2','ISET','passive',-15.24,2.54,0),('3','TS','input',-15.24,0,0),('4','GND','power_in',-15.24,-2.54,0),('5','STAT','open_collector',-15.24,-5.08,0),
 ('6','PG','open_collector',15.24,5.08,180),('7','VSET','input',15.24,2.54,180),('8','OUT','power_out',15.24,0,180),('9','EP_GND','passive',15.24,-2.54,180)])
syms['TPS61023DRLR']=box('TPS61023DRLR',[
 ('1','FB','input',-15.24,5.08,0),('2','EN','input',-15.24,0,0),('3','VIN','power_in',-15.24,-5.08,0),('4','GND','power_in',15.24,-5.08,180),('5','SW','passive',15.24,0,180),('6','VOUT','power_out',15.24,5.08,180)])
syms['TLV803EA30DBZR']=box('TLV803EA30DBZR',[
 ('1','GND','power_in',-15.24,-5.08,0),('2','RESET_n','open_collector',15.24,0,180),('3','VDD','power_in',-15.24,5.08,0)])
syms['MSK12C02']=box('MSK12C02',[
 ('1','RUN','passive',-15.24,5.08,0),('2','COMMON','passive',15.24,0,180),('3','OFF_NC','passive',-15.24,-5.08,0),('SH','SHELL','passive',15.24,-5.08,180)],'SW')
syms['DC-050-2.0-BD']=box('DC-050-2.0-BD',[
 ('1','CENTRE_POS','passive',15.24,5.08,180),('2','SLEEVE_GND','passive',15.24,0,180),('3','SLEEVE_NC_SWITCH','passive',15.24,-5.08,180)],'J')
datasheets={'BQ25170DSGR':'https://www.ti.com/lit/ds/symlink/bq25170.pdf','TPS61023DRLR':'https://www.ti.com/lit/ds/symlink/tps61023.pdf','TLV803EA30DBZR':'https://www.ti.com/lit/ds/symlink/tlv803e.pdf'}
for name,s in syms.items():
    if name in datasheets:s.append(prop('Datasheet',datasheets[name],hide=True))
rootid=uid('root')
t=parse(f'(kicad_sch (version 20260306) (generator "eeschema") (uuid "{rootid}") (paper "A2") (title_block (title "Mini Companion A2 — separate power and keys") (date "2026-11-19") (rev "A2-DRAFT") (comment 1 "Two-unit prototype candidate. No fabrication release. Core BAT and VBAT remain empty.")) (lib_symbols))')
items=[]
def text(s,x,y,size=1.3):
    t.append(parse(f'(text {Q(s)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid("text/"+s)}"))'))
def add(ref,part,value,fp,mpn,code,pos,pins,domain='main',maker=''):
    libid='A2_Power:'+part; cache=one(t,'lib_symbols')
    if not any(n[1]==libid for n in ch(cache,'symbol')):
        s=copy.deepcopy(syms[part]);s[1]=libid;cache.append(s)
    x,y=(round(round(v/1.27)*1.27,5) for v in pos); onboard=domain=='main';bom=not ref.startswith('#')
    s=parse(f'(symbol (lib_id {Q(libid)}) (at {x} {y} 0) (unit 1) (in_bom {"yes" if bom else "no"}) (on_board {"yes" if onboard else "no"}) (dnp no) (uuid "{uid(ref)}"))')
    s += [prop('Reference',ref,x,y-12.7),prop('Value',value,x,y-10.16),prop('Footprint',fp,x,y,True),prop('Datasheet',datasheets.get(part,''),x,y,True),prop('MPN',mpn,x,y,True),prop('LCSC',code,x,y,True),prop('Manufacturer',maker,x,y,True),prop('AssemblyDomain',domain,x,y,True)]
    for sub in ch(syms[part],'symbol'):
        for pn in ch(sub,'pin'):s.append(parse(f'(pin {Q(one(pn,"number")[1])} (uuid "{uid(ref+"/pin/"+one(pn,"number")[1])}"))'))
    s.append(parse(f'(instances (project "mini_companion_a2" (path "/{rootid}" (reference {Q(ref)}) (unit 1))))'))
    t.append(s)
    seen=set()
    for sub in ch(syms[part],'symbol'):
        for pn in ch(sub,'pin'):
            num=one(pn,'number')[1];seen.add(num);nx,ny,angle=map(float,one(pn,'at')[1:4]);pt=(round(x+nx,5),round(y-ny,5));net=pins[num]
            if net is None:
                t.append(parse(f'(no_connect (at {pt[0]} {pt[1]}) (uuid "{uid(ref+"/NC/"+num)}"))'));continue
            dx=-5.08 if nx<0 or (nx==0 and ny>0) else 5.08
            end=(round(pt[0]+dx,5),pt[1]);ang=180 if dx<0 else 0
            t.append(parse(f'(wire (pts (xy {pt[0]} {pt[1]}) (xy {end[0]} {end[1]})) (stroke (width 0) (type default)) (uuid "{uid(ref+"/wire/"+num)}"))'))
            t.append(parse(f'(global_label {Q(net)} (shape bidirectional) (at {end[0]} {end[1]} {ang}) (effects (font (size 1 1)) (justify {"right" if ang else "left"})) (uuid "{uid(ref+"/label/"+num)}"))'))
    assert seen==set(pins),(ref,seen,set(pins))
    items.append(dict(ref=ref,part=part,value=value,footprint=fp,mpn=mpn,lcsc=code,manufacturer=maker,domain=domain,pins=pins))
RFP='Resistor_SMD:R_0603_1608Metric';CFP='Capacitor_SMD:C_0805_2012Metric';SOT='Package_TO_SOT_SMD:SOT-23'
def resistor(ref,value,mpn,code,pos,a,b):add(ref,'R',value,RFP,mpn,code,pos,{'1':a,'2':b},maker='UNI-ROYAL')
def cap(ref,value,mpn,code,pos,a,fp=CFP):add(ref,'C',value,fp,mpn,code,pos,{'1':a,'2':'GND'},maker='Samsung Electro-Mechanics' if mpn.startswith('CL') else 'YAGEO')
PH2='Connector_JST:JST_PH_B2B-PH-SM4-TB_1x02-1MP_P2.00mm_Vertical'
text('A2 / 5 V CENTRE-POSITIVE DC CHARGER INPUT — not a computer USB charging port',20,15,2)
text('RUN cable occupies the core USB-C socket. Unplug it before connecting a computer. Core BAT/VBAT stay empty.',20,23)
add('J1','DC-050-2.0-BD','5V DC / centre +','A2_Candidate:DC-050-2.0-BD','DC-050-2.0-BD','C51927418',(40,55),{'1':'DC_RAW','2':'GND','3':'PLUG_SENSE'},maker='CAX')
add('Q3','Q_PMOS_GSD','AO3401A / reverse protection',SOT,'AO3401A','C15127',(110,55),{'1':'PMOS_GATE','2':'DC_PROTECTED','3':'DC_RAW'},maker='Alpha and Omega Semiconductor')
resistor('R15','100k gate bias','0603WAF1003T5E','C25803',(180,95),'PMOS_GATE','GND')
add('D3','D_Zener','10V gate clamp','Diode_SMD:D_SOD-123','BZT52C10','C2103',(110,95),{'1':'DC_PROTECTED','2':'PMOS_GATE'},maker='Jiangsu Changjing Electronics')
cap('C1','2.2uF 50V','CL21B225KBYNNNE','C2762602',(180,55),'DC_PROTECTED')
add('U1','BQ25170DSGR','BQ25170 / 4.1V 0.3A','Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm','BQ25170DSGR','C5208201',(265,55),{'1':'DC_PROTECTED','2':'CHG_ISET','3':'NTC_TS','4':'GND','5':'CHG_STAT','6':None,'7':'CHG_VSET','8':'PACK_POS','9':'GND'},maker='Texas Instruments')
resistor('R1','36k 1%','0603WAF3602T5E','C23147',(350,55),'CHG_VSET','GND')
resistor('R2','1k 1%','0603WAF1001T5E','C21190',(420,55),'CHG_ISET','GND')
add('J2','Conn_01x04','PROTECTED BATTERY + NTC','Connector_JST:JST_PH_B4B-PH-SM4-TB_1x04-1MP_P2.00mm_Vertical','B4B-PH-SM4-TB(LF)(SN)','C160354',(520,55),{'1':'PACK_POS','2':'GND','3':'NTC_TS','4':'GND'},maker='JST')
text('Battery has independent PCM. NTC must touch the cell with verified electrical insulation; connector is not a fixed resistor.',20,75)
add('TH1','Thermistor_NTC','10k B3950 cell probe','','HNTC-103F3950FB-100B','C52204609',(45,115),{'1':'NTC_TS','2':'GND'},domain='battery_probe',maker='HNTC')
add('Q2','Q_NMOS_GSD','AO3400A / inhibit charge',SOT,'AO3400A','C20917',(210,115),{'1':'CORE_SENSE_GATE','2':'GND','3':'NTC_TS'},maker='Alpha and Omega Semiconductor')
resistor('R3','1k 1%','0603WAF1001T5E','C21190',(290,115),'CORE_5V_SENSE','CORE_SENSE_GATE')
resistor('R4','100k 1%','0603WAF1003T5E','C25803',(360,115),'CORE_SENSE_GATE','GND')
resistor('R5','3.3k 1%','0603WAF3301T5E','C22978',(430,115),'PACK_POS','LED_ANODE')
add('D2','KT-0603R','CHARGE red / 1A 2K','A2_Candidate:KT-0603R','KT-0603R','C2286',(520,115),{'1':'LED_ANODE','2':'CHG_STAT'},maker='KENTO')
text('RUN / regulated ~4.96 V; TPS61023 has true shutdown disconnection. No host/data connection exists on this power lead.',20,150)
cap('C2','22uF 25V','CL21A226MAQNNNE','C45783',(40,185),'PACK_POS')
cap('C3','100nF 50V','CC0603KRX7R9BB104','C14663',(110,185),'PACK_POS','Capacitor_SMD:C_0603_1608Metric')
add('L1','L','1uH high-current','A2_Candidate:FTC404030S1R0MGCA','FTC404030S1R0MGCA','C39676079',(180,185),{'1':'PACK_POS','2':'BOOST_SW'},maker='cjiang (Changjiang)')
add('U2','TPS61023DRLR','TPS61023 / true shutdown','Package_TO_SOT_SMD:SOT-563','TPS61023DRLR','C919459',(265,185),{'1':'BOOST_FB','2':'RUN_EN','3':'PACK_POS','4':'GND','5':'BOOST_SW','6':'RUN_5V'},maker='Texas Instruments')
cap('C4','22uF 25V','CL21A226MAQNNNE','C45783',(350,185),'RUN_5V')
cap('C5','22uF 25V','CL21A226MAQNNNE','C45783',(420,185),'RUN_5V')
add('J4','Conn_01x02','RUN USB-C power lead',PH2,'B2B-PH-SM4-TB(LF)(SN)','C160352',(520,185),{'1':'RUN_5V','2':'GND'},maker='JST')
resistor('R6','220k 1%','0603WAF2203T5E','C22961',(350,230),'RUN_5V','BOOST_FB')
resistor('R7','30k 1%','0603WAF3002T5E','C22984',(420,230),'BOOST_FB','GND')
resistor('R8','10k bleed','0603WAF1002T5E','C25804',(520,230),'RUN_5V','GND')
add('SW4','MSK12C02','POWER RUN / OFF','Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02','MSK12C02','C431540',(60,255),{'1':'PACK_POS','2':'RUN_REQUEST','3':None,'SH':'GND'},maker='SHOU HAN')
resistor('R9','10k 1%','0603WAF1002T5E','C25804',(110,245),'RUN_REQUEST','RUN_EN')
resistor('R10','100k default OFF','0603WAF1003T5E','C25803',(180,245),'RUN_EN','GND')
add('Q1','Q_NMOS_GSD','AO3400A / plug OFF',SOT,'AO3400A','C20917',(265,245),{'1':'PLUG_SENSE','2':'GND','3':'RUN_EN'},maker='Alpha and Omega Semiconductor')
resistor('R11','47k plug bias','0603WAF4702T5E','C25819',(40,310),'PACK_POS','PLUG_SENSE')
text('J1.3 shorts to GND with no plug. Insertion opens it and Q1 clamps RUN_EN. OFF throw is NC, never battery-to-GND.',20,280)
resistor('R12','10k','0603WAF1002T5E','C25804',(110,310),'PACK_POS','UVLO_VDD')
resistor('R13','330k feedback','0603WAF3303T5E','C23137',(180,310),'RUN_5V','UVLO_VDD')
resistor('R14','330k','0603WAF3303T5E','C23137',(265,310),'UVLO_VDD','GND')
add('U3','TLV803EA30DBZR','3.08V / 200ms supervisor',SOT,'TLV803EA30DBZR','C5218924',(350,310),{'1':'GND','2':'RUN_EN','3':'UVLO_VDD'},maker='Texas Instruments')
cap('C6','100nF 50V','CC0603KRX7R9BB104','C14663',(420,310),'UVLO_VDD','Capacitor_SMD:C_0603_1608Metric')
add('J5','Conn_01x05','CORE keys + 5V sense','Connector_JST:JST_PH_B5B-PH-SM4-TB_1x05-1MP_P2.00mm_Vertical','B5B-PH-SM4-TB(LF)(SN)','C265085',(520,310),{'1':'GND','2':'KEY_A','3':'KEY_B','4':'KEY_C','5':'CORE_5V_SENSE'},maker='JST')
for i,key in enumerate(['KEY_A','KEY_B','KEY_C'],1):
    add('SW'+str(i),'SW_Push',key+' / dry contact','Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A','TS-1187A-B-A-B','C318884',(40+70*(i-1),365),{'1':key,'2':'GND'},maker='XKB')
text('Core harness: KEY_A=GPIO2/P1.1; KEY_B=GPIO4/P1.2; KEY_C=GPIO7/P1.9; sense=P1.14(5V).\nNo carrier-side key pull-ups. Do not connect core BAT/VBAT. Permanent labelled harness; sense-open is an explicit fault boundary.',250,357)
for n,(net,pos) in enumerate([('GND',(270,385)),('DC_PROTECTED',(420,385)),('UVLO_VDD',(350,385))],1):
    add('#FLG0'+str(n),'PWR_FLAG','PWR_FLAG','','','',pos,{'1':net},domain='annotation')
library=[A('kicad_symbol_lib'),[A('version'),A('20231120')],[A('generator'),'eeschema']]+list(syms.values())
(P/'A2_Power.kicad_sym').write_text(dump(library)+'\n',encoding='utf-8')
(P/'sym-lib-table').write_text('(sym_lib_table\n  (version 7)\n  (lib (name "A2_Power") (type "KiCad") (uri "${KIPRJMOD}/A2_Power.kicad_sym") (options "") (descr "A2 exact pin contracts and vendored passives"))\n)\n',encoding='utf-8')
(P/'mini_companion_a2.kicad_sch').write_text(dump(t)+'\n',encoding='utf-8')
(ROOT/'design'/'electrical_contract.json').write_text(json.dumps({'schema':1,'status':'DRAFT_NOT_RELEASED','components':items},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'schematic':str(P/'mini_companion_a2.kicad_sch'),'board_components':sum(x['domain']=='main' for x in items),'offboard_components':sum(x['domain']=='battery_probe' for x in items)},ensure_ascii=False))
