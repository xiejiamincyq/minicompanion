"""Import preserved core into MCP-created child, with explicit integration edits.

One-shot structured fallback: backups retained; CLI and independent pin contracts
are mandatory after running. The original standalone core is never changed.
"""
from pathlib import Path
import re,sys,uuid
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=ROOT/'hardware/candidates/system_power_review'
def uid():return str(uuid.uuid4())
def items(t,k):return [n for n in nodes(t)['items'] if isinstance(n,dict) and n['items'][0]==k]
def props(n):return {c['items'][1].strip('"'):c for c in n['items'] if isinstance(c,dict) and c['items'][0]=='property'}
def apply(t,ed):
 for a,b,s in sorted(ed,reverse=True):t=t[:a]+s+t[b:]
 nodes(t);return re.sub(r'[ \t]+(?=\n|\Z)','',t)
def glabel(net,x,y):return f'(global_label "{net}" (shape passive) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid "{uid()}"))'
def globalize(t,names):
 ed=[]
 for n in items(t,'label'):
  if n['items'][1].strip('"') in names:
   s=t[n['start']:n['end']].replace('(label ','(global_label ',1)
   s=s.replace('(at ','(shape passive) (at ',1);ed.append((n['start'],n['end'],s))
 return apply(t,ed)

# Keep parent bytes from pre-MCP snapshot except the new hierarchy and deliberate nets.
p=B/'system_power_review.kicad_sch';t=p.read_text(encoding='utf-8')
(H/'root-after-mcp.kicad_sch').write_text(t,encoding='utf-8')
n=next(n for n in items(t,'sheet') if 'charger.kicad_sch' in t[n['start']:n['end']]);sheetid=child(n,'uuid')['items'][1].strip('"');sheet=t[n['start']:n['end']]
old=(H/'system_power_review.kicad_sch').read_text(encoding='utf-8');parentid=child(nodes(old),'uuid')['items'][1].strip('"')
t=old.rstrip()[:-1]+'\n'+sheet+'\n)\n'
# Remove the isolated SYS_RAW PWR_FLAG cluster: the charger now really drives it.
ed=[]
for n in nodes(t)['items']:
 if isinstance(n,dict) and n['items'][0] in ['symbol','label','wire']:
  m=re.search(r'\((?:at|xy) ([\d.]+) ([\d.]+)',t[n['start']:n['end']])
  if m and 29<float(m[1])<34 and abs(float(m[2])-154.94)<.01:ed.append((n['start'],n['end'],''))
t=globalize(apply(t,ed),{'SYS_RAW','VLOGIC_SWITCHED'}).replace('HW-PWR-010','HW-PWR-011')
p.write_text(t,encoding='utf-8')
p=B/'backlight.kicad_sch';t=p.read_text(encoding='utf-8');p.write_text(globalize(t,{'VLOGIC_SWITCHED'}),encoding='utf-8')

# Import charger; remap component references and hierarchy instance paths.
p=B/'charger.kicad_sch';empty=p.read_text(encoding='utf-8');(H/'charger-empty.kicad_sch').write_text(empty,encoding='utf-8')
newid=child(nodes(empty),'uuid')['items'][1]
source=ROOT/'hardware/candidates/power_path_core_review/power_path_core_review/power_path_core_review.kicad_sch'
t=source.read_text(encoding='utf-8');ed=[]
for n in items(t,'symbol'):
 pr=props(n);ref=pr['Reference']['items'][2].strip('"');s=t[n['start']:n['end']]
 m=re.fullmatch(r'([URCJ])(\d+)',ref)
 newref=m[1]+str(int(m[2])+100) if m else '#PWR'+str(100000+int(re.search(r'\d+',ref)[0]))
 s=s.replace('"'+ref+'"','"'+newref+'"')
 inst=child(nodes(s),'instances')
 replacement=f'(instances (project "system_power_review" (path "/{parentid}/{sheetid}" (reference "{newref}") (unit 1))))'
 s=s[:inst['start']]+replacement+s[inst['end']:]
 ed.append((n['start'],n['end'],s))
u=child(nodes(t),'uuid');ed.append((u['start'],u['end'],f'(uuid {newid})'))
t=apply(t,ed);ed=[]
# Remove redundant input/GND flag clusters (USB and parent already provide flags).
for n in nodes(t)['items']:
 if isinstance(n,dict) and n['items'][0] in ['symbol','label','wire']:
  m=re.search(r'\((?:at|xy) ([\d.]+) ([\d.]+)',t[n['start']:n['end']])
  if m and 29<float(m[1])<50 and abs(float(m[2])-25.4)<.01:ed.append((n['start'],n['end'],''))
t=apply(t,ed)
# Replace only the two EN pulldowns' GND terminals with VBUS pullups.
ed=[]
for ref in ['R107','R108']:
 n=next(n for n in items(t,'symbol') if props(n)['Reference']['items'][2]=='"'+ref+'"')
 x,y=map(float,child(n,'at')['items'][1:3]);pin=(x,y+3.81)
 wire=next(w for w in items(t,'wire') if any(abs(float(c['items'][1])-pin[0])<.01 and abs(float(c['items'][2])-pin[1])<.01 for c in child(w,'pts')['items'] if isinstance(c,dict)))
 xy=[tuple(map(float,c['items'][1:3])) for c in child(wire,'pts')['items'] if isinstance(c,dict)]
 end=next(v for v in xy if abs(v[0]-pin[0])>.01 or abs(v[1]-pin[1])>.01)
 g=next(g for g in items(t,'symbol') if child(g,'lib_id')['items'][1]=='"power:GND"' and all(abs(float(a)-b)<.01 for a,b in zip(child(g,'at')['items'][1:3],end)))
 ed.append((g['start'],g['end'],glabel('VBUS_IN',*end)))
 v=props(n)['Value'];s=t[v['start']:v['end']];s=re.sub(r'^(\(property "Value") "[^"]*"',r'\1 "10k 1%"',s);ed.append((v['start'],v['end'],s))
t=apply(t,ed)
t=globalize(t,{'VBUS_IN','SYS_RAW','VLOGIC_SWITCHED','USB_EN1','USB_EN2'})
tb=child(nodes(t),'title_block');t=t[:tb['start']]+'(title_block (title "Mini Companion - INTEGRATED CHARGER REVIEW") (date "2026-09-27") (rev "HW-PWR-011") (comment 1 "CC high-current path connected; default USB and BC1.2 not implemented") (comment 2 "Cell-body NTC and protected 4.2V pack required; NOT FOR FABRICATION"))'+t[tb['end']:]
p.write_text(t,encoding='utf-8')

# Supervisor survives loss of USB_3V3. Change only identified pin terminals.
p=B/'usb_qualify.kicad_sch';t=p.read_text(encoding='utf-8');(H/'qualify-after-mcp.kicad_sch').write_text(t,encoding='utf-8');ed=[]
for n in items(t,'global_label'):
 a=child(n,'at');xy=tuple(map(float,a['items'][1:3]))
 if xy in [(76.2,66.04),(88.9,48.26),(43.18,29.21)]:
  assert n['items'][1]=='"USB_3V3"'
  ed.append((n['start'],n['end'],t[n['start']:n['end']].replace('"USB_3V3"','"VBUS_IN"',1)))
for n in items(t,'symbol'):
 pr=props(n);ref=pr['Reference']['items'][2].strip('"')
 if ref in ['R11','R12']:
  v=pr['Value'];s=t[v['start']:v['end']];value='22k 1%' if ref=='R11' else '47k 1%';s=re.sub(r'^(\(property "Value") "[^"]*"',lambda m:m[1]+' "'+value+'"',s);ed.append((v['start'],v['end'],s))
t=apply(t,ed);p.write_text(t,encoding='utf-8')
print('Core imported with R/U/C/J +100 references; EN pullups and supervisor supply changed.')
