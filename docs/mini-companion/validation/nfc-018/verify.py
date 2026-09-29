"""Static interface budgets; conditional 25C analysis, not transient validation."""
import itertools,json,sys,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'final.xml');old,op=read(H.parent/'nfc-017/final.xml')
assert p==op and len(p)==74
def values(root):return {c.attrib['ref']:c.findtext('value') for c in root.findall('./components/comp')}
v,ov=values(r),values(old)
assert len(v)==25 and {k:(ov[k],v[k]) for k in v if ov[k]!=v[k]}=={'R5':('100k 1%','47k 1%')}
assert not any(s['violations'] for s in json.loads((H/'erc.json').read_text(encoding='utf-8'))['sheets'])
# Independent leakage magnitudes added as an engineering envelope. Test biases
# differ across sources, so this is not an all-bias guaranteed leakage model.
leak=2*2e-6+2*.25e-6+50e-9
def floating_low(r):return leak*r*1.01
assert floating_low(100000)>.45
assert floating_low(47000)<.45
# A request-high lower bound is conditional on GPIO meeting .8*VDD under load.
# 6Mohm SEL pulldowns are typical only and are omitted here; 2uA per SEL
# is already budgeted, not added a second time as a guaranteed resistor bound.
req=.8*3.137544
sel=(req/(10000*1.01)-leak)/(1/(10000*1.01)+1/(47000*.99))
assert sel>1.2
# Deliberately additive accuracy+load+line at 25C, not a temperature spec.
module=[3.3*(1-.02-.01-.0035),3.3*(1+.02+.01+.0035)]
host=[3.137544,3.222584]
fall=json.loads((H.parent/'nfc-017/verification.json').read_text())['rails']['host']['fall_V'][0]
def solve(h,m,rh,rm,ih,im,rs=4.5):
 # KCL for host and module bus nodes, leakage positive = current drawn.
 a,b,c=1/rh+1/rs,-1/rs,1/rm+1/rs
 d,e=h/rh-ih,m/rm-im
 det=a*c-b*b
 return (d*c-b*e)/det,(a*e-b*d)/det
def envelope(hosts):
 rows=[]
 for h,m,rh,rm,ih,im in itertools.product(hosts,module,[4700*.99,4700*1.01],[2200*.99,2200*1.01],[-.1e-6,.1e-6],[-20.05e-6,20.05e-6]):
  bh,bm=solve(h,m,rh,rm,ih,im)
  rows.append({'host_high_margin':bh-.75*h,'host_upper_margin':h+.3-bh,'module_high_margin':bm-.8*m,'module_upper_margin':m+.4-bm})
 return {k:min(x[k] for x in rows) for k in rows[0]}
normal=envelope(host);pretrip=envelope([fall])
assert min(normal.values())>0 and min(pretrip.values())>0
# Explicitly show unmonitored internal-rail collapse invalidates direct connect.
_,collapsed=solve(host[0],0,4700,2200,0,0)
assert collapsed>.4
report={'status':'conditional_static_only','components':25,'pins':74,'ERC_violations':0,
 'old_floating_SEL_V':floating_low(100000),'new_floating_SEL_V':floating_low(47000),
 'conditional_high_SEL_V':sel,'module_25C_budget_V':module,
 'normal_bus_min_margins_V':normal,'pretrip_bus_min_margins_V':pretrip,
 'collapsed_module_unclamped_bus_V':collapsed,
 'nominal_request_pulldown_current_uA':3.18/(10000+47000)*1e6,
 'ldo_pdf_sha256':hashlib.sha256((H/'TPAP7343D.pdf').read_bytes()).hexdigest(),
 'limits':['25C only; module pullup tolerance assumed 1 percent',
 'GPIO VOH specification is high-impedance-load, not a loaded/full-temperature guarantee',
 'Leakage limits quoted at differing bias conditions; characterize final operating points',
 'Unclamped collapse model demonstrates missing proof, not actual clamped pin voltage',
 'No dynamic, full-temperature or manufacturing approval']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
