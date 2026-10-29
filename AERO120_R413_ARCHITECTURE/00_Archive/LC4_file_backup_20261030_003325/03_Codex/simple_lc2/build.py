"""Three printed structural parts; ordinary fasteners and foam are purchased."""
import argparse,json,csv,itertools,hashlib,struct,collections,math
from pathlib import Path
import model as m
from model import cq
ROOT=Path(__file__).resolve().parents[2]
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
def mesh_metrics(path):
    b=path.read_bytes();n=struct.unpack_from('<I',b,80)[0];edges=collections.Counter();volume=0;degenerate=0
    if len(b)!=84+50*n:raise ValueError('Bad binary STL')
    for i in range(n):
        a=struct.unpack_from('<12fH',b,84+50*i);tri=[tuple(a[3+3*j:6+3*j]) for j in range(3)]
        degenerate+=len(set(tri))<3
        for j,k in [(0,1),(1,2),(2,0)]:edges[tuple(sorted((tri[j],tri[k])))]+=1
        x,y,z=tri;volume+=(x[0]*(y[1]*z[2]-y[2]*z[1])-x[1]*(y[0]*z[2]-y[2]*z[0])+x[2]*(y[0]*z[1]-y[1]*z[0]))/6
    return {'triangles':n,'bad_edges':sum(c!=2 for c in edges.values()),'degenerate_triangles':degenerate,'signed_volume_mm3':volume}
def render(parts,label,exploded=False,section=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.patches import Patch
    colors=['#91aebc','#365e6c','#b2b6ba','#474e58','#7caa8d','#7caa8d','#7caa8d','#c3a465','#c8cccf']
    fig=plt.figure(figsize=(12,9));ax=fig.add_subplot(111,projection='3d');allpoints=[]
    shifts={'B_twin_louver':(0,45,0),'C_printed_base_mount':(22,0,-35),'fan_ENVELOPE':(0,-65,-10),'fan_face_foam_REFERENCE':(0,0,-20),'base_foam_REFERENCE':(0,0,-25),'cap_seal_REFERENCE':(0,0,-30),'stock_clamp_ENVELOPE':(0,0,10),'4040_OBSTRUCTION':(30,0,0)}
    for i,(n,q) in enumerate(parts.items()):
        if n.startswith('metal_standoff'):continue
        if section and n in ['A_integrated_shell','B_twin_louver','fan_ENVELOPE','fan_face_foam_REFERENCE','base_foam_REFERENCE','cap_seal_REFERENCE']:q=q.cut(m.box(250,500,500,(125,0,0)))
        vs,fs=q.val().tessellate(.7);delta=shifts.get(n,(0,0,0)) if exploded else (0,0,0)
        v=[tuple(a+b for a,b in zip(p.toTuple(),delta)) for p in vs];allpoints+=v
        alpha=.2 if n=='4040_OBSTRUCTION' else (.4 if n=='fan_ENVELOPE' and not section else 1)
        ax.add_collection3d(Poly3DCollection([[v[j] for j in f] for f in fs],facecolor=colors[i%len(colors)],edgecolor='none',alpha=alpha))
        if exploded:
            c=q.val().Center().toTuple();ax.text(*(a+b for a,b in zip(c,delta)),n.split('_')[0],fontsize=8)
    for fn,k in [(ax.set_xlim,0),(ax.set_ylim,1),(ax.set_zlim,2)]:fn(min(v[k] for v in allpoints)-10,max(v[k] for v in allpoints)+10)
    ax.set_box_aspect([max(v[k] for v in allpoints)-min(v[k] for v in allpoints) for k in range(3)])
    ax.view_init(24,68);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
    ax.set_title('AERO120 LC4 | '+label+' | 38-40mm fan / prototype, not manufacturing release')
    ax.legend(handles=[Patch(color=colors[0],label='A: one-piece shell'),Patch(color=colors[1],label='B: moving twin louver'),Patch(color=colors[2],label='C: printed retainer + mount')],loc='upper left',fontsize=9)
    fig.tight_layout();fig.savefig(ROOT/'10_Previews'/f'{label}.png',dpi=140);plt.close(fig)
def flat_pattern():
    return {'process':'printed polymer; no sheet metal or bend DXF','base_mm':4,'mount_wall_mm':6,'ribs_mm':3}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--hand',choices=['R','L'],default='R');args=parser.parse_args()
    for d in ['05_STEP','06_STL','07_Assembly','08_BOM','09_Test_Reports','10_Previews','11_Manufacturing']:(ROOT/d).mkdir(exist_ok=True)
    p=m.parts();r={'revision':'LC2','parameters':m.P,'hand_for_print':args.hand,'solids':{},'stl':{},'collisions':{},'motion':[],'fan_fit':{},'installation':{},'hardware_limit':'all threads, worm clamp, fan and 4040 are reference envelopes; no fastener certification'}
    for n,s in p.items():
        r['solids'][n]={'valid':s.val().isValid(),'count':len(s.solids().vals()),'cm3':s.val().Volume()/1000}
        for hand in ['R','L']:
            q=s if hand=='R' else s.mirror('YZ');cq.exporters.export(q,str(ROOT/'05_STEP'/f'{hand}_{n}.step'))
    for i,n in enumerate(['A_integrated_shell','B_twin_louver','C_printed_base_mount'],1):
        q=p[n] if args.hand=='R' else p[n].mirror('YZ');path=ROOT/'06_STL'/f'{i:02d}_{n}.stl'
        q.val().exportStl(str(path),tolerance=.06,angularTolerance=.1,ascii=False);r['stl'][path.name]=mesh_metrics(path)
    dump(ROOT/'06_STL/PRINT_SELECTION.json',{'hand':args.hand,'fan_depth_range_mm':[38,40],'physical_print_parts_per_side':3,'warning':'THREE STL files: shell, louver and printed base/mount. Foam and screws/nuts are purchased. No metal bracket or clamp. --hand L replaces the same three filenames.'})
    for a,b in itertools.combinations(p,2):r['collisions'][a+' / '+b]=m.overlap(p[a],p[b])
    for i in range(-24,25):
        core=m.build_core(i/2);r['motion'].append({'angle':i/2,'overlap_mm3':{n:m.overlap(core,s) for n,s in p.items() if n!='B_twin_louver'}})
    r['overtravel']={str(a):m.overlap(m.build_core(a),p['A_integrated_shell']) for a in [-13,-12.1,12.1,13]}
    for depth in [38,39,40,40.5]:
        fan=m.fan(depth,width=120.4 if depth==40.5 else 120)
        r['fan_fit'][str(depth)]={'overlap_mm3':{n:m.overlap(fan,s) for n,s in p.items()},'bottom_free_mm':(2-depth)-m.P['cap_top_z'],'note':'40.5 x120.4 is a dimensional stress probe, not a certified fan size'}
    # Model-side minimum clearances, before supplier-specific printing error.
    r['clearances']={'fan_side_per_side_nominal_mm':(121.6-120)/2,'fan_side_per_side_for_120_4mm_frame_mm':(121.6-120.4)/2,'axial_chamber_mm':43,'top_foam_installed_mm':1,'base_foam_installed_for_38_40_mm':[4,2],'pivot_radial_clearance_to_M3_nominal_mm':(.8/2),'no_printed_threads_or_nut_traps':True,'printed_holes':{'shell_pivot':2,'core_pivot':2,'cable_port':1,'base_closure_pairs':4,'profile_mount':3},'metal_structural_part_count':0}
    r['airpath']=m.airpath_closure(p['A_integrated_shell'])
    r['wire_port']={'center':[0,-62.6,m.P['wire_hole_z']],'opening_mm':[14,10],'corner_radius_mm':1,'drill_probe_void':not p['A_integrated_shell'].val().isInside(cq.Vector(0,-62,m.P['wire_hole_z']),1e-6),'connector_envelope_mm':[12,16,8],'source':'https://everconn.com/Uploads/2022-03-16/6231af3b8f931.pdf','limits':'4P KF2510-family reference, not a guarantee for every vendor. Pass connector BEFORE inserting fan; 0.8mm fan-side gap is not a connector route.'}
    r['connector_passage']={str(y):m.overlap(m.box(12,16,8,(0,y,m.P['wire_hole_z'])),p['A_integrated_shell']) for y in range(-90,-49,2)}
    r['pivot_bores_through']={str(x):not p['A_integrated_shell'].val().isInside(cq.Vector(x,83,67),1e-6) for x in [-61,-59,-57,57,59,61]}
    r['revision']='LC4'
    r['cradle_insertion_path_mm3']={str(d):m.overlap(p['A_integrated_shell'].translate((0,0,d)),p['C_printed_base_mount']) for d in range(0,141,10)}
    for mode in ['upright','crossbar']:
        refs=m.reference_parts(mode=mode);r['installation'][mode]={n:{a:m.overlap(s,q) for a,q in p.items()} for n,s in refs.items()}
        assembly=dict(p);assembly.update(refs)
        for hand in ['R','L']:
            ass=cq.Assembly(name=f'LC2_{hand}_{mode}')
            for n,q in assembly.items():ass.add(q if hand=='R' else q.mirror('YZ'),name=n)
            ass.export(str(ROOT/'07_Assembly'/f'{hand}_{mode}.step'))
        render(assembly,mode+'_assembly')
        if mode=='upright':
            render(assembly,'exploded',exploded=True)
            exp=cq.Assembly(name='LC2_exploded')
            shifts={'B_twin_louver':(0,45,0),'C_printed_base_mount':(22,0,-35),'fan_ENVELOPE':(0,-65,-10),'stock_clamp_ENVELOPE':(0,0,10)}
            for n,q in assembly.items():exp.add(q,name=n,loc=cq.Location(cq.Vector(*shifts.get(n,(0,0,0)))))
            exp.export(str(ROOT/'07_Assembly/R_exploded.step'))
    render({**p,**{n:s for n,s in m.reference_parts().items() if n not in ['4040_OBSTRUCTION','stock_clamp_ENVELOPE'] and not n.startswith('metal_standoff')}},'fan_housing_section',section=True)
    r['flat']=flat_pattern()
    r['base_bolt_routes']={str((x,y)):{n:m.overlap(m.cylinder(2,20,(x,y,-45)),s) for n,s in p.items()} for x in [-68,68] for y in [-42,42]}
    r['base_screw_centers']=[[x,y] for x in [-68,68] for y in [-42,42]]
    r['volume_comparison']={'LC3_printed_cm3':150.40540449987708,'LC4_printed_cm3':sum(r['solids'][n]['cm3'] for n in ['A_integrated_shell','B_twin_louver','C_printed_base_mount']),'LC3_print_part_count':2,'LC4_print_part_count':3,'note':'Structural mount converted to polymer; includes the newly printed base. Not a quote.'}
    r['source_sha256']={n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ['model.py','build.py','parameters.json']}
    dump(ROOT/'09_Test_Reports/geometry.json',r);dump(ROOT/'11_Manufacturing/print_assumptions.json',r['flat'])
    print(json.dumps(r['volume_comparison'],indent=2));print('Airpath',r['airpath']);print('Built',ROOT)
if __name__=='__main__':main()
