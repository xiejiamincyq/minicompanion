"""Cosmetic-only fallback after MCP field auto-placement left visible overlaps.

Edits only placed-symbol field layout, label justification, and zero-offset
GND symbol orientation. Never changes symbols, pin numbers, wires or nets.
The official CLI netlists must be compared before accepting the output.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCH = ROOT / 'hardware/candidates/system_power_review/system_power_review.kicad_sch'


def nodes(text):
    stack = []
    root = None
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        t = m.group()
        if t == '(':
            n = {'start': m.start(), 'items': []}
            if stack:
                stack[-1]['items'].append(n)
            else:
                root = n
            stack.append(n)
        elif t == ')':
            stack.pop()['end'] = m.end()
        else:
            stack[-1]['items'].append(t)
    assert not stack
    return root


def child(n, key):
    return next((c for c in n['items'] if isinstance(c, dict) and c['items'][0] == key), None)


if __name__ == '__main__':
    text = SCH.read_text(encoding='utf-8')
    backup = Path(__file__).with_name('system-before-cosmetics.kicad_sch')
    if backup.exists():
        raise SystemExit('Refusing to replace previous cosmetic backup')
    backup.write_text(text, encoding='utf-8')
    edits = []

    def replace(n, value):
        edits.append((n['start'], n['end'], value))

    def field(p, x, y, justify='left'):
        replace(child(p, 'at'), f'(at {x:.4f} {y:.4f} 0)')
        eff = f'(effects (font (size 1.0 1.0))' + (f' (justify {justify})' if justify else '') + ')'
        replace(child(p, 'effects'), eff)

    for n in nodes(text)['items'][1:]:
        if not isinstance(n, dict):
            continue
        if n['items'][0] == 'symbol':
            props = {c['items'][1].strip('"'): c for c in n['items'] if isinstance(c, dict) and c['items'][0] == 'property'}
            if 'Reference' not in props:
                continue
            ref = props['Reference']['items'][2].strip('"')
            at = child(n, 'at')
            x, y = map(float, at['items'][1:3])
            lib = child(n, 'lib_id')['items'][1].strip('"')
            if lib == 'power:GND':
                replace(at, f'(at {x} {y} 0)')
                field(props['Value'], x, y + 3.3, '')
            elif ref == 'U1':
                field(props['Reference'], x + 12.7, y - 20.32)
                field(props['Value'], x + 12.7, y - 17.78)
            elif ref.startswith(('R', 'C', 'L')):
                field(props['Reference'], x + 3.81, y - 1.27)
                field(props['Value'], x + 3.81, y + 1.27)
            elif ref.startswith('J'):
                field(props['Reference'], x + 2.54, y - 1.27)
                field(props['Value'], x + 2.54, y + 1.27)
        elif n['items'][0] == 'label':
            at = child(n, 'at')
            x, y = map(float, at['items'][1:3])
            # U1 and connector left-facing terminals read away from the body.
            left = abs(x-114.3)<.01 or abs(x-107.95)<.01 or abs(x-237.49)<.01 or abs(x-22.86)<.01
            replace(child(n, 'effects'), '(effects (font (size 1.0 1.0)) (justify ' + ('right' if left else 'left') + ' bottom))')
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    text = re.sub(r'(?m)^[ \t]+$', '', text)
    nodes(text)
    SCH.write_text(text, encoding='utf-8')
    print(f'Applied {len(edits)} cosmetic field/label changes; no wire edits.')
