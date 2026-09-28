"""Cosmetic cleanup of the newly added EN switch; netlist comparison required."""
from pathlib import Path
import sys,re
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=H.parents[3]/'hardware/candidates/system_power_review'
p=B/'usb_qualify.kicad_sch';t=p.read_text(encoding='utf-8')
backup=H/'qualify-before-layout.kicad_sch';assert not backup.exists()
backup.write_text(t,encoding='utf-8');ed=[]
def replace(n,s):ed.append((n['start'],n['end'],s))
def field(n,x,y,j='left'):
 replace(child(n,'at'),f'(at {x} {y} 0)')
 replace(child(n,'effects'),'(effects (font (size 1 1))'+(f' (justify {j})' if j else '')+')')
for n in nodes(t)['items'][1:]:
 if not isinstance(n,dict):continue
 if n['items'][0]=='title_block':
  replace(n,'(title_block (title "Mini Companion - CC CHARGER CONTROL REVIEW") (date "2026-09-28") (rev "HW-PWR-011") (comment 1 "Two series switches pull EN1 low only with READY and CC permission") (comment 2 "VBUS-powered supervisor; fast brownout and default USB/BC1.2 not validated"))')
 elif n['items'][0]=='symbol':
  pr={c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
  ref=pr['Reference']['items'][2].strip('"');at=child(n,'at');x,y=map(float,at['items'][1:3])
  if ref=='U7':field(pr['Reference'],x+13,y-14);field(pr['Value'],x+13,y-11.46)
  elif ref=='C14':field(pr['Reference'],x+5.08,y-1.27);field(pr['Value'],x+5.08,y+1.27)
  elif child(n,'lib_id')['items'][1]=='"power:GND"':
   replace(at,f'(at {x} {y} 0)');field(pr['Value'],x,y+3.3,'')
 elif n['items'][0]=='global_label':
  e=child(n,'effects');s=t[e['start']:e['end']];replace(e,re.sub(r'\(size [\d.]+ [\d.]+\)','(size 1 1)',s))
for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
lib=child(nodes(t),'lib_symbols');c=next(c for c in lib['items'] if isinstance(c,dict) and 'TS5A23166' in str(c['items'][:2]))
s=t[c['start']:c['end']].replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)')
t=t[:c['start']]+s+t[c['end']:];p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
p=B/'output/symbols/TS5A23166DCUR.kicad_sym';t=p.read_text(encoding='utf-8');p.write_text(t.replace('(offset 1.016)','(offset 0.254)').replace('(size 1.27 1.27)','(size 0.9 0.9)'),encoding='utf-8')
