"""Read-only A2 saved-CAD verification. Run with KiCad 10's bundled Python.

Writes verification/a2_saved_drc.json and a2_pcb_receipt.json, never saves PCB.
Uses installed kicad-cli and pcbnew; no network, no autorouter dependency.
"""
from pathlib import Path
import collections, hashlib, json, subprocess, xml.etree.ElementTree as ET
import pcbnew as p

BASE=Path(__file__).resolve().parents[1]
PROJECT=BASE/'project'; BOARD=PROJECT/'mini_companion_a2.kicad_pcb'
CLI=Path(p.__file__).resolve().parents[2]/'kicad-cli.exe'
OUT=BASE/'verification';OUT.mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before=sha(BOARD)
cmd=[str(CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','--exit-code-violations','-o',str(OUT/'a2_saved_drc.json'),str(BOARD)]
subprocess.run(cmd,check=True)
assert sha(BOARD)==before,'Verifier must not save the board'
dr=json.loads((OUT/'a2_saved_drc.json').read_text(encoding='utf8'))
for key in ['violations','unconnected_items','schematic_parity']:assert not dr[key],key
assert not dr.get('ignored_checks',[]),'Final A2 verification must enable every available check'
pro=json.loads(BOARD.with_suffix('.kicad_pro').read_text(encoding='utf8'))
assert pro['board']['design_settings']['drc_exclusions']==[]
b=p.LoadBoard(str(BOARD));assert b.GetCopperLayerCount()==2
assert b.GetDesignSettings().GetBoardThickness()==1600000
edges=[e for e in b.GetDrawings()if e.GetLayer()==p.Edge_Cuts]
assert len(edges)==4 and all(e.GetShape()==p.SHAPE_T_SEGMENT for e in edges)
edge_points={(a.x/1e6,a.y/1e6)for e in edges for a in (e.GetStart(),e.GetEnd())}
assert edge_points=={(100,100),(168,100),(168,135),(100,135)}
fps={f.GetReference():f for f in b.GetFootprints()};main={r:f for r,f in fps.items() if not f.IsExcludedFromBOM()}
anchors={'H1':(3,3,0),'H2':(65,3,0),'H3':(3,32,0),'H4':(65,32,0),'J1':(0,12.5,90),'J2':(23,5,0),'J5':(40,5,0),'J4':(57,5,0),'SW1':(12,26,0),'SW2':(34,26,0),'SW3':(56,26,0),'SW4':(66,12.5,90),'D2':(24,19.5,0)}
for ref,(xx,yy,rot) in anchors.items():
 f=fps[ref];assert (f.GetPosition().x,f.GetPosition().y)==(round((100+xx)*1e6),round((100+yy)*1e6)),ref
 assert (f.GetOrientationDegrees()-rot)%360==0,ref
for ref in ['H1','H2','H3','H4']:
 a=next(iter(fps[ref].Pads()));assert a.GetDrillSize().x==2200000 and a.GetAttribute()==p.PAD_ATTRIB_NPTH
x=ET.parse(OUT/'a2_netlist.xml').getroot();expected={c.get('ref'):c for c in x.findall('components/comp') if c.findtext('footprint')}
assert set(main)==set(expected),{'board':sorted(main),'xml':sorted(expected)}
for ref,c in expected.items():
 f=main[ref];assert f.GetLayer()==p.F_Cu,ref;fid=f.GetFPID();assert str(fid.GetLibNickname())+':'+str(fid.GetLibItemName())==c.findtext('footprint'),ref
 assert f.GetValue()==c.findtext('value'),ref
pinmap={(n.get('ref'),n.get('pin')):net.get('name') for net in x.findall('nets/net') for n in net.findall('node')}
for ref,f in main.items():
 for a in f.Pads():
  if (ref,a.GetNumber()) in pinmap:assert a.GetNetname()==pinmap[(ref,a.GetNumber())],(ref,a.GetNumber())
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
assert min(t.GetWidth() for t in tracks)>=200000
assert min(t.GetDrillValue() for t in vias)>=300000
assert min((t.GetWidth(p.F_Cu)-t.GetDrillValue())/2 for t in vias)>=150000
assert all(t.IsTented(p.F_Cu) and t.IsTented(p.B_Cu) for t in vias)
pads=[(ref,a) for ref,f in main.items() for a in f.Pads() if a.GetAttribute()==p.PAD_ATTRIB_SMD and a.GetLayerSet().Contains(p.F_Paste)]
for via in vias:
 hole=p.SHAPE_CIRCLE(via.GetPosition(),via.GetDrillValue()//2)
 assert not any(a.GetEffectiveShape(p.F_Cu).Collide(hole,150000) for ref,a in pads),'Via drill too near SMT paste pad'
netmetrics={}
for net in sorted({t.GetNetname() for t in tracks}):
 ts=[t for t in tracks if t.GetNetname()==net]
 netmetrics[net]={'track_length_mm':round(sum(t.GetLength() for t in ts)/1e6,4),'min_width_mm':min(t.GetWidth() for t in ts)/1e6,'max_width_mm':max(t.GetWidth() for t in ts)/1e6,'vias':sum(t.GetNetname()==net for t in vias)}
zones=[]
for z in b.Zones():
 poly=z.GetFilledPolysList(z.GetLayer());zones.append({'layer':b.GetLayerName(z.GetLayer()),'net':z.GetNetname(),'filled_area_mm2':round(poly.Area()/1e12,3),'polygon_count':poly.OutlineCount()})
assert len(zones)==2 and all(z['net']=='GND' and z['filled_area_mm2']>1500 for z in zones)
refs={ref:{'local_x_mm':round(f.GetPosition().x/1e6-100,4),'local_y_mm':round(f.GetPosition().y/1e6-100,4),'rotation_deg':f.GetOrientationDegrees(),'side':'top'}for ref,f in sorted(main.items())}
xy=lambda a:[a.x,a.y]
geometry={'placements':refs,'pads':sorted([[ref,a.GetNumber(),xy(a.GetPosition()),xy(a.GetSize()),xy(a.GetDrillSize()),a.GetOrientationDegrees(),a.GetNetname()]for ref,f in fps.items()for a in f.Pads()]),'tracks':sorted([[t.GetNetname(),t.GetLayer(),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth()]for t in tracks]),'vias':sorted([[t.GetNetname(),xy(t.GetPosition()),t.GetWidth(p.F_Cu),t.GetDrillValue()]for t in vias]),'edges':sorted(edge_points),'zones':zones}
geometry_sha=hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest()
command_template=['kicad-cli',*cmd[1:-2],'verification/a2_saved_drc.json','project/mini_companion_a2.kicad_pcb']
receipt={'pcb_sha256':before,'schematic_sha256':sha(BOARD.with_suffix('.kicad_sch')),'xml_sha256':sha(OUT/'a2_netlist.xml'),'kicad_cli_version':subprocess.check_output([str(CLI),'version'],text=True).strip(),'drc_command_template':command_template,'ignored_checks':dr.get('ignored_checks',[]),'violations':0,'unconnected_items':0,'schematic_parity':0,'drc_exclusions':0,'board_mm':[68,35,1.6],'copper_layers':2,'assembly_components_top':len(main),'assembly_components_bottom':0,'physical_smd_copper_pads':sum(1 for f in main.values()for a in f.Pads()if a.GetAttribute()==p.PAD_ATTRIB_SMD and a.GetLayerSet().Contains(p.F_Cu)),'via_drill_histogram_mm':dict(collections.Counter(str(t.GetDrillValue()/1e6)for t in vias)),'minimum_via_annulus_mm':min((t.GetWidth(p.F_Cu)-t.GetDrillValue())/2e6 for t in vias),'via_drill_to_paste_pad_minimum_checked_mm':.15,'vias_tented_front_and_back':True,'zones':zones,'net_metrics':netmetrics,'placements':refs,'physical_validation_complete':False,'fabrication_release':False}
receipt['mechanical_anchors_checked']=True;receipt['geometry_sha256']=geometry_sha
(OUT/'a2_pcb_receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({k:receipt[k]for k in ['pcb_sha256','assembly_components_top','assembly_components_bottom','physical_smd_copper_pads','via_drill_histogram_mm','zones']}))
