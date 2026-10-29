"""AERO120 cost restart: mm, separate manufactured parts, +Y outlet, +Z inlet.
The R4.12 source is absent. Only documented interfaces are inherited.
"""
import os,sys,math,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
if os.environ.get('AERO120_RUNTIME'): sys.path.insert(0,os.environ['AERO120_RUNTIME'])
else:
    for parent in HERE.parents:
        if (parent/'.runtime/cadquery').exists():
            sys.path.insert(0,str(parent/'.runtime'));break
import cadquery as cq
P=json.loads((HERE/'parameters.json').read_text(encoding='utf8'))
def box(a,b,c,xyz): return cq.Workplane('XY').box(a,b,c).translate(xyz)
def cylinder(r,h,xyz,axis='Z'):
    q=cq.Workplane('XY').circle(r).extrude(h)
    if axis=='X': q=q.rotate((0,0,0),(0,1,0),90)
    if axis=='Y': q=q.rotate((0,0,0),(1,0,0),-90)
    return q.translate(xyz)
def yz_prism(points,width):
    return cq.Workplane('YZ').polyline(points).close().extrude(width).translate((-width/2,0,0))
def chamfer_outline(w,h,c):
    return [(-w/2+c,-h/2),(w/2-c,-h/2),(w/2,-h/2+c),(w/2,h/2-c),(w/2-c,h/2),(-w/2+c,h/2),(-w/2,h/2-c),(-w/2,-h/2+c)]
def wire_xz(w,h,c,y,z=67):
    pl=cq.Plane(origin=(0,y,z),xDir=(1,0,0),normal=(0,-1,0))
    return cq.Workplane(pl).polyline(chamfer_outline(w,h,c)).close().val()
def loft_xz(sections): return cq.Workplane(obj=cq.Solid.makeLoft([wire_xz(*s) for s in sections]))
def hex_y(af,depth,xyz):
    return cq.Workplane('XZ').polygon(6,af/math.cos(math.pi/6)).extrude(depth).translate(xyz)
def build_duct(p=P):
    w=p['wall']
    shift=p['front_shift_y']
    profile=[(-57,5),(57,5),(76+shift,38),(76+shift,96),(0,96),(-57,40)]
    air=[(-57+w,-1),(57-w,-1),(57-w,5.5),(76+shift-w,40),(78+shift,40),(78+shift,96-w),(1,96-w),(-57+w,39)]
    duct=yz_prism(profile,114).cut(yz_prism(air,114-2*w))
    flange=box(p['flange_size'],p['flange_size'],p['flange_thickness'],(0,0,2.5)).cut(cylinder(55,7,(0,0,-1)))
    for x in [-p['fan_pitch']/2,p['fan_pitch']/2]:
        for y in [-p['fan_pitch']/2,p['fan_pitch']/2]:
            flange=flange.cut(cylinder(p['fan_hole']/2,7,(x,y,-1)))
            # Bottom-loaded M4 captive nut; fan/gasket retains nut during assembly.
            pocket=cq.Workplane('XY').polygon(6,7.2/math.cos(math.pi/6)).extrude(3.3).translate((x,y,0))
            flange=flange.cut(pocket)
    duct=duct.union(flange)
    collar=loft_xz([(114,58,5,75+shift),(114,58,5,84+shift)]).cut(loft_xz([(110,54,3,74.9+shift),(110,54,3,84.1+shift)]))
    duct=duct.union(collar)
    # Close rectangular-to-chamfered corner transitions; no exposed corner air pockets.
    shoulder=box(114,1.8,58,(0,75.1+shift,67)).cut(loft_xz([(110,54,3,74+shift),(110,54,3,76.1+shift)]))
    duct=duct.union(shoulder)
    # Keys + captive M3 nuts outside the continuous bottom air wall.
    for x in [-40,40]:
        lug=box(8,10,10,(x,79,33))
        lug=lug.cut(cylinder(1.7,12,(x,73,31),'Y'))
        lug=lug.cut(box(5.8,2.8,7,(x,78.5,30)))
        duct=duct.union(lug.translate((0,shift,0)))
    # Only local side material; blind insert pilots leave air-side wall intact.
    for y in [-15,15]:
        for z in [30,50]:
            boss=cylinder(5,6.5,(56.5,y,z),'X').cut(cylinder(2.6,4.2,(58.8,y,z),'X'))
            duct=duct.union(boss)
    # Thin external perimeter rails distribute loads; no full solid mounting slab.
    for y in [-15,15]: duct=duct.union(box(2,3,24,(58,y,40)))
    for z in [30,50]: duct=duct.union(box(2,30,3,(58,0,z)))
    return duct.clean()
def build_mask(p=P):
    w=p['mask_wall']
    sleeve=box(114.5+2*w,7,58.5+2*w,(0,81.5,67)).cut(box(114.5,9,58.5,(0,81.5,67)))
    outer=loft_xz([(118.1,62.1,7,85),(116.1,60.1,7,100)])
    # Continuous rear shoulder gives an axial sealing land against A's face.
    inner=loft_xz([(110,54,5,84.99),(112.5,56.5,5,100.01)])
    mask=sleeve.union(outer.cut(inner))
    spine=yz_prism([(100,65),(104,66),(104,68),(100,69)],104)
    # Two end bridges connect fixed spine to the outside frame.
    mask=mask.union(spine)
    for s in [-1,1]:
        mask=mask.union(box(2,5,4,(s*57.5,101.5,67)))
        mask=mask.union(box(6.5,2,4,(s*54.5,103,67)))
        mask=mask.union(cylinder(4,3,(56.5 if s==1 else -59.5,94,67),'X'))
        mask=mask.cut(cylinder(1.7,8,(s*54-4,94,67),'X'))
    # Bottom, forward-facing screws are below the visible mask, pulling the seal axially.
    for x in [-40,40]:
        mask=mask.cut(box(9,7.1,11,(x,81.45,32.5)))
        tab=box(12,2,10,(x,86,32)).cut(cylinder(1.7,4,(x,84,31),'Y'))
        web=box(2,7,9,(x+6,83.5,32.5))
        mask=mask.union(tab).union(web)
    # Tangential stop faces, ±12°.  The moving pin is round, radius 1.5 at radius 10.
    t=math.radians(p['pitch_limit_deg'])
    for s in [-1,1]:
        face=67+14*math.cos(t)+s*(13*math.sin(t)+1.5)
        mask=mask.union(box(4,15,2.5,(57,105.5,face+s*1.25)))
    return mask.translate((0,p['front_shift_y'],0)).clean()
def build_core(p=P,angle=0):
    cy,cz=p['pivot_y'],p['pivot_z']
    core=None
    for dz in [-14,14]:
        blade=box(106,p['blade_chord'],p['blade_thickness'],(0,cy,cz+dz))
        core=blade if core is None else core.union(blade)
    for s in [-1,1]:
        cheek=box(2,14,32,(s*54,cy,cz))
        hub=cylinder(4,5,(49 if s==1 else -54,cy,cz),'X')
        core=core.union(cheek).union(hub)
        core=core.cut(cylinder(1.7,12,(48 if s==1 else -60,cy,cz),'X'))
        # Nut insertion from interior, behind the central cosmetic spine.
        nut=cq.Workplane('YZ').polygon(6,5.8/math.cos(math.pi/6)).extrude(2.7).translate((49 if s==1 else -51.7,cy,cz))
        core=core.cut(nut)
    core=core.union(box(2,8,2,(54,103,81))).union(cylinder(1.5,4,(53,107,81),'X'))
    return core.rotate((0,cy,cz),(1,cy,cz),angle).translate((0,p['front_shift_y'],0)).clean()
def build_bracket(p=P):
    # Constant 2mm steel sheet, two true R2 inside bends, common blank for both modes.
    q=(cq.Workplane('XZ').moveTo(64,60).lineTo(64,26)
       .threePointArc((65.171572875,23.171572875),(68,22)).lineTo(96,22)
       .threePointArc((98.828427125,23.171572875),(100,26)).lineTo(100,72)
       .lineTo(98,72).lineTo(98,26)
       .threePointArc((97.414213562,24.585786438),(96,24)).lineTo(68,24)
       .threePointArc((66.585786438,24.585786438),(66,26)).lineTo(66,60).close().extrude(44).translate((0,22,0)))
    for y in [-15,15]:
        for z in [30,50]:q=q.cut(cylinder(2.25,5,(63,y,z),'X'))
    for y,z in [(0,40),(0,64),(-14,40),(14,40)]:q=q.cut(cylinder(2.75,6,(97,y,z),'X'))
    return q.clean()
def build_gaskets(p=P):
    fan=box(124,124,1,(0,0,-.5)).cut(cylinder(55,3,(0,0,-2)))
    for x in [-52.5,52.5]:
        for y in [-52.5,52.5]:fan=fan.cut(cylinder(2.4,3,(x,y,-2)))
    nose=loft_xz([(114,58,5,84),(114,58,5,85)]).cut(loft_xz([(110,54,3,83.9),(110,54,3,85.1)]))
    return fan,nose.translate((0,p['front_shift_y'],0))
def fan(depth):
    q=box(120,120,depth,(0,0,-1-depth/2))
    for x in [-52.5,52.5]:
        for y in [-52.5,52.5]:q=q.cut(cylinder(2.3,depth+2,(x,y,-depth-2)))
    return q
def profile4040(mode):
    # Conservative solid obstruction: no slot detail claimed as verified.
    if mode=='upright':return box(40,40,200,(120,0,60))
    return box(40,200,40,(120,0,40))
def parts(angle=0,p=P):
    g1,g2=build_gaskets(p)
    result={'A_duct':build_duct(p),'B_STRIKE_mask':build_mask(p),'C_twin_louver':build_core(p,angle),'D_common_bracket':build_bracket(p),'E_fan_gasket_installed':g1,'F_mask_gasket_installed':g2}
    for y in [-15,15]:
        for z in [30,50]:result[f'washer_{y}_{z}']=cylinder(4,1,(63,y,z),'X').cut(cylinder(2.25,2,(62.5,y,z),'X'))
    return result
def volume_overlap(a,b):return a.val().intersect(b.val()).Volume()
