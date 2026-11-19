"""One-time field layout and sheet-symbol move; CLI netlist must remain equal."""
from pathlib import Path
import re,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=H.parents[3]/'hardware/candidates/system_power_review'
p=B/'usb_qualify.kicad_sch';t=p.read_text(encoding='utf-8')
backup=H/'qualify-before-format.kicad_sch';assert not backup.exists()
backup.write_text(t,encoding='utf-8');ed=[]
def replace(n,s):ed.append((n['start'],n['end'],s))
def field(n,x,y,j='left'):
 replace(child(n,'at'),f'(at {x} {y} 0)')
 replace(child(n,'effects'),'(effects (font (size 1 1))'+(f' (justify {j})' if j else '')+')')
for n in nodes(t)['items'][1:]:
 if not isinstance(n,dict):continue
 if n['items'][0]=='title_block':
  replace(n,'(title_block (title "Mini Companion - CC QUALIFICATION CANDIDATE") (date "2026-09-27") (rev "HW-PWR-010") (comment 1 "Y = USB_READY AND NOT CC_OUT1; NOT direct charger enable") (comment 2 "Low-voltage clamp, BC1.2/default USB, transient validation still required"))')
 elif n['items'][0]=='symbol':
  props={c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
  ref=props['Reference']['items'][2].strip('"');a=child(n,'at');x,y=map(float,a['items'][1:3]);lib=child(n,'lib_id')['items'][1]
  if lib=='"power:GND"':replace(a,f'(at {x} {y} 0)');field(props['Value'],x,y+3.3,'')
  elif ref.startswith('U'):field(props['Reference'],x+14,y-17.78);field(props['Value'],x+14,y-15.24)
  else:field(props['Reference'],x+3.81,y-1.27);field(props['Value'],x+3.81,y+1.27)
 elif n['items'][0]=='global_label':
  ef=child(n,'effects');s=t[ef['start']:ef['end']];s=re.sub(r'\(size [\d.]+ [\d.]+\)','(size 1 1)',s);replace(ef,s)
for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
p=B/'system_power_review.kicad_sch';t=p.read_text(encoding='utf-8')
n=next(n for n in nodes(t)['items'] if isinstance(n,dict) and n['items'][0]=='sheet' and 'usb_qualify.kicad_sch' in t[n['start']:n['end']])
s=t[n['start']:n['end']];s=re.sub(r'\(at ([\d.]+) ([\d.]+)',lambda m:f'(at {float(m[1])-175.26:.4f} {float(m[2])-73.66:.4f}',s)
t=t[:n['start']]+s+t[n['end']:];nodes(t);p.write_text(t,encoding='utf-8')
