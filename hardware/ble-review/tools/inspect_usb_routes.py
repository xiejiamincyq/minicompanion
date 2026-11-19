"""Read-only native KiCad PCB measurements; run with KiCad's bundled Python.

Writes verification/usb_route_metrics.json only. Does not fill or save the PCB.
Centerline lengths exclude package/pad-to-die and vertical via-barrel delay;
they describe geometry, not USB signal-integrity qualification.
"""
from pathlib import Path
import collections,hashlib,heapq,json,math
import pcbnew as pc
ROOT=Path(__file__).resolve().parent.parent;FILE=ROOT/'project/mini_companion_integrated.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(FILE);b=pc.LoadBoard(str(FILE));fps={f.GetReference():f for f in b.GetFootprints()}
xy=lambda p:(p.x/1e6,p.y/1e6)
roundpt=lambda p:(round(p[0],6),round(p[1],6))
def cross(a,z):return a[0]*z[1]-a[1]*z[0]
def sub(a,z):return(a[0]-z[0],a[1]-z[1])
def pad(ref,pin):return next(p for p in fps[ref].Pads() if p.GetNumber()==pin)
contracts={
 'USB_DP_CONN':[(('J201','A6'),('U1101','10')),(('J201','B6'),('U1101','10')),(('D7301','1'),('J201','A6'))],
 'USB_DM_CONN':[(('J201','A7'),('U1101','14')),(('J201','B7'),('U1101','14')),(('D7301','2'),('J201','B7'))],
 'USB_DP_ISO':[(('U1101','9'),('R7302','1'))],
 'USB_DM_ISO':[(('U1101','13'),('R7303','1'))],
 'MCU_USB_DP':[(('R7302','2'),('U101','24'))],
 'MCU_USB_DM':[(('R7303','2'),('U101','23'))],
}
report={'board_sha256':before,'method':'Native saved copper; planar segment-centerline graph, exact same-net crossings split; pad-center and via coordinates. Vertical via lengths and package delays excluded.','nets':{},'physical_usb_qualification':False}
for net,paths in contracts.items():
 ts=[t for t in b.GetTracks() if t.GetNetname()==net];tracks=[t for t in ts if not isinstance(t,pc.PCB_VIA)];vias=[t for t in ts if isinstance(t,pc.PCB_VIA)]
 graph=collections.defaultdict(list);segments=[]
 def add(a,z,w,via=None):
  if a!=z:graph[a].append((z,w,via));graph[z].append((a,w,via))
 for t in tracks:
  assert not isinstance(t,pc.PCB_ARC),'Arc graph measurement not implemented'
  a,z=xy(t.GetStart()),xy(t.GetEnd());segments.append({'a':a,'z':z,'layer':t.GetLayer(),'points':{a,z}})
 for i,one in enumerate(segments):
  a=one['a'];r=sub(one['z'],a)
  for two in segments[i+1:]:
   if one['layer']!=two['layer']:continue
   c=two['a'];s=sub(two['z'],c);den=cross(r,s);ca=sub(c,a)
   if abs(den)>1e-12:
    u=cross(ca,s)/den;v=cross(ca,r)/den
    if -1e-8<=u<=1+1e-8 and -1e-8<=v<=1+1e-8:
     q=roundpt((a[0]+u*r[0],a[1]+u*r[1]));one['points'].add(q);two['points'].add(q)
   elif abs(cross(ca,r))<1e-8:
    for owner,other in [(one,two),(two,one)]:
     for q in [other['a'],other['z']]:
      if abs(math.dist(owner['a'],q)+math.dist(q,owner['z'])-math.dist(owner['a'],owner['z']))<1e-6:owner['points'].add(q)
 for s in segments:
  ordered=sorted(s['points'],key=lambda q:math.dist(s['a'],q))
  for a,z in zip(ordered,ordered[1:]):add((*a,s['layer']),(*z,s['layer']),math.dist(a,z))
 for v in vias:
  q=xy(v.GetPosition());layers=[l for l in [pc.F_Cu,pc.In1_Cu,pc.In2_Cu,pc.B_Cu] if v.IsOnLayer(l)]
  for i,l in enumerate(layers):
   for m in layers[i+1:]:add((*q,l),(*q,m),0,v.m_Uuid.AsString())
 # Pad centers coincide with routed endpoints in these generated escapes.
 # Connect other graph nodes inside the same pad at their centerline distance.
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()!=net:continue
   center=xy(p.GetPosition());l=f.GetLayer();key=(*center,l)
   for node in list(graph):
    if node[2]==l and math.dist(center,node[:2])<2 and p.HitTest(pc.VECTOR2I(round(node[0]*1e6),round(node[1]*1e6))):add(key,node,math.dist(center,node[:2]))
 measures=[]
 for start,end in paths:
  a=(*xy(pad(*start).GetPosition()),fps[start[0]].GetLayer());z=(*xy(pad(*end).GetPosition()),fps[end[0]].GetLayer())
  queue=[(0,a)];dist={a:0};parent={}
  while queue:
   d,n=heapq.heappop(queue)
   if d!=dist[n]:continue
   if n==z:break
   for nxt,w,via in graph[n]:
    nd=d+w
    if nd<dist.get(nxt,1e99)-1e-10:dist[nxt]=nd;parent[nxt]=(n,via);heapq.heappush(queue,(nd,nxt))
  assert z in dist,'Centerline graph disconnected for '+str((net,start,end))
  route=[z];used_vias=set();n=z
  while n!=a:
   n,via=parent[n];route.append(n)
   if via:used_vias.add(via)
  used_layers={b.GetLayerName(a[2]) for a,z in zip(route,route[1:]) if a[2]==z[2] and math.dist(a[:2],z[:2])>1e-9}
  measures.append({'from':'.'.join(start),'to':'.'.join(end),'planar_centerline_mm':round(dist[z],6),'through_vias_on_path':len(used_vias),'layers_on_path':sorted(used_layers),'path_points':[{'x':n[0],'y':n[1],'layer':b.GetLayerName(n[2])} for n in reversed(route)]})
 layer_lengths=collections.defaultdict(float)
 for t in tracks:layer_lengths[b.GetLayerName(t.GetLayer())]+=t.GetLength()/1e6
 report['nets'][net]={'total_copper_centerline_mm':round(sum(layer_lengths.values()),6),'length_by_layer_mm':{l:round(v,6) for l,v in layer_lengths.items()},'track_segments':len(tracks),'through_vias':len(vias),'widths_mm':sorted({t.GetWidth()/1e6 for t in tracks}),'paths':measures}
for orientation,index in [('A',0),('B',1)]:
 dp=report['nets']['USB_DP_CONN']['paths'][index]['planar_centerline_mm']+sum(report['nets'][n]['paths'][0]['planar_centerline_mm'] for n in ['USB_DP_ISO','MCU_USB_DP'])
 dm=report['nets']['USB_DM_CONN']['paths'][index]['planar_centerline_mm']+sum(report['nets'][n]['paths'][0]['planar_centerline_mm'] for n in ['USB_DM_ISO','MCU_USB_DM'])
 report['connector_'+orientation]={'DP_planar_mm':round(dp,6),'DM_planar_mm':round(dm,6),'absolute_planar_skew_mm':round(abs(dp-dm),6)}
ground_polys=[z.GetFilledPolysList(pc.In1_Cu) for z in b.Zones() if z.GetNetname()=='GND' and z.IsOnLayer(pc.In1_Cu) and not z.GetIsRuleArea()]
coverage={}
for net in contracts:
 total=covered=largest_gap=0.0
 for t in b.GetTracks():
  if t.GetNetname()!=net or isinstance(t,pc.PCB_VIA) or t.GetLayer()!=pc.F_Cu or t.GetWidth()!=284000:continue
  a,z=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(a,z);count=max(1,math.ceil(length/.1));step=length/count;run=0
  for i in range(count):
   f=(i+.5)/count;q=pc.VECTOR2I(round((a[0]+f*(z[0]-a[0]))*1e6),round((a[1]+f*(z[1]-a[1]))*1e6));total+=step
   if any(p.Contains(q) for p in ground_polys):covered+=step;run=0
   else:run+=step;largest_gap=max(largest_gap,run)
 if total:coverage[net]={'sampled_trunk_mm':round(total,6),'covered_by_saved_In1_GND_percent':round(100*covered/total,3),'max_uncovered_run_within_one_segment_mm':round(largest_gap,6)}
report['paired_trunk_reference_sampling']={'sample_step_at_most_mm':.1,'test':'Track centerline point over saved In1 GND filled copper only; not a field solver or impedance/return-path signoff.','nets':coverage}
assert before==sha(FILE),'Read-only inspection changed source unexpectedly'
(ROOT/'verification/usb_route_metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'board_sha256':before,'nets':{n:{k:v for k,v in d.items() if k!='paths'} for n,d in report['nets'].items()},'connector_A':report['connector_A'],'connector_B':report['connector_B']},indent=2))
