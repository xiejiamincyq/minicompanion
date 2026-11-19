"""Rebuild the A2 fits and print models. Coordinates in mm: x right, y down,
z from the front face towards the removable rear lid. CadQuery 2.8 + trimesh.
Optional: python build_case.py --core-step path/to/ESP32-S3-LCD-2-20250122.stp
"""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq
import trimesh

HERE = Path(__file__).resolve().parent
OUT = HERE / 'stl'
OUT.mkdir(exist_ok=True)
W, H = 80., 94.
FRONT, SPLIT, DEPTH = 2.4, 31.2, 33.4
BOARD_X, BOARD_Y, PCB_FRONT = 6., 52., 14.
CORE_BOSS_Z = 9.50
CORE_HOLES = [(x,y) for x in (6.5,48.7) for y in (12.,41.)]
SMALL_HOLES = [(BOARD_X+x, BOARD_Y+y) for x in (3.,65.) for y in (3.,32.)]
SHELL_HOLES = [(x,y) for x in (4.5,W-4.5) for y in (4.2,H-3.8)]
KEYS = [(BOARD_X+x, BOARD_Y+26.) for x in (12.,34.,56.)]
# The main power switch is registered to the right PCB edge.
SWITCH_Y = BOARD_Y+12.5
SWITCH_Z = PCB_FRONT-.9

def box(x,y,z,dx,dy,dz):
    return cq.Workplane('XY').box(dx,dy,dz, centered=(False,False,False)).translate((x,y,z))

def cylinder(x,y,z,r,h):
    return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z))

def rounded(x,y,z,dx,dy,dz,r):
    return box(x,y,z,dx,dy,dz).edges('|Z').fillet(r)

def along_x(x,y,z,r,length):
    return cq.Workplane('YZ').center(y,z).circle(r).extrude(length).translate((x,0,0))

def outer(z,h):
    return rounded(0,0,z,W,H,h,4.6)

def tray_model():
    tray = outer(0,SPLIT).cut(rounded(2.3,2.3,FRONT,W-4.6,H-4.6,SPLIT,2.6))
    # Wide aperture covers the active LCD on the bare/non-touch 30306.
    tray = tray.cut(rounded(3.9,9.55,-.2,47.35,33.85,FRONT+.4,.85))
    # Clear the glass down to z=1.30; the four rear M2 bosses support the module.
    tray = tray.cut(rounded(3.2,8.73,1.05,48.8,35.53,FRONT,1.1))
    # Micro board interface: same physical USB-C socket for RUN and PC service.
    tray = tray.cut(box(-.2,19.65,4.7,5.8,13.7,7.8))
    for y in (17.05,35.95):
        tray = tray.cut(along_x(-.2,y,7.9,1.55,4.3))
    # The side-split notch admits a finished RUN cable while closing the lid.
    tray = tray.cut(box(-.2,42.5,SPLIT-4.6,4.0,5.8,6.2))
    # Barrel tip body must clear the wall all the way to the board edge.
    tray = tray.cut(along_x(-.3,BOARD_Y+12.5,PCB_FRONT-6.55,6.2,7.2))
    tray = tray.cut(box(W-3.2,SWITCH_Y-4.4,SWITCH_Z-2.,3.5,8.8,4.0))
    for x,y in SHELL_HOLES:
        tray = tray.union(cylinder(x,y,FRONT,3.2,SPLIT-FRONT))
        tray = tray.cut(cylinder(x,y,SPLIT-8.5,.83,9.))
    for x,y in SMALL_HOLES:
        tray = tray.union(cylinder(x,y,FRONT,2.8,PCB_FRONT-FRONT))
        tray = tray.cut(cylinder(x,y,PCB_FRONT-5.6,.83,6.))
    for x,y in KEYS:
        tray = tray.cut(cylinder(x,y,-.2,3.8,FRONT+.4))
        guide = cylinder(x,y,FRONT,5.8,5.0).cut(cylinder(x,y,FRONT-.1,4.95,5.2))
        tray = tray.union(guide)
    # A sidewall eye beside the cable notch transfers pull to the harness jacket.
    for y in (44.6,50.8):
        tray=tray.union(box(1.9,y,22.8,5.8,1.65,2.1))
    tray=tray.union(box(6.1,44.6,22.8,1.6,7.85,2.1))
    # A straight sight line to the charge status LED, local (24,19.5).
    tray=tray.cut(cylinder(BOARD_X+24.,BOARD_Y+19.5,-.1,1.55,FRONT+.2))
    for legend,x,y,size in [('CHG',30.,67.6,2.1),('5V IN',11,64.5,2.4),('POWER',67.5,64.5,2.4),
                            ('A',KEYS[0][0],70.5,3.1),('B',KEYS[1][0],70.5,3.1),('C',KEYS[2][0],70.5,3.1)]:
        letters = cq.Workplane('XY').text(legend,size,.65,font='Arial',kind='bold',combine=True)
        cutter = letters.rotate((0,0,0),(1,0,0),180).translate((x,y,.45))
        tray = tray.cut(cutter)
    return tray

def lid_model():
    lid = outer(SPLIT,DEPTH-SPLIT)
    for x,y in SHELL_HOLES:
        lid = lid.cut(cylinder(x,y,SPLIT-.1,1.2,3.))
    for x,y in CORE_HOLES:
        lid = lid.union(cylinder(x,y,CORE_BOSS_Z,2.35,SPLIT-CORE_BOSS_Z+.05))
        lid = lid.cut(cylinder(x,y,CORE_BOSS_Z-.1,1.12,DEPTH-CORE_BOSS_Z+.2))
        # M2x25 head bears on the shelf at z32.4, leaving 2.10 mm engagement.
        lid = lid.cut(cylinder(x,y,32.4,2.05,1.3))
    # Rounded corner stops surround the *factory wrapped* 52.5 x 35 x 10.3 cell.
    # Leave the left end open for cell leads and the separate insulated NTC probe.
    for y in (50.85,88.15):
        lid = lid.union(rounded(16,y,26.8,48,1.5,SPLIT-26.8+.05,.55))
    lid = lid.union(rounded(66.8,54.,26.8,1.5,32.,SPLIT-26.8+.05,.55))
    for y in (48.0,90.25):
        lid=lid.cut(rounded(34.,y,SPLIT-.2,12.,1.65,3.,.5))
    # Independent rear-lid anchor for the protected pack/NTC leads. It moves with the pack.
    for y in (52.,58.5):
        lid=lid.union(box(7.9,y,27.2,2.1,1.65,4.1))
    lid=lid.union(box(7.9,52.,27.2,2.1,8.15,1.55))
    # Captures the slider after the rear lid closes; the tongue stays off switch loads.
    lid = lid.union(box(75.50,SWITCH_Y-4.2,15.30,.90,8.4,SPLIT-15.30+.05).union(box(75.20,SWITCH_Y-4.2,17.0,1.20,8.4,SPLIT-17.0+.05)))
    return lid

def button_model():
    # Assembly rest: outer face at -0.65, integral flange at z=2.4.
    cap = cylinder(0,0,-.65,3.55,3.2)
    cap = cap.union(cylinder(0,0,FRONT,4.60,1.4))
    cap = cap.union(cylinder(0,0,FRONT+1.35,2.65,7.05))
    return cap.union(cylinder(0,0,10.70,1.18,1.55))

def slider_model():
    # Global X/Z and relative Y. A keyed open fork captures the MSK side lever.
    fork = box(73.72,-2.05,12.16,3.95,4.10,1.68)
    fork = fork.cut(box(73.6,-.87,12.05,1.58,1.74,1.91))
    flange = box(76.62,-2.85,10.55,.88,5.70,5.25)
    thumb = box(77.2,-2.75,SWITCH_Z-1.4,3.8,5.50,2.80)
    return fork.union(flange).union(thumb)

def component_position(shape):
    return shape.rotate((0,0,0),(1,1,0),180).translate((29.3,26.5,3.4))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--core-step',type=Path)
    args=ap.parse_args()
    tray, lid, button = tray_model(), lid_model(), button_model()
    parts = {'front_tray': (tray,2), 'rear_lid': (lid,2), 'keycap': (button,6), 'power_slider':(slider_model(),2)}
    metrics = {'units':'mm', 'housing_mm':[W,H,DEPTH], 'pcb_front_z_mm':PCB_FRONT,
               'pcb_origin_xy_mm':[BOARD_X,BOARD_Y], 'key_centres_xy_mm':KEYS,'parts':{}}
    for name,(part,quantity) in parts.items():
        solid = part.val()
        assert solid.isValid() and len(solid.Solids())==1, name
        orient = part
        if name == 'rear_lid':
            orient = part.rotate((0,0,0),(1,0,0),180)
        origin = orient.val().BoundingBox()
        orient = orient.translate((-origin.xmin,-origin.ymin,-origin.zmin))
        file=OUT/f'{name}.stl'
        cq.exporters.export(orient,str(file),tolerance=.035,angularTolerance=.12)
        mesh=trimesh.load(file,force='mesh')
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0, name
        metrics['parts'][name]=dict(quantity_for_two=quantity,
            size_mm=[round(float(v),3) for v in mesh.extents],
            volume_cm3=round(float(mesh.volume/1000),5),
            sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    # Positive material intersection; touching screw grip/seat planes are intentional.
    tests={}
    def overlap(name, a,b,max_mm3=.012):
        inter=a.val().intersect(b.val()).Volume()
        tests[name]=round(inter,6)
        if inter > max_mm3: raise ValueError(f'{name}: {inter:.5f} mm3')
    overlap('tray_lid',tray,lid)
    pcb=box(BOARD_X,BOARD_Y,PCB_FRONT,68,35,1.6)
    overlap('pcb_tray',pcb,tray)
    overlap('pcb_lid',pcb,lid)
    battery=box(13.4,52.9,SPLIT-10.3,52.5,35,10.3)
    overlap('battery_lid',battery,lid)
    overlap('battery_pcb',battery,pcb)
    overlap('battery_shell',battery,tray)
    for position,dy in [('up',-.8),('down',.8)]:
        cap=slider_model().translate((0,SWITCH_Y+dy,0))
        overlap(f'slider_{position}_tray',cap,tray)
        overlap(f'slider_{position}_lid',cap,lid)
        overlap(f'slider_{position}_pcb',cap,pcb)
    for i,(x,y) in enumerate(KEYS,1):
        overlap(f'key{i}_tray',button.translate((x,y,0)),tray)
    metrics['mechanics']={'cell_max_mm':[52.5,35,10.3], 'cell_xyz':[13.4,52.9,SPLIT-10.3],
        'cell_pcb_gap_mm':round(SPLIT-10.3-(PCB_FRONT+1.6),2),'key_tip_z_mm':12.25,
        'key_nominal_height_mm':1.5,'key_rest_gap_mm':.25,
        'small_board_mounts':SMALL_HOLES,'core_mounts':CORE_HOLES,'core_mount_seat_z':CORE_BOSS_Z,
        'usb_socket_y_mm':26.5,'barrel_axis_yz_mm':[BOARD_Y+12.5, PCB_FRONT-6.55]}
    if args.core_step:
        core=component_position(cq.importers.importStep(str(args.core_step)))
        # Supplier assembly brings several hundred detailed solids; test only overlapping AABBs.
        for name,shape in (('tray',tray),('lid',lid),('cell',battery),('pcb',pcb)):
            colliding=[]
            for idx,s in enumerate(core.val().Solids()):
                bb=s.BoundingBox()
                qb=shape.val().BoundingBox()
                if not (bb.xmax>qb.xmin and bb.xmin<qb.xmax and bb.ymax>qb.ymin and bb.ymin<qb.ymax and bb.zmax>qb.zmin and bb.zmin<qb.zmax): continue
                volume=shape.val().intersect(s).Volume()
                if volume>.012: colliding.append((idx,round(volume,4)))
            if colliding: raise ValueError(f'core/{name} collision {colliding}')
            tests[f'vendor_core_{name}']=0
        metrics['vendor_step_sha256']=hashlib.sha256(args.core_step.read_bytes()).hexdigest()
    metrics['intersection_mm3']=tests
    (HERE/'geometry-check.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':
    main()
