"""Restore the cache dropped by MCP; retain new sheet and its connections.

Run once; backups preserve the failing input. Verify with official CLI afterwards.
"""
from pathlib import Path
import subprocess,sys,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'power-006'))
from format_review_fields import nodes,child
p=ROOT/'hardware/candidates/system_power_review/system_power_review.kicad_sch'
t=p.read_text(encoding='utf-8')
backup=HERE/'root-before-cache-repair.kicad_sch'
assert not backup.exists()
backup.write_text(t,encoding='utf-8')
old=subprocess.check_output(['git','show','9ad7b08:hardware/candidates/system_power_review/system_power_review.kicad_sch'],cwd=ROOT).decode('utf-8')
lib=child(nodes(old),'lib_symbols')
current=child(nodes(t),'lib_symbols')
t=t[:current['start']]+old[lib['start']:lib['end']]+t[current['end']:]
t=t.replace('(global_label "VLOGIC_SWITCHED"','(global_label "BL_SUPPLY"')
t=re.sub(r'[ \t]+(?=\n|\Z)','',t)
p.write_text(t,encoding='utf-8')
p=p.with_name('backlight.kicad_sch')
t=p.read_text(encoding='utf-8')
(HERE/'backlight-before-repair.kicad_sch').write_text(t,encoding='utf-8')
t=t.replace('(global_label "VLOGIC_SWITCHED"','(global_label "BL_SUPPLY"')
p.write_text(re.sub(r'[ \t]+(?=\n|\Z)','',t),encoding='utf-8')
print('Restored embedded library from 9ad7b08; cross-sheet alias BL_SUPPLY.')
