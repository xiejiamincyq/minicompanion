"""Export saved A2 schematic, portable XML metadata, native ERC and PDF.

Only source/uri XML metadata is normalized; component and net payloads remain
byte-for-byte native KiCad output. Paths are relative to hardware/ble-economy.
"""
from pathlib import Path
import os, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli')
if not CLI:
    fallback = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
    if fallback.is_file(): CLI = str(fallback)
if not CLI:
    raise SystemExit('Set KICAD_CLI or put kicad-cli on PATH.')
SCH = 'project/mini_companion_a2.kicad_sch'
XML = ROOT/'verification/a2_netlist.xml'

def run(*args):
    subprocess.run([CLI, *args], cwd=ROOT, check=True)

run('sch','export','netlist','--format','kicadxml','-o',str(XML.relative_to(ROOT)),SCH)
native = XML.read_text(encoding='utf-8')

def portable(match):
    value = match[2]
    if re.match(r'^(?:[A-Za-z]:[\\/]|[\\/])',value):
        p = Path(value)
        value = p.relative_to(ROOT).as_posix() # Outside-project paths fail closed.
    return match[1] + value + match[3]

normalized = re.sub(r'(<(?:source|uri)>)([^<]*)(</(?:source|uri)>)',portable,native)
XML.write_text(normalized,encoding='utf-8',newline='\n')
run('sch','erc','--format','json','--severity-all','--exit-code-violations',
    '-o','verification/a2_erc.json',SCH)
run('sch','export','pdf','-o','verification/a2_schematic.pdf',SCH)
subprocess.run([sys.executable,'design/verify_electrical.py'],cwd=ROOT,check=True)
