"""Build genuine B-rep exports, meshes, measurements and reproducible review images."""
import json,csv,math,struct,itertools,collections,sys,hashlib
from pathlib import Path
import model as m
from airpath import body_closure
from model import cq
ROOT=Path(__file__).resolve().parents[2]
def write_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
def mesh_metrics(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,80)[0];edges=collections.Counter();volume=0.;degenerate=0
    if len(raw)!=84+50*n:raise ValueError('Binary STL size mismatch')
    for i in range(n):
        vals=struct.unpack_from('<12fH',raw,84+50*i)
        tri=[tuple(vals[3+3*j:6+3*j]) for j in range(3)]
        if len(set(tri))<3:degenerate+=1
        for a,b in [(0,1),(1,2),(2,0)]:edges[tuple(sorted((tri[a],tri[b])))]+=1
        a,b,c=tri;volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return {'triangles':n,'non_manifold_edges':sum(v!=2 for v in edges.values()),'degenerate_triangles':degenerate,'signed_volume_mm3':volume}
COLORS={'A_duct':'#92adbb','B_STRIKE_mask':'#d1aa70','C_twin_louver':'#3a6878','D_common_bracket':'#a4a9ad','E_fan_gasket_installed':'#69a58a','F_mask_gasket_installed':'#69a58a','fan_38mm_ENVELOPE':'#424c57','4040_OBSTRUCTION_ENVELOPE':'#b8bec4'}
def render(p,name,exploded=False,section=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(13,9));ax=fig.add_subplot(111,projection='3d');allpoints=[]
    shifts={'A_duct':(0,0,0),'B_STRIKE_mask':(0,42,0),'C_twin_louver':(0,75,0),'D_common_bracket':(35,0,0),'E_fan_gasket_installed':(0,0,-16),'F_mask_gasket_installed':(0,20,0),'fan_38mm_ENVELOPE':(0,0,-40),'4040_OBSTRUCTION_ENVELOPE':(50,0,0)}
    for n,s in p.items():
        if n.startswith('washer'):continue
        if section and n in ['A_duct','B_STRIKE_mask']:s=s.cut(m.box(200,500,500,(100,0,0)))
        vertices,faces=s.val().tessellate(.7)
        shift=shifts.get(n,(0,0,0)) if exploded else (0,0,0)
        v=[tuple(a+b for a,b in zip(t.toTuple(),shift)) for t in vertices];allpoints+=v
        tris=[[v[j] for j in f] for f in faces]
        ax.add_collection3d(Poly3DCollection(tris,facecolors=COLORS.get(n,'#8a9098'),edgecolors='none',alpha=.22 if 'ENVELOPE' in n else 1))
        if exploded:
            center=s.val().Center().toTuple();ax.text(*(a+b for a,b in zip(center,shift)),n.split('_')[0],fontsize=10)
    for fn,k in [(ax.set_xlim,0),(ax.set_ylim,1),(ax.set_zlim,2)]:fn(min(v[k] for v in allpoints)-10,max(v[k] for v in allpoints)+10)
    ax.set_box_aspect([max(v[k] for v in allpoints)-min(v[k] for v in allpoints) for k in range(3)])
    ax.view_init(24,38);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
    ax.set_title('AERO120 R4.13-LC1 | '+name+' | CAD candidate / NOT manufacturing release')
    fig.tight_layout();fig.savefig(ROOT/'10_Previews'/f'{name}.png',dpi=150);plt.close(fig)
def bracket_flat_pattern():
    # K=.4 is a quotation assumption, not a qualified bend table.
    radius=2.;t=2.;k=.4;ba=math.pi/2*(radius+k*t)
    length=34+28+46+2*ba
    blank=cq.Workplane('XY').rect(44,length).extrude(.1)
    for y in [-15,15]:
        for dist in [10,30]:blank=blank.cut(m.cylinder(2.25,1,(y,-length/2+dist,-.3)))
    # Folded outer plate coordinates measured from second bend end.
    for y,z in [(0,40),(0,64),(-14,40),(14,40)]:
        blank=blank.cut(m.cylinder(2.75,1,(y,-length/2+34+ba+28+ba+(z-26),-.3)))
    face=blank.faces('>Z').wires().toPending()
    cq.exporters.export(face,str(ROOT/'11_Manufacturing/D_common_bracket_FLAT_K04_UNQUALIFIED.dxf'))
    return {'sheet_mm':2,'inside_radius_mm':2,'assumed_K':k,'bend_angle_deg':90,'bend_count':2,'flat_width_mm':44,'flat_length_mm':length,'bend_centers_from_start_mm':[34+ba/2,34+ba+28+ba/2],'status':'supplier must verify K, bend deduction, relief and tolerances before cutting'}
def main():
    for d in ['05_STEP','06_STL','07_Assembly','08_BOM','09_Test_Reports','10_Previews','11_Manufacturing']:(ROOT/d).mkdir(exist_ok=True)
    p=m.parts();report={'revision':m.P['revision'],'status':'GEOMETRY_CANDIDATE_NOT_RELEASED','parameters':m.P,'solids':{},'meshes':{},'collisions':{},'motion':[],'fan_envelopes':{},'installation_modes':{}}
    coupon_dir=ROOT/'11_Manufacturing/coupons';coupon_dir.mkdir(exist_ok=True)
    report['coupons']={}
    regions={'A_duct':m.box(14,36,64,(57,78,67)),'B_STRIKE_mask':m.box(14,40,70,(57,80,67)),'C_twin_louver':m.box(14,36,40,(50,84,67))}
    for n,region in regions.items():
        sample=p[n].intersect(region).clean()
        # One exported coupon per connected component, never pretend detached pieces are one part.
        for i,solid in enumerate(sample.solids().vals()):
            name=f'{n}_fit_coupon_{i+1}';report['coupons'][name]={'valid':solid.isValid(),'volume_cm3':solid.Volume()/1000}
            cq.exporters.export(cq.Workplane(obj=solid),str(coupon_dir/f'{name}.step'))
            solid.exportStl(str(coupon_dir/f'{name}.stl'),tolerance=.06,angularTolerance=.1,ascii=False)
    for n,s in p.items():
        bb=s.val().BoundingBox();report['solids'][n]={'valid':s.val().isValid(),'solid_count':len(s.solids().vals()),'volume_cm3':s.val().Volume()/1000,'bbox_mm':[bb.xlen,bb.ylen,bb.zlen]}
        for side in ['R','L']:
            q=s if side=='R' else s.mirror('YZ');name=f'{side}_{n}'
            cq.exporters.export(q,str(ROOT/'05_STEP'/f'{name}.step'))
            stl=ROOT/'06_STL'/f'{name}.stl';q.val().exportStl(str(stl),tolerance=.06,angularTolerance=.1,ascii=False)
            report['meshes'][name]=mesh_metrics(stl)
    for a,b in itertools.combinations(p,2):report['collisions'][a+' / '+b]=m.volume_overlap(p[a],p[b])
    for i in range(-24,25):
        a=i/2;core=m.build_core(angle=a)
        report['motion'].append({'angle_deg':a,'overlap_mm3':{n:m.volume_overlap(core,p[n]) for n in ['A_duct','B_STRIKE_mask','D_common_bracket']}})
    report['overtravel_stops']={str(a):m.volume_overlap(m.build_core(angle=a),p['B_STRIKE_mask']) for a in [-13,-12.1,12.1,13]}
    for depth in m.P['fan_depth_checks']:
        f=m.fan(depth);cable=m.box(25,15,12,(72.5,40,-1-depth/2))
        report['fan_envelopes'][str(depth)]={'fan_overlaps_mm3':{n:m.volume_overlap(f,s) for n,s in p.items()},'example_side_cable_overlaps_mm3':{n:m.volume_overlap(cable,s) for n,s in p.items()}}
    # Actual screwdriver shaft/head envelope below front mask. No imaginary access paths.
    report['mask_screw_tool_access']={}
    for x in [-40,40]:
        tool=m.cylinder(3.2,42,(x,88+m.P['front_shift_y'],31),'Y')
        report['mask_screw_tool_access'][str(x)]={n:m.volume_overlap(tool,s) for n,s in p.items()}
    for mode in ['upright','crossbar']:
        env=m.profile4040(mode);obstructions={n:m.volume_overlap(s,env) for n,s in p.items()}
        report['installation_modes'][mode]={'4040_obstruction_overlaps_mm3':obstructions,'note':'solid 4040 obstruction only; T-slot profile, T nuts, corner gussets and cockpit dimensions require real hardware review'}
        assemblyparts=dict(p);assemblyparts['fan_38mm_ENVELOPE']=m.fan(38);assemblyparts['4040_OBSTRUCTION_ENVELOPE']=env
        for side in ['R','L']:
            for explode in [False,True]:
                ass=cq.Assembly(name=f'{side}_{mode}')
                shiftmap={'B_STRIKE_mask':(0,42,0),'C_twin_louver':(0,75,0),'D_common_bracket':(35,0,0),'E_fan_gasket_installed':(0,0,-16),'F_mask_gasket_installed':(0,20,0),'fan_38mm_ENVELOPE':(0,0,-40),'4040_OBSTRUCTION_ENVELOPE':(50,0,0)}
                for n,s in assemblyparts.items():
                    q=s if side=='R' else s.mirror('YZ');shift=shiftmap.get(n,(0,0,0)) if explode else (0,0,0)
                    if side=='L':shift=(-shift[0],shift[1],shift[2])
                    ass.add(q,name=n,loc=cq.Location(cq.Vector(*shift)))
                label='exploded' if explode else 'assembly';ass.export(str(ROOT/'07_Assembly'/f'{side}_{mode}_{label}.step'))
        render(assemblyparts,f'{mode}_assembly');render(assemblyparts,f'{mode}_exploded',exploded=True)
    render({n:p[n] for n in ['A_duct','B_STRIKE_mask','C_twin_louver','D_common_bracket']},'airpath_section',section=True)
    report['flat_pattern']=bracket_flat_pattern()
    total=sum(report['solids'][n]['volume_cm3'] for n in ['A_duct','B_STRIKE_mask','C_twin_louver'])
    old={'duct':234.1640935868359,'mask':29.796424796047395,'two_blades':13.682094698223846}
    report['cost_geometry']={'new_printed_parts_cm3':total,'old_rejected_reconstruction_printed_parts_cm3':sum(old.values()),'reduction_vs_rejected_percent':100*(1-total/sum(old.values())),'R412_documented_duct_only_cm3':296.5,'new_duct_only_cm3':report['solids']['A_duct']['volume_cm3'],'duct_reduction_vs_documented_R412_percent':100*(1-report['solids']['A_duct']['volume_cm3']/296.5),'warning':'R412 comparison from design brief only, original CAD missing. Volume is not price. No slicing or quote.'}
    with (ROOT/'08_BOM/材料量比较.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['item','rejected_local_reconstruction_cm3','LC1_cm3','basis'])
        for n,oldkey in [('A_duct','duct'),('B_STRIKE_mask','mask'),('C_twin_louver','two_blades')]:writer.writerow([n,old[oldkey],report['solids'][n]['volume_cm3'],'CAD solid volume, not quote'])
        writer.writerow(['printed_total',sum(old.values()),total,'excludes gaskets, metal, hardware, supports and waste'])
    # Air-side clearance probe verifies blind mounting pilots have not pierced the wall.
    report['blind_boss_remaining_nominal_air_wall_mm']=58.8-55.2
    report['capped_body_air_closure']=body_closure(p['A_duct'])
    report['source_sha256']={n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ['model.py','parameters.json','build.py','airpath.py']}
    write_json(ROOT/'09_Test_Reports/geometry.json',report)
    write_json(ROOT/'11_Manufacturing/bracket_bend_assumptions.json',report['flat_pattern'])
    print(json.dumps(report['cost_geometry'],ensure_ascii=False,indent=2));print('Built',ROOT)
if __name__=='__main__':main()
