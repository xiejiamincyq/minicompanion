"""Read-only comparison of two boards serialized by the same KiCad version.

Ignores ordering of top-level objects; reports every changed object.
No design data is edited by this parser.
"""
import json
import re
import sys
from pathlib import Path


def read(path):
    stack = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', Path(path).read_text(encoding='utf-8')):
        if token == '(':
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ')':
            stack.pop()
        else:
            stack[-1].append(token)
    assert len(stack) == 1
    return stack[0][0]


def objects(tree):
    result = {}
    for node in tree[1:]:
        uid = next((v[1] for v in node[1:] if isinstance(v, list) and v[0] == 'uuid'), None)
        key = node[0] + ':' + (uid or str(sum(k.startswith(node[0] + ':') for k in result)))
        result[key] = node
    return result


if __name__ == '__main__':
    a, b = [objects(read(p)) for p in sys.argv[1:3]]
    changes = []
    for key in sorted(a.keys() | b.keys()):
        if a.get(key) != b.get(key):
            changes.append({'key': key, 'before': a.get(key), 'after': b.get(key)})
    print(json.dumps(changes, ensure_ascii=False, indent=2))
