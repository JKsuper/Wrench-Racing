"""LC2: two printed parts, one combined metal retainer/mount, stock clamp.
User requested internal 38-40mm fan with clearance; this supersedes LC1 external fan.
"""
import os,sys,math,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
if os.environ.get('AERO120_RUNTIME'):sys.path.insert(0,os.environ['AERO120_RUNTIME'])
else:
    for parent in HERE.parents:
        if (parent/'.runtime/cadquery').exists():sys.path.insert(0,str(parent/'.runtime'));break
import cadquery as cq
P=json.loads((HERE/'parameters.json').read_text(encoding='utf8'))
def box(a,b,c,p):return cq.Workplane('XY').box(a,b,c).translate(p)
def cylinder(r,h,p,axis='Z'):
    q=cq.Workplane('XY').circle(r).extrude(h)
    if axis=='X':q=q.rotate((0,0,0),(0,1,0),90)
    if axis=='Y':q=q.rotate((0,0,0),(1,0,0),-90)
    return q.translate(p)
def yz_prism(points,width):return cq.Workplane('YZ').polyline(points).close().extrude(width).translate((-width/2,0,0))
def outline(w,h,c):return [(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]
def wire_xz(w,h,c,y):return cq.Workplane(cq.Plane(origin=(0,y,67),xDir=(1,0,0),normal=(0,-1,0))).polyline(outline(w,h,c)).close().val()
def loft(sections):return cq.Workplane(obj=cq.Solid.makeLoft([wire_xz(*s) for s in sections]))
def rounded_box(w,h,d,z,r):return box(w,h,d,(0,0,z)).edges('|Z').fillet(r)
def build_body(p=P):
    w=p['wall'];outer=yz_prism([(-57,5),(57,5),(65,38),(65,96),(0,96),(-57,40)],114)
    inner=yz_prism([(-57+w,4),(57-w,4),(57-w,5.5),(65-w,40),(67,40),(67,96-w),(1,96-w),(-57+w,39)],114-2*w)
    duct=outer.cut(inner)
    # Integral front: no slip-fit, nose screws, gasket, nuts or decorative add-on shell.
    nose=loft([(114,58,1,64),(116.1,60.1,7,85)]).cut(loft([(110.4,54.4,1,63.9),(112.5,56.5,5,85.1)]))
    shoulder=box(114,1.8,58,(0,64.1,67)).cut(loft([(110.4,54.4,1,62.9),(110.4,54.4,1,65.1)]))
    body=duct.union(shoulder).union(nose)
    body=body.union(yz_prism([(89,65),(93,66),(93,68),(89,69)],104))
    for s in [-1,1]:
        body=body.union(box(2,9,4,(s*57.5,88.5,67)))
        body=body.union(box(6.5,2,4,(s*54.5,92,67)))
        body=body.union(cylinder(4,3,(56.5 if s==1 else -59.5,83,67),'X'))
        body=body.cut(cylinder(p['pivot_hole_diameter']/2,8,(50 if s==1 else -62,83,67),'X'))
    t=math.radians(p['pitch_limit_deg'])
    for s in [-1,1]:
        face=67+14*math.cos(t)+s*(13*math.sin(t)+1.5)
        body=body.union(box(4,18,2.5,(57,93,face+s*1.25)))
    side=p['housing_inner_width']+2*p['housing_wall']
    seat=box(side,side,p['seat_thickness'],(0,0,4)).cut(cylinder(55,5,(0,0,2)))
    bottom=p['cap_top_z']+p['cap_seal_installed'];height=p['seat_bottom_z']-bottom
    housing=rounded_box(side,side,height,(bottom+3)/2,2.4).cut(rounded_box(p['housing_inner_width'],p['housing_inner_width'],height+2,(bottom+3)/2,.6))
    # Wiring port below the pressurized fan/duct interface. Grommet is purchased, not printed.
    housing=housing.cut(cylinder(p['wire_hole_diameter']/2,12,(0,-67,p['wire_hole_z']),'Y'))
    body=body.union(seat).union(housing)
    # Broad external ledges bear on the cradle. No hole or insert in the housing.
    for s in [-1,1]:body=body.union(box(5.1,16,2,(s*64.95,10,-2)))
    return body.clean()
def build_core(angle=0,p=P):
    core=None
    for dz in [-14,14]:
        q=box(106,p['blade_chord'],p['blade_thickness'],(0,83,67+dz));core=q if core is None else core.union(q)
    for s in [-1,1]:
        core=core.union(box(2,14,32,(s*54,83,67))).union(cylinder(4,5,(49 if s==1 else -54,83,67),'X'))
        # Simple clearance bore; all nuts and friction washers are off-the-shelf.
        core=core.cut(cylinder(p['pivot_hole_diameter']/2,12,(48 if s==1 else -60,83,67),'X'))
    core=core.union(box(2,8,2,(54,92,81))).union(cylinder(1.5,4,(53,96,81),'X'))
    return core.rotate((0,83,67),(1,83,67),angle).clean()
def bend_profile(center_z,left=False,width=26,p=P):
    # One quarter annulus, constant 1.5mm sheet; positive X side before optional mirror.
    z=center_z
    q=(cq.Workplane('XZ').moveTo(64,z-3).threePointArc((66.121320344,z-2.121320344),(67,z)).lineTo(65.5,z)
       .threePointArc((65.060660172,z-1.060660172),(64,z-1.5)).close().extrude(width).translate((0,width/2,0)))
    return q.mirror('YZ') if left else q
def build_cradle(p=P):
    top=p['cap_top_z'];t=p['sheet_thickness'];bend_z=top+1.5
    q=box(128,128,t,(0,0,top-t/2)).cut(cylinder(55,t+2,(0,0,top-t-1)))
    left=box(1.5,50,-3-bend_z,(-66.25,0,(-3+bend_z)/2))
    right=box(1.5,50,45-bend_z,(66.25,0,(45+bend_z)/2))
    # Slot accepts the broad plastic support ledge, ±2mm lateral / +1mm vertical clearance.
    right=right.cut(box(4,26,3,(66.25,13,-1.5)))
    # Three generous M5 holes; choose two for upright OR crossbar, never all three.
    for y,z in [(0,18),(0,36),(18,18)]:right=right.cut(cylinder(3.25,4,(64.5,y,z),'X'))
    return q.union(bend_profile(bend_z,True,50)).union(bend_profile(bend_z,False,50)).union(left).union(right).clean()
def fan(depth,p=P,width=None):return box(width or p['fan_width'],width or p['fan_width'],depth,(0,0,p['fan_top_z']-depth/2))
def reference_parts(depth=40,mode='upright',p=P):
    side=p['housing_inner_width']+2*p['housing_wall']
    upper=box(120,120,1,(0,0,2.5)).cut(cylinder(55,3,(0,0,1.5)))
    bottomseal=rounded_box(side,side,1,-39.5,2.4).cut(rounded_box(p['housing_inner_width'],p['housing_inner_width'],3,-39.5,.6))
    padheight=(2-depth)-p['cap_top_z']
    # One continuous annulus of cut foam, not many shims or printed spacers.
    pad=box(120,120,padheight,(0,0,p['cap_top_z']+padheight/2)).cut(cylinder(55,padheight+2,(0,0,p['cap_top_z']-1)))
    band=rounded_box(135,127,9,-9,8.5).cut(rounded_box(134,126,11,-9,8))
    band=band.union(box(12,10,9,(0,68,-9)))
    if mode=='upright':profile=box(40,40,200,(93,0,45))
    else:profile=box(40,200,40,(93,0,18))
    result={'fan_ENVELOPE':fan(depth),'fan_face_foam_REFERENCE':upper,'cap_seal_REFERENCE':bottomseal,'base_foam_REFERENCE':pad,'stock_clamp_ENVELOPE':band,'4040_OBSTRUCTION':profile}
    # 6mm stand-offs give access behind the mounting tab; not printed.
    centers=[(0,18),(0,36)] if mode=='upright' else [(0,18),(18,18)]
    for i,(y,z) in enumerate(centers):result[f'metal_standoff_REFERENCE_{i+1}']=cylinder(5,6,(67,y,z),'X').cut(cylinder(2.75,8,(66,y,z),'X'))
    return result
def parts(angle=0,p=P):return {'A_integrated_shell':build_body(p),'B_twin_louver':build_core(angle,p),'C_metal_cap_mount_NOT_PRINT':build_cradle(p)}
def overlap(a,b):return a.val().intersect(b.val()).Volume()
def airpath_closure(body):
    # Cap the pressure-side seat inlet and outlet. Housing/wire port is upstream of the fan seal.
    q=body.union(cylinder(56,4,(0,0,1))).union(box(122,5,64,(0,86.5,67)))
    for s in [-1,1]:q=q.union(cylinder(4,10,(49 if s==1 else -60,83,67),'X'))
    q=q.clean()
    return {'valid':q.val().isValid(),'solids':len(q.solids().vals()),'shells':len(q.val().Shells()),'air_seed_is_void':not q.val().isInside(cq.Vector(0,0,30),1e-6),
            'scope':'exact nominal CAD closure of pressure-side airpath with temporary inlet/outlet/pivot plugs; fan chamber is deliberately outside this closed pressure domain',
            'limits':'not a physical leakage test; actual fan gasket and moving pivots not certified'}
