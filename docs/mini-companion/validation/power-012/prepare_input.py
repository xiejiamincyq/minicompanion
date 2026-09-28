"""One-shot parent-cache preservation after MCP child creation."""
from pathlib import Path
import sys,re
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from format_review_fields import nodes,child
B=H.parents[3]/'hardware/candidates/system_power_review'
p=B/'system_power_review.kicad_sch';t=p.read_text(encoding='utf-8')
(H/'root-after-mcp.kicad_sch').write_text(t,encoding='utf-8')
s=next(n for n in nodes(t)['items'] if isinstance(n,dict) and n['items'][0]=='sheet' and 'usb_input.kicad_sch' in t[n['start']:n['end']])
old=(H/'root-before.kicad_sch').read_text(encoding='utf-8').rstrip()
p.write_text(old[:-1]+'\n'+t[s['start']:s['end']]+'\n)\n',encoding='utf-8')
p=B/'sym-lib-table';t=p.read_text(encoding='utf-8')
assert 'MiniCompanionInput' not in t
t=t.replace('(version 7)','(version 7)\n  (lib (name "MiniCompanionInput")(type "KiCad")(uri "${KIPRJMOD}/output/symbols/TPS259470LRPWR.kicad_sym")(options "")(descr "Review input protection"))')
p.write_text(t,encoding='utf-8')
