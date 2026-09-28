"""Format the preserved post-MCP sheet, with non-overlapping replacements."""
from pathlib import Path
import sys,re
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=H.parents[3]/'hardware/candidates/system_power_review'
t=(H/'input-before-layout.kicad_sch').read_text(encoding='utf-8');ed=[]
for n in nodes(t)['items']:
 if not isinstance(n,dict):continue
 if n['items'][0] in ['label','global_label']:
  e=child(n,'effects');angle=float(child(n,'at')['items'][3]);j='left' if angle==0 else 'right'
  ed.append((e['start'],e['end'],f'(effects (font (size 1 1)) (justify {j}))'))
  continue
 if n['items'][0]!='symbol':continue
 pr={c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
 ref=pr['Reference']['items'][2].strip('"');x,y=map(float,child(n,'at')['items'][1:3])
 if ref.startswith('#'):
  if child(n,'lib_id')['items'][1]=='"power:GND"':
   a=child(n,'at');ed.append((a['start'],a['end'],f'(at {x} {y} 0)'))
   v=pr['Value'];ed.append((v['start'],v['end'],f'(property "Value" "GND" (at {x} {y+3.81} 0) (effects (font (size 1 1))))'))
  continue
 for key,offset in [('Reference',-1.27),('Value',1.27)]:
  c=pr[key];value=c['items'][2]
  if key=='Value' and ref=='C15':value='"1uF 50V X7R"'
  if key=='Value' and ref=='C16':value='"2.2uF 10V X7R"'
  xx,yy=(x+19.05,y-15.24+(0 if key=='Reference' else 2.54)) if ref=='U8' else (x+7.62,y+offset)
  ed.append((c['start'],c['end'],f'(property "{key}" {value} (at {xx} {yy} 0) (effects (font (size 1 1)) (justify left)))'))
for (a,b,_),(c,d,_) in zip(sorted(ed),sorted(ed)[1:]):assert b<=c,'Overlapping edits'
for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
# Shrink the custom symbol's pin labels, retaining coordinates and pin contracts.
lib=child(nodes(t),'lib_symbols')
sub=t[lib['start']:lib['end']]
sym=next(n for n in nodes(sub)['items'] if isinstance(n,dict) and n['items'][0]=='symbol' and 'TPS259470' in n['items'][1])
st=sub[sym['start']:sym['end']].replace('(size 1.27 1.27)','(size 0.8 0.8)')
sub=sub[:sym['start']]+st+sub[sym['end']:]
t=t[:lib['start']]+sub+t[lib['end']:]
nodes(t);(B/'usb_input.kicad_sch').write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
p=B/'output/symbols/TPS259470LRPWR.kicad_sym'
t=p.read_text(encoding='utf-8').replace('(size 1.27 1.27)','(size 0.8 0.8)');p.write_text(t,encoding='utf-8')
