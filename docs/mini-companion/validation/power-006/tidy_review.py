"""Move the isolated output-port drawing off the title block; preserve nets.

Run once after format_review_fields.py. The before/after CLI netlist contract
must pass. Only J2's complete terminal cluster is translated, by 101.6 mm left.
"""
from pathlib import Path
import re
from format_review_fields import nodes, child, SCH

text = SCH.read_text(encoding='utf-8')
backup = Path(__file__).with_name('system-before-port-move.kicad_sch')
if backup.exists():
    text = backup.read_text(encoding='utf-8')
else:
    backup.write_text(text, encoding='utf-8')
edits = []
for n in nodes(text)['items'][1:]:
    if not isinstance(n, dict) or n['items'][0] not in ('symbol', 'label', 'wire'):
        continue
    block = text[n['start']:n['end']]
    coords = list(re.finditer(r'\((?:at|xy) ([\d.]+) ([\d.]+)', block))
    if not coords:
        continue
    x, y = map(float, coords[0].groups())
    if x > 230 and y > 160:
        block = re.sub(r'\((at|xy) ([\d.]+) ([\d.]+)',
                       lambda m: f'({m[1]} {float(m[2])-101.6:.4f} {m[3]}', block)
        edits.append((n['start'], n['end'], block))
for a, b, replacement in sorted(edits, reverse=True):
    text = text[:a] + replacement + text[b:]
# The auto-generated small IC body needs smaller pin text. Apply identically
# to the library and the embedded cache; no names/numbers/coordinates change.
def small_pins(t):
    return t.replace('(offset 1.016)', '(offset 0.254)').replace('(size 1.27 1.27)', '(size 0.9 0.9)')
root = nodes(text)
lib = child(root, 'lib_symbols')
chip = next(n for n in lib['items'] if isinstance(n, dict) and 'TPS63802DLAR' in str(n['items'][:2]))
text = text[:chip['start']] + small_pins(text[chip['start']:chip['end']]) + text[chip['end']:]
text = re.sub(r'[\t ]+(?=\r?\n|\Z)', '', text)
SCH.write_text(text, encoding='utf-8')
lib_path = SCH.parent/'output/symbols/TPS63802DLAR.kicad_sym'
lib_path.write_text(small_pins(lib_path.read_text(encoding='utf-8')), encoding='utf-8')
print('Translated', len(edits), 'output-port drawing objects; smaller IC pin font.')
