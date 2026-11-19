"""One-time drawing cleanup after MCP placement; verify connectivity afterwards."""
from pathlib import Path
import re,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'power-006'))
from format_review_fields import nodes,child
BASE=HERE.parents[3]/'hardware/candidates/system_power_review'
p=BASE/'usb_cc.kicad_sch';t=p.read_text(encoding='utf-8')
backup=HERE/'usb-before-format.kicad_sch';assert not backup.exists()
backup.write_text(t,encoding='utf-8');ed=[]
def replace(n,s):ed.append((n['start'],n['end'],s))
def field(p,x,y,justify='left'):
 replace(child(p,'at'),f'(at {x} {y} 0)')
 replace(child(p,'effects'),'(effects (font (size 1 1))'+(f' (justify {justify})' if justify else '')+')')
for n in nodes(t)['items'][1:]:
 if not isinstance(n,dict):continue
 k=n['items'][0];block=t[n['start']:n['end']]
 if k in ['symbol','wire']:
  m=re.search(r'\((?:at|xy) ([\d.]+) ([\d.]+)',block)
  # Remove redundant global-GND PWR_FLAG and its local drawing cluster only.
  if m and float(m[1])>240 and float(m[2])>130:replace(n,'');continue
 if k=='title_block':
  replace(n,'(title_block (title "Mini Companion - USB CC DETECTION REVIEW ONLY") (date "2026-09-24") (rev "HW-PWR-009") (comment 1 "Raw CC outputs only; NOT charge permission; BC1.2 and default-USB policy pending") (comment 2 "USB-powered 3.3V island; do not join switched MCU rail or add external CC Rd"))')
 elif k=='symbol':
  props={c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
  ref=props['Reference']['items'][2].strip('"');at=child(n,'at');x,y=map(float,at['items'][1:3]);lib=child(n,'lib_id')['items'][1].strip('"')
  if lib=='power:GND':replace(at,f'(at {x} {y} 0)');field(props['Value'],x,y+3.3,'')
  elif ref=='U3':field(props['Reference'],x+10.16,y-10.16);field(props['Value'],x+10.16,y-7.62)
  elif ref=='U4':field(props['Reference'],x+20.32,y-20.32);field(props['Value'],x+20.32,y-17.78)
  elif not ref.startswith('#'):field(props['Reference'],x+3.81,y-1.27);field(props['Value'],x+3.81,y+1.27)
 elif k=='label':
  x,y,angle=map(float,child(n,'at')['items'][1:4])
  replace(child(n,'effects'),'(effects (font (size 1 1)) (justify '+('right' if angle==180 else 'left')+' bottom))')
for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
cache=child(nodes(t),'lib_symbols')
c=next(c for c in cache['items'] if isinstance(c,dict) and 'TPS70933' in str(c['items'][:2]))
s=t[c['start']:c['end']].replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)')
t=t[:c['start']]+s+t[c['end']:]
p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
p=BASE/'output/symbols/TPS70933DBVR.kicad_sym';t=p.read_text(encoding='utf-8');p.write_text(t.replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)'),encoding='utf-8')
