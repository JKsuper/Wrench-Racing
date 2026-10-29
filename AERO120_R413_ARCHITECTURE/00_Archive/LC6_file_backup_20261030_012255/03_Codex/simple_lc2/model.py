"""LC6: broad reinforced corners plus optional universal branded colour shroud."""
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
def corner_plate(height,z,air_clearance=False,p=P):
    q=box(28,28,height,(63,63,z+height/2)).edges('|Z').fillet(3)
    if air_clearance:q=q.cut(rounded_box(p['housing_inner_width'],p['housing_inner_width'],height+2,z+height/2,.6))
    return q
def corner_copies(feature):
    return [feature,feature.mirror('YZ'),feature.mirror('XZ'),feature.mirror('YZ').mirror('XZ')]
def build_body(p=P):
    w=p['wall'];outer=yz_prism([(-57,5),(57,5),(65,38),(65,96),(0,96),(-57,40)],114)
    inner=yz_prism([(-57+w,4),(57-w,4),(57-w,5.5),(65-w,40),(67,40),(67,96-w),(1,96-w),(-57+w,39)],114-2*w)
    duct=outer.cut(inner)
    # Integral front: no slip-fit, nose screws, gasket, nuts or decorative add-on shell.
    nose=loft([(114,58,1,64),(122,64,12,88)]).cut(loft([(110.4,54.4,1,63.9),(118.4,60.4,10,88.1)]))
    shoulder=box(114,1.8,58,(0,64.1,67)).cut(loft([(110.4,54.4,1,62.9),(110.4,54.4,1,65.1)]))
    body=duct.union(shoulder).union(nose)
    # Hollow-outline fighter styling: broad slash corners and a forward chevron ridge.
    ridge=[(-52,90),(-15,95),(-2,99),(2,99),(15,95),(52,90),(52,94),(15,99),(2,103),(-2,103),(-15,99),(-52,94)]
    body=body.union(cq.Workplane('XY').polyline(ridge).close().extrude(2).translate((0,0,66)))
    brow=[(-48,86),(-10,90),(0,92),(10,90),(48,86),(48,88),(10,92),(0,94),(-10,92),(-48,88)]
    for z in [35,97.4]:body=body.union(cq.Workplane('XY').polyline(brow).close().extrude(1.6).translate((0,0,z)))
    for s in [-1,1]:
        body=body.union(box(2,9,4,(s*57.5,88.5,67)))
        body=body.union(box(6.5,2,4,(s*54.5,92,67)))
        body=body.union(cylinder(6,5,(56.5 if s==1 else -61.5,83,67),'X'))
        body=body.cut(cylinder(p['pivot_hole_diameter']/2,16,(50 if s==1 else -66,83,67),'X'))
    t=math.radians(p['pitch_limit_deg'])
    for s in [-1,1]:
        face=67+14*math.cos(t)+s*(13*math.sin(t)+1.5)
        body=body.union(box(4,18,2.5,(57,93,face+s*1.25)))
    side=p['housing_inner_width']+2*p['housing_wall']
    seat=box(side,side,p['seat_thickness'],(0,0,4)).cut(cylinder(55,5,(0,0,2)))
    bottom=p['cap_top_z']+p['cap_seal_installed'];height=p['seat_bottom_z']-bottom
    housing=rounded_box(side,side,height,(bottom+3)/2,2.4).cut(rounded_box(p['housing_inner_width'],p['housing_inner_width'],height+2,(bottom+3)/2,.6))
    # Wiring port below the pressurized fan/duct interface. Grommet is purchased, not printed.
    port=box(p['wire_port_width'],12,p['wire_port_height'],(0,-62,p['wire_hole_z'])).edges('|Y').fillet(p['wire_port_corner_radius'])
    housing=housing.cut(port)
    body=body.union(seat).union(housing)
    # Wide corner bearing plates tie each screw into BOTH adjacent walls.
    pad=corner_plate(5,-39,True,p)
    ribs=box(3,16,14,(63.9,57,-27)).union(box(16,3,14,(57,63.9,-27)))
    ribs=ribs.cut(cylinder(7,20,(68,68,-35))) # nut/tool access cylinder, no nut trap
    for feature in corner_copies(pad.union(ribs)):body=body.union(feature)
    for x in [-68,68]:
        for y in [-68,68]:body=body.cut(cylinder(2.4,12,(x,y,-41)))
    # Separate low-load cosmetic mounts; entirely outside the pressure boundary.
    for s in [-1,1]:
        tab=box(17.2,12,3,(s*65.4,0,5.5))
        body=body.union(tab).cut(cylinder(2.4,8,(s*68,0,2)))
    return body.clean()
def build_core(angle=0,p=P):
    core=None
    for dz in [-14,14]:
        q=box(106,p['blade_chord'],p['blade_thickness'],(0,83,67+dz));core=q if core is None else core.union(q)
    for s in [-1,1]:
        core=core.union(box(2,14,32,(s*54,83,67))).union(cylinder(6,3,(52 if s==1 else -55,83,67),'X'))
        # Simple clearance bore; all nuts and friction washers are off-the-shelf.
        core=core.cut(cylinder(p['pivot_hole_diameter']/2,12,(48 if s==1 else -60,83,67),'X'))
    core=core.union(box(2,8,2,(54,92,81))).union(cylinder(1.5,4,(53,96,81),'X'))
    return core.rotate((0,83,67),(1,83,67),angle).clean()
def build_cradle(p=P):
    # Printed base, ribbed external mount. All nuts/washers are standard hardware.
    q=box(128,128,4,(0,0,-42)).cut(cylinder(55,6,(0,0,-45)))
    for feature in corner_copies(corner_plate(4,-44)):q=q.union(feature)
    for x in [-68,68]:
        for y in [-68,68]:q=q.cut(cylinder(2.4,7,(x,y,-45)))
    q=q.union(box(16,50,4,(70,0,-42))).union(box(6,50,34,(75,0,-23)))
    for y in [-21,21]:
        rib=(cq.Workplane('XZ').polyline([(64,-40),(72,-40),(72,-10)]).close().extrude(3).translate((0,y+1.5,0)))
        q=q.union(rib)
    for y,z in [(0,-27),(0,-13),(18,-27)]:q=q.cut(cylinder(3.25,10,(70,y,z),'X'))
    return q.clean()
def fan(depth,p=P,width=None):return box(width or p['fan_width'],width or p['fan_width'],depth,(0,0,p['fan_top_z']-depth/2))
def reference_parts(depth=40,mode='upright',p=P):
    side=p['housing_inner_width']+2*p['housing_wall']
    upper=box(120,120,1,(0,0,2.5)).cut(cylinder(55,3,(0,0,1.5)))
    bottomseal=rounded_box(side,side,1,-39.5,2.4).cut(rounded_box(p['housing_inner_width'],p['housing_inner_width'],3,-39.5,.6))
    padheight=(2-depth)-p['cap_top_z']
    # One continuous annulus of cut foam, not many shims or printed spacers.
    pad=box(120,120,padheight,(0,0,p['cap_top_z']+padheight/2)).cut(cylinder(55,padheight+2,(0,0,p['cap_top_z']-1)))
    if mode=='upright':profile=box(40,40,100,(98,0,-50))
    else:profile=box(40,200,40,(98,0,-27))
    result={'fan_ENVELOPE':fan(depth),'fan_face_foam_REFERENCE':upper,'cap_seal_REFERENCE':bottomseal,'base_foam_REFERENCE':pad,'4040_OBSTRUCTION':profile}
    cover=box(28,1,24,(0,-63.1,p['wire_hole_z'])).edges('|Y').fillet(2)
    cover=cover.cut(cylinder(2,3,(0,-65,p['wire_hole_z']),'Y')).cut(box(15,3,.6,(-7.5,-63,p['wire_hole_z'])))
    result['slit_seal_PATCH_NOT_PRINT']=cover
    # Reference stack: non-countersunk M4x16, standard nut, two 0.5mm flat washers.
    screw=cylinder(2,16,(46,83,67),'X').union(cylinder(3.5,3,(62,83,67),'X'))
    nut=cq.Workplane('YZ').polygon(6,7.2/math.cos(math.pi/6)).extrude(3.5).translate((48,83,67)).cut(cylinder(2.1,6,(47,83,67),'X'))
    outer=cylinder(4.5,.5,(61.5,83,67),'X').cut(cylinder(2.2,2,(61,83,67),'X'))
    inner=cylinder(4.5,.5,(51.5,83,67),'X').cut(cylinder(2.2,2,(51,83,67),'X'))
    friction=cylinder(5,1.5,(55,83,67),'X').cut(cylinder(2.2,3,(54.5,83,67),'X'))
    for side in ['R','L']:
        for name,shape in [('screw',screw),('nut',nut),('outer_washer',outer),('inner_washer',inner),('friction_washer',friction)]:
            result['M4_'+side+'_'+name+'_REFERENCE']=shape if side=='R' else shape.mirror('YZ')
    return result
def build_cosmetic(p=P,brand=True):
    profile=[(-57,5),(57,5),(65,38),(65,96),(0,96),(-57,40)]
    gap=p['cosmetic_clearance'];wall=p['cosmetic_wall']
    def envelope(offset,width):
        return cq.Workplane('YZ').polyline(profile).close().offset2D(offset).extrude(width).translate((-width/2,0,0))
    q=envelope(gap+wall,114+2*(gap+wall)).cut(envelope(gap,114+2*gap))
    # Open the entire front, including the lower diagonal wall, for a true upward removal path.
    q=q.cut(box(400,400,200,(0,0,-93))).cut(box(400,200,400,(0,152,0)))
    for s in [-1,1]:
        tab=box(16.4,12,3,(s*65.8,0,8.5))
        q=q.union(tab).cut(cylinder(2.4,8,(s*68,0,5)))
    if brand:
        letters=cq.Workplane('XY').text('Wrench Racing',p['brand_text_size'],p['brand_relief'],font='Arial',kind='bold',combine=False).rotate((0,0,0),(0,0,1),180).translate((0,30,96+gap+wall-.1))
        q=q.union(letters)
    return q.clean()
def parts(angle=0,p=P):return {'A_integrated_shell':build_body(p),'B_twin_louver':build_core(angle,p),'C_printed_base_mount':build_cradle(p),'D_Wrench_Racing_colour_shell':build_cosmetic(p)}
def overlap(a,b):return a.val().intersect(b.val()).Volume()
def airpath_closure(body):
    # Cap the pressure-side seat inlet and outlet. Housing/wire port is upstream of the fan seal.
    q=body.union(cylinder(56,4,(0,0,1))).union(box(126,5,68,(0,90,67)))
    for s in [-1,1]:q=q.union(cylinder(6,18,(49 if s==1 else -67,83,67),'X'))
    q=q.clean()
    return {'valid':q.val().isValid(),'solids':len(q.solids().vals()),'shells':len(q.val().Shells()),'air_seed_is_void':not q.val().isInside(cq.Vector(0,0,30),1e-6),
            'scope':'exact nominal CAD closure of pressure-side airpath with temporary inlet/outlet/pivot plugs; fan chamber is deliberately outside this closed pressure domain',
            'limits':'not a physical leakage test; actual fan gasket and moving pivots not certified'}
