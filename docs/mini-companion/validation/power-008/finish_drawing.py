"""Targeted fallback: explicit hierarchical supply and readable fields.

MCP dropped a custom cache in this project. Back up, edit structured spans,
and require independent pin contracts and CLI ERC, not suppression rules.
"""
from pathlib import Path
import sys,re,uuid
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'power-006'))
from format_review_fields import nodes,child
BASE=ROOT/'hardware/candidates/system_power_review'
def uid(): return str(uuid.uuid4())
for name in ['system_power_review','backlight']:
 p=BASE/(name+'.kicad_sch');t=p.read_text(encoding='utf-8')
 backup=HERE/(name+'-before-finish.kicad_sch');assert not backup.exists() or backup.read_text(encoding='utf-8')==t
 backup.write_text(t,encoding='utf-8'); edits=[]
 def replace(n,s): edits.append((n['start'],n['end'],s))
 def field(p,x,y,justify='left'):
  replace(child(p,'at'),f'(at {x} {y} 0)')
  replace(child(p,'effects'),'(effects (font (size 1 1))'+(f' (justify {justify})' if justify else '')+')')
 for n in nodes(t)['items'][1:]:
  if not isinstance(n,dict): continue
  kind=n['items'][0]
  if kind=='global_label':
   if name=='backlight':
    s=t[n['start']:n['end']].replace('global_label "BL_SUPPLY"','hierarchical_label "VLOGIC_SWITCHED"').replace('shape bidirectional','shape input').replace('size 1.524 1.524','size 1 1')
    replace(n,s)
   else: replace(n,'')
  elif kind=='sheet' and name!='backlight':
   s=t[n['start']:n['end']]
   s=s[:-1]+f'(pin "VLOGIC_SWITCHED" input (at 95.25 147.32 180) (effects (font (size 1 1)))(uuid "{uid()}")))'
   replace(n,s)
  elif name=='backlight' and kind=='symbol':
   props={c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
   ref=props['Reference']['items'][2].strip('"');at=child(n,'at');x,y=map(float,at['items'][1:3])
   lib=child(n,'lib_id')['items'][1].strip('"')
   if lib=='power:GND':
    replace(at,f'(at {x} {y} 0)');field(props['Value'],x,y+3.3,'')
   elif ref=='U2':
    field(props['Reference'],x+13,y-23);field(props['Value'],x+13,y-20.46)
   else:
    field(props['Reference'],x+3.81,y-1.27);field(props['Value'],x+3.81,y+1.27)
  elif name=='backlight' and kind=='label':
   x,y,angle=map(float,child(n,'at')['items'][1:4])
   replace(child(n,'effects'),'(effects (font (size 1 1)) (justify '+('right' if angle==180 else 'left')+' bottom))')
 for a,b,s in sorted(edits,reverse=True): t=t[:a]+s+t[b:]
 if name!='backlight':
  t=t.replace('(xy 209.55 50.8)','(xy 207.01 50.8)')
  t=t.rstrip()[:-1]+f'\n(wire (pts (xy 90.17 147.32) (xy 95.25 147.32)) (stroke (width 0) (type solid)) (uuid "{uid()}"))\n(label "VLOGIC_SWITCHED" (at 90.17 147.32 180) (effects (font (size 1 1)) (justify right bottom)) (uuid "{uid()}"))\n)\n'
  t=t.replace('HW-PWR-007','HW-PWR-008')
 else:
  cache=child(nodes(t),'lib_symbols')
  c=next(c for c in cache['items'] if isinstance(c,dict) and 'TPS60231' in str(c['items'][:2]))
  s=t[c['start']:c['end']].replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)')
  t=t[:c['start']]+s+t[c['end']:]
 t=re.sub(r'[ \t]+(?=\n|\Z)','',t);nodes(t);p.write_text(t,encoding='utf-8')
lib=BASE/'output/symbols/TPS60231RGTR.kicad_sym'
t=lib.read_text(encoding='utf-8').replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)')
lib.write_text(t,encoding='utf-8')
print('Hierarchical supply and field layout written; verification required.')
