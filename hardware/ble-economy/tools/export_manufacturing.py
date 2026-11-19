"""Export saved A2 Gerber/Excellon/CPL; requires clean current verify_pcb.py receipt.
Run with KiCad 10 bundled Python. Writes manufacturing/, does not save CAD.
J1's footprint anchor is its mouth: JLC CPL uses its 13.4-mm housing midpoint.
"""
from pathlib import Path
import csv,hashlib,json,subprocess,zipfile
import pcbnew as p
B=Path(__file__).resolve().parents[1];P=B/'project/mini_companion_a2.kicad_pcb';M=B/'manufacturing';G=M/'gerber';G.mkdir(parents=True,exist_ok=True)
CLI=Path(p.__file__).resolve().parents[2]/'kicad-cli.exe';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
r=json.loads((B/'verification/a2_pcb_receipt.json').read_text(encoding='utf8'));assert sha(P)==r['pcb_sha256']
def run(*args):subprocess.run([str(CLI),*map(str,args)],check=True)
run('pcb','export','gerbers','-l','F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','-o',str(G)+'/',P)
jobpath=G/'mini_companion_a2-job.gbrjob'
job=json.loads(jobpath.read_text(encoding='utf8'));job['GeneralSpecs']['Finish']='OSP';job['GeneralSpecs']['Size']={'X':68.0,'Y':35.0}
jobpath.write_text(json.dumps(job,indent=2)+'\n',encoding='utf8')
run('pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-report','--report-path',M/'drill-report.txt','-o',str(G)+'/',P)
run('pcb','export','pos','--side','front','--format','csv','--units','mm','--use-drill-file-origin','--smd-only','--exclude-dnp','-o',M/'top-position-kicad.csv',P)
rows=list(csv.DictReader((M/'top-position-kicad.csv').open(newline='',encoding='utf8')));assert len(rows)==38
with (M/'top-position-jlc.csv').open('w',newline='',encoding='utf8')as f:
 w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
 for row in rows:
  xx=float(row['PosX']);yy=float(row['PosY']);rot=float(row['Rot'])%360
  if row['Ref']=='J1':assert abs(xx)<1e-6 and abs(yy-22.5)<1e-6 and abs(rot-90)<1e-6;xx+=6.7
  w.writerow([row['Ref'],f'{xx:.6f}',f'{yy:.6f}','Top',f'{rot:.6f}'])
with zipfile.ZipFile(M/'a2-gerber-drill.zip','w',zipfile.ZIP_DEFLATED)as z:
 for f in sorted(G.iterdir()):
  if f.is_file():z.write(f,f.name)
assert sha(P)==r['pcb_sha256']
manifest={'pcb_sha256':sha(P),'schematic_sha256':r['schematic_sha256'],'xml_sha256':r['xml_sha256'],'origin':'PCB bottom-left; mm; +Y upward','j1_placement_correction':{'footprint_anchor_local_top_left_mm':[0,12.5],'housing_pick_center_local_top_left_mm':[6.7,12.5],'jlc_cpl_mm':[6.7,22.5],'rotation_deg':90,'reason':'DC-050 13.4mm housing centre; anchor intentionally at mouth'},'fabrication_release':False,'files':{str(f.relative_to(M)).replace('\\','/'):sha(f)for f in sorted(M.rglob('*'))if f.is_file()and f.name!='manifest.json'}}
(M/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('Exported 38 top positions and Gerber/Excellon ZIP; CAD hash preserved.')
