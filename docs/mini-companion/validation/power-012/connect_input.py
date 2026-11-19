"""Split raw receptacle supply from the protected downstream supply."""
from pathlib import Path
import sys,re
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=H.parents[3]/'hardware/candidates/system_power_review'
p=B/'usb_cc.kicad_sch';t=p.read_text(encoding='utf-8');ed=[]
for n in nodes(t)['items']:
 if not isinstance(n,dict) or n['items'][0]!='global_label':continue
 xy=tuple(map(float,child(n,'at')['items'][1:3]))
 if xy in [(27.94,170.18),(218.44,137.16)]:
  assert n['items'][1]=='"VBUS_IN"'
  ed.append((n['start'],n['end'],t[n['start']:n['end']].replace('"VBUS_IN"','"VBUS_RAW"',1)))
assert len(ed)==2
for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
p=B/'system_power_review.kicad_sch';t=p.read_text(encoding='utf-8')
t=t.replace('(rev "HW-PWR-011")','(rev "HW-PWR-012")').replace('(date "2026-09-23")','(date "2026-09-28")')
p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
