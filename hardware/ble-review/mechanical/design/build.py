"""Build the six-piece BLE mechanical study with original board interfaces.

This writes only this isolated enclosure's design/step/stl/mesh directories.
No KiCad loading, edits, refill, source copy or production release is performed.
"""
from __future__ import annotations
import json, math, hashlib, sys, time
from pathlib import Path
import cadquery as cq
import trimesh
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'design/parameters.json').read_text(encoding='utf8'))
for rel in ['step/global','mesh/global','stl']:(ROOT/rel).mkdir(parents=True,exist_ok=True)
(ROOT/'design/BUILD_STATUS.json').write_text(json.dumps({'status':'building','revision':P['revision']}),encoding='utf8')
C=P['case']; X=C['width'];Y=C['length'];H=C['height'];S=C['split_z'];W=C['wall']
parts={}

def box(x0,y0,z0,x1,y1,z1):
    assert x1>x0 and y1>y0 and z1>z0,(x0,y0,z0,x1,y1,z1)
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def bbox_shape(bb):return box(*bb)
def rounded(x0,y0,z0,x1,y1,z1,r):
    b=cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0,centered=(False,False,False)).translate((x0,y0,z0))
    return b.edges('|Z').fillet(r).val() if r>0 else b.val()
def inset_body(inset,z0,z1):
    return rounded(inset,inset,z0,X-inset,Y-inset,z1,C['corner_radius']-inset)
def cylinder(x,y,z0,z1,r):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
def cyl_axis(pos,direction,length,r):return cq.Solid.makeCylinder(r,length,cq.Vector(*pos),cq.Vector(*direction))
def union(*items):
    out=items[0]
    for q in items[1:]:out=out.fuse(q)
    return out.clean()
def add(key,shape,role,color,print_key=None,flip_print=False,notes=None):
    assert key not in parts
    shape=shape.clean()
    assert shape.isValid(),('Invalid BRep',key)
    assert len(shape.Solids())==1,('Not exactly one solid',key,len(shape.Solids()))
    assert shape.Volume()>0,('Nonpositive volume',key)
    parts[key]={'shape':shape,'role':role,'color':color,'print_key':print_key,'flip_print':flip_print,'notes':notes or []}
    return shape
def shell_cuts(shape):
    u=P['usb'];shape=shape.cut(box(u['center_x']-u['opening_width']/2,u['cut_y_start'],u['center_z']-u['opening_height']/2,u['center_x']+u['opening_width']/2,Y+.2,u['center_z']+u['opening_height']/2))
    return shape.cut(bbox_shape(P['power']['window_bbox'])).clean()
def side_holes(shape,front_part=False):
    q=P['closure'];z=q['side_screw_z']
    for y in q['side_screw_y']:
        for left in [True,False]:
            start=(-.1,y,z) if left else (X+.1,y,z)
            d=(1,0,0) if left else (-1,0,0)
            shape=shape.cut(cyl_axis(start,d,2.3,q['clearance_diameter']/2))
            if front_part:
                # A separate shorter pilot preserves the fixed thread block.
                p=(2.2,y,z) if left else (X-2.2,y,z)
                shape=shape.cut(cyl_axis(p,d,4.75,q['pilot_diameter']/2))
            # Axis Z8.9 keeps the entire 4.2mm head below the Z11.4 split.
            shape=shape.cut(cq.Solid.makeCone(q['head_diameter']/2,q['clearance_diameter']/2,q['countersink_depth'],cq.Vector(0 if left else X,y,z),cq.Vector(*d)))
    return shape.clean()

# Front cup and its electronic supports.
front=inset_body(0,0,S).cut(inset_body(W,C['front_floor'],S+.2))
l=P['lcd'];pc=P['pcb'];b=P['buttons']
cx,cy=l['pocket_center'];pw,ph=l['pocket_size']
front=front.cut(rounded(cx-pw/2,cy-ph/2,l['pocket_bottom_z'],cx+pw/2,cy+ph/2,l['pocket_top_z'],.5))
cx,cy=l['active_center'];ww,wh=l['window_size']
front=front.cut(rounded(cx-ww/2,cy-wh/2,-.1,cx+ww/2,cy+wh/2,l['pocket_top_z']+.1,l['window_corner_radius']))
for x,y in b['centers']:front=front.cut(cylinder(x,y,-.1,3,b['hole_diameter']/2))
front=union(front,cylinder(*pc['h101'],C['front_floor']-.02,pc['bounds'][2],pc['h101_post_diameter']/2))
front=front.cut(cylinder(*pc['h101'],pc['h101_pilot_bottom_z'],7,pc['plastic_pilot']/2))
clip_top=pc['bounds'][5]+pc['clip_gap']
for x,y in pc['clip_centers']:
    # Wide beams stop outside the PCB; only a 0.6x1 contact enters its edge.
    if x<X/2:
        beam=box(W-.02,y-1.5,C['front_floor']-.02,12.45,y+1.5,pc['bounds'][2])
        toe=box(12.40,y-.5,C['front_floor']-.02,13.1,y+.5,pc['bounds'][2])
    else:
        beam=box(57.55,y-1.5,C['front_floor']-.02,X-W+.02,y+1.5,pc['bounds'][2])
        toe=box(56.9,y-.5,C['front_floor']-.02,57.60,y+.5,pc['bounds'][2])
    front=union(front,beam,toe,cylinder(x,y,C['front_floor']-.02,pc['bounds'][2],pc['clip_post_diameter']/2))
    front=front.cut(cylinder(x,y,3.1,clip_top+.1,pc['plastic_pilot']/2))
bat=P['battery']
q=P['closure']
groove=inset_body(q['front_groove_outside_inset'],*q['front_groove_z']).cut(inset_body(q['front_groove_inside_inset'],q['front_groove_z'][0]-.1,q['front_groove_z'][1]+.1))
front=front.cut(groove)
for y in q['side_screw_y']:
    for left in [True,False]:
        a,c=q['front_slot_left_x'] if left else q['front_slot_right_x']
        front=front.cut(box(a,y-q['front_slot_y_half'],q['front_slot_z'][0],c,y+q['front_slot_y_half'],q['front_slot_z'][1]))
        a,c=q['left_front_thread_x'] if left else q['right_front_thread_x']
        block=box(a,y-q['tongue_y_half'],C['front_floor']-.02,c,y+q['tongue_y_half'],q['tongue_z'][1])
        # Local room for the removable LCD retainer and its screw head.
        block=block.cut(cylinder(l['clip_x'][0 if left else 1],l['clip_y'][0],3.9,7.2,2.85))
        front=union(front,block)
front=side_holes(shell_cuts(front),front_part=True)
# Front exported only after the integral cradle and left retainer are added.

# Rear cup. The low locator lip and horizontal screw tongues stay below pack.
rear=inset_body(0,S,H).cut(inset_body(W,S-.2,H-C['rear_floor']))
lip=inset_body(q['lip_outside_inset'],*q['lip_z']).cut(inset_body(q['lip_inside_inset'],q['lip_z'][0]-.1,q['lip_z'][1]+.1))
rear=union(rear,lip)
for y in q['side_screw_y']:
    for left in [True,False]:
        x0,x1=q['left_tongue_x'] if left else q['right_tongue_x']
        tongue=box(x0,y-q['tongue_y_half'],q['tongue_z'][0],x1,y+q['tongue_y_half'],q['tongue_z'][1])
        rear=union(rear,tongue)
# Right retainer is behind the pack, leaving its rigid insertion path open.
right_y=pc['clip_centers'][1][1]
rear=union(rear,box(59.2,right_y-1.5,clip_top,62.0,right_y+1.5,H-C['rear_floor']+.02),
    box(56.9,right_y-.5,clip_top,62.0,right_y+.5,clip_top+1.6))
rear=side_holes(shell_cuts(rear))
# Rear exported after the cradle is fused.

# Fill obsolete clip pilots; the two supporting ledges stay open at the top.
for x,y in pc['clip_centers']:
    front=union(front,cylinder(x,y,3.1,pc['bounds'][2],pc['plastic_pilot']/2))
# Captive recessed buttons. Switch travel/preload is a dry-fit gate.
for i,(x,y) in enumerate(b['centers']):
    cap=cylinder(x,y,b['face_z'],b['flange_front_z']+.02,b['cap_diameter']/2)
    flange=cylinder(x,y,b['flange_front_z'],b['flange_rear_z'],b['flange_diameter']/2)
    tip=cylinder(x,y,b['flange_rear_z']-.02,b['tip_end_z'],b['tip_diameter']/2)
    add(f'button_{i+1}',union(cap,flange,tip),'printed key plunger',[.91,.91,.84],'button',False,['Dry-fit tip coupon; tactile switch height and travel unqualified'])

# Integral insulated battery cradle, genuinely fused to the removable rear shell.
bb=bat['body_bbox'];z0,z1=bat['tray_z']
tray=box(bb[0],bb[1],z0,bb[3],bb[4],z1)
for x,y in bat['tray_posts']:
    disc=cylinder(x,y,z0,z1,2.8)
    bridge=box(x-2,y if y<bb[1] else bb[4]-.02,z0,x+2,bb[1]+.02 if y<bb[1] else y,z1)
    tray=union(tray,disc,bridge)
# Wider end tabs contain real soft-strap and wire-anchor slots.
tray=union(tray,box(10,2.4,z0,31,5.55,z1),box(10,57.95,z0,31,61.8,z1))
for a,c in bat['tray_stop_y']:
    tray=union(tray,box(bb[0]+1,a,z0,bb[3]-1,c,bat['tray_stop_top_z']))
tray=tray.intersect(box(0,bat['tray_tab_min_y'],13.1,70,70,16.2))
tray=union(tray,box(1.78,5.5,z0,2.55,58,z1),box(10,1.78,z0,31,2.45,z1),
    cylinder(33,60.8,z1-.02,H-C['rear_floor']+.02,2.0))
rear=union(rear,tray)
# SS-12D01 is mounted on its side in a dedicated rear-shell seat, with
# three leads pointing inward. The manufacturer drawing has no fixing holes.
power=P['power']
rear=union(rear,box(61.5,61.8,12.8,68.3,68.3,28.22))
# Clear the existing front-shell side-screw block by 0.3mm; keep the
# mounting-screw boss at Y=65 intact rather than allowing a shell overlap.
rear=rear.cut(box(63.0,61.7,12.7,68.4,64.2,13.5))
rear=rear.cut(box(*power['body_cavity_bbox']))
rear=rear.cut(box(65.4,64.0,18.4,70.2,66.0,22.4))
rear=rear.cut(box(*power['flange_cavity_bbox'])).cut(box(*power['window_bbox']))
for z in power['mount_screw_axis_z']:
    rear=rear.cut(cyl_axis((61.4,65,z),(1,0,0),.6,2.1))
    rear=rear.cut(cyl_axis((61.4,65,z),(1,0,0),4.2,1.1))
    rear=rear.cut(cyl_axis((65.6,65,z),(1,0,0),2.7,.85))
# Wire anchor lies behind the pack; opening load must reach this loop rather
# than the switch solder joints. Wire routing/service slack still need trial.
anchor=box(46,66.0,18,50,68.3,22).cut(box(47,66.5,17.8,49,67.3,22.2))
rear=union(rear,anchor)
# Left upper PCB restraint joins the tray from below, outside the PCB edge.
x,y=pc['clip_centers'][0]
rear=union(rear,cylinder(x,y,clip_top,13.22,2.6),
    box(x,y-.5,clip_top,13.1,y+.5,clip_top+1.6))
for slot in bat['strap_slots']+[bat['ntc_strain_relief_slot']]:
    rear=rear.cut(box(*slot))
# Machine access through the rear wall only. The tool approaches along the back normal.
ports = P['service_ports']
sx, sy = ports['SERVICE']['xy_mm']
sw, sl = ports['SERVICE']['opening_xy_mm']
bx, by = ports['BOOT']['xy_mm']
z0, z1 = H - C['rear_floor'] - 0.1, H + 0.1
rear = rear.cut(rounded(sx - sw/2, sy - sl/2, z0, sx + sw/2, sy + sl/2, z1, 1.0))
rear = rear.cut(cylinder(bx, by, z0, z1, ports['BOOT']['opening_diameter_mm']/2))
add('rear_shell',rear,'printed housing with integral cradle and two PCB restraints',[.20,.49,.52],'rear_shell',True,
    ['Integral cradle is 1.4mm thick; no battery-tray screws. Soft liner/straps/NTC attachment require physical qualification.',
     'Battery/probe move with rear; harness strain relief and controlled service loop required; support removal access must be checked by slicer.'])
add('front_shell',front,'printed housing with integral PCB and LCD seating supports',[.055,.12,.22],'front_shell',False,
    ['LCD retention uses separately costed compliant adhesive patches; no brittle snap-through action required.'])

# New captive cap for the side-mounted SS-12D01 actuator; no old linkage.
slider=union(cyl_axis((68,65,20.4),(1,0,0),1.9,1.6),box(67.3,62.6,19.2,68.02,67.4,21.6))
slider=slider.cut(box(67.1,64.05,19.45,69.6,65.95,21.35))
add('power_slider',slider,'printed SS-12D01 captive actuator cap',[.91,.91,.84],'power_slider',True,
    ['Nominal 1.5mm shaft, 1.9mm square cap cavity and +/-1mm Z motion. Fit/force/end stops require real-switch coupon; cap does not retain switch body.'])

# Analytical reference geometry; these are never included in printable STLs.
pcb=rounded(*pc['bounds'],pc['corner_radius']).cut(cylinder(*pc['h101'],6.5,8.4,pc['h101_drill']/2))
add('ref_pcb',pcb,'reference PCB (not printable)',[.13,.44,.26])
add('ref_lcd',bbox_shape(l['body_max_bbox']),'reference maximum LCD',[.16,.17,.18])
aa=l['active_center'];aas=l['active_size']
add('ref_lcd_active_area',box(aa[0]-aas[0]/2,aa[1]-aas[1]/2,1.48,aa[0]+aas[0]/2,aa[1]+aas[1]/2,1.50),'reference active display face',[.12,.58,.75])
add('ref_protected_pack',bbox_shape(bb),'reference protected battery maximum',[.68,.70,.72])
switch=box(*P['power']['body_bbox'])
for z in P['power']['pin_center_z']:
    switch=union(switch,box(57,64.85,z-.25,62.02,65.15,z+.25))
add('ref_ss12_body_pins',switch,'reference SS-12D01 nominal body and pins',[.65,.67,.7])
add('ref_ss12_actuator',box(*P['power']['actuator_bbox']),'reference SS-12D01 midpoint actuator',[.25,.25,.25])

for i,tape_bb in enumerate(l['adhesive_reference_bboxes']):
    add('ref_lcd_tape_'+str(i+1),box(*tape_bb),'reference compliant adhesive (not printable)',[.9,.6,.2])

def bounding(s):
    # CadQuery's usual box may expand by cached STL deflection after export.
    # Use analytic OCC bounds, independent of the cached triangulation.
    b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
    return list(b.Get())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
metadata=[];print_groups={};assembly=cq.Assembly(name=P['revision'])
mesh_tol=P['mesh']['linear_tolerance'];mesh_ang=P['mesh']['angular_tolerance']
for name,item in parts.items():
    s=item['shape'];bbx=bounding(s)
    stp=ROOT/'step/global'/f'{name}.step';stl=ROOT/'mesh/global'/f'{name}.stl'
    cq.exporters.export(s,str(stp),exportType='STEP')
    cq.exporters.export(s,str(stl),exportType='STL',tolerance=mesh_tol,angularTolerance=mesh_ang)
    color=cq.Color(*item['color']);assembly.add(s,name=name,color=color)
    m=trimesh.load(str(stl),force='mesh',process=True)
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,('Bad exported mesh',name)
    row={k:v for k,v in item.items() if k!='shape'}
    row.update({'id':name,'name':name,'label':name.replace('_',' '),'kind':'print' if item['print_key'] else 'reference','rgba':item['color']+[1.0],'assembly_transform':{'rotation_about_x_deg':0,'translation_mm':[0,0,0]},'global_bbox_mm':bbx,'volume_mm3':s.Volume(),'solid_count':len(s.Solids()),'brep_valid':s.isValid(),'global_step':str(stp.relative_to(ROOT)).replace('\\','/'),'STEP':str(stp.relative_to(ROOT)).replace('\\','/'),'global_stl':str(stl.relative_to(ROOT)).replace('\\','/'),'stl_watertight':bool(m.is_watertight),'stl_winding_consistent':bool(m.is_winding_consistent),'stl_volume_mm3':float(m.volume),'stl_sha256':sha(stl),'step_sha256':sha(stp)})
    key=item['print_key']
    if key:
        flat=s.rotate((0,0,0),(1,0,0),180) if item['flip_print'] else s
        bbb=bounding(flat);translation=[-bbb[i] for i in range(3)]
        flat=flat.translate(tuple(translation))
        print_transform={'rotation_about_x_deg':180 if item['flip_print'] else 0,'translation_after_rotation_mm':translation}
        if key not in print_groups:
            out=ROOT/'stl'/f'PRINT_{key}.stl'
            cq.exporters.export(flat,str(out),exportType='STL',tolerance=mesh_tol,angularTolerance=mesh_ang)
            sm=trimesh.load(str(out),force='mesh',process=True)
            assert sm.is_watertight and abs(sm.bounds[0,2])<1e-5,('Print mesh/bottom failure',key)
            print_groups[key]={'file':str(out.relative_to(ROOT)).replace('\\','/'),'quantity':0,'source_instance':name,'global_flip_about_x_180':item['flip_print'],'transform':print_transform,'normalized_bbox_mm':bounding(flat),'sha256':sha(out),'watertight':bool(sm.is_watertight),'note':'Orientation is provided as a starting point; supports, tolerance coupon, slicing and physical fit are not validated. Front cantilever bridge requires local supports.'}
        print_groups[key]['quantity']+=1
        row['print_stl']=print_groups[key]['file']
        row['print_transform']=print_transform
    metadata.append(row)
    print(json.dumps({'built':name,'volume_mm3':round(s.Volume(),3),'solid_count':len(s.Solids())}),flush=True)
assembly.export(str(ROOT/'step/ASSEMBLY_WITH_REFERENCE_ENVELOPES.step'),exportType='STEP')
printed=cq.Assembly(name=P['revision']+'_PRINTED_PARTS_ONLY')
for name,item in parts.items():
    if item['print_key']:printed.add(item['shape'],name=name,color=cq.Color(*item['color']))
printed.export(str(ROOT/'step/ASSEMBLED_PRINTED_PARTS.step'),exportType='STEP')
result={'revision':P['revision'],'status':P['status'],'units':'mm','source_board_sha256':P['source_board_sha256'],'parameters_sha256':sha(ROOT/'design/parameters.json'),'cadquery_version':cq.__version__,'parts':metadata,'print_groups':print_groups,'printed_physical_piece_count':sum(g['quantity'] for g in print_groups.values()),'unique_print_stl_count':len(print_groups),'reference_parts_excluded_from_print':True,'limits':['BRep and STL integrity checks are numerical geometry checks only.','The design has never been printed or fitted to a physical board/display/pack.','MPN heights, screws, side preload, key travel, slider stroke, FPC, new power switch and battery restraint still require first-article validation.','No production, thermal, battery, ingress or fire-rating release.']}
(ROOT/'design/model_metadata.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
(ROOT/'design/BUILD_SELF_CHECKS.json').write_text(json.dumps({'passed':True,'printed_physical_piece_count':result['printed_physical_piece_count'],'unique_print_stl_count':len(print_groups),'all_brep_single_valid_positive_solids':True,'all_exported_stl_watertight_consistent_positive':True,'all_print_stls_min_z_zero':True,'source_board_sha256':P['source_board_sha256'],'scope':'Integrity only; exported-solid clearance and assembly path review required; old interfaces only; physical/production fit not validated'},indent=2),encoding='utf8')
(ROOT/'design/BUILD_STATUS.json').write_text(json.dumps({'status':'integrity passed; clearance review pending','revision':P['revision'],'parameters_sha256':result['parameters_sha256']},indent=2),encoding='utf8')
print(json.dumps({'build_passed':True,'part_count':len(parts),'printed_pieces':result['printed_physical_piece_count'],'unique_print_stls':len(print_groups)}),flush=True)
