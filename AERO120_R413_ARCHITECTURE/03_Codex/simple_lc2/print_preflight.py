"""Read exported STL/STEP independently, not just cached model report results."""
from pathlib import Path
import json,hashlib,sys,struct,math
import model as m
import vtk
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'12_Prototype_Review';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stl_signed(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,80)[0];v=0.
    for i in range(n):
        f=struct.unpack_from('<12fH',raw,84+50*i);a,b,c=[f[3+j*3:6+j*3] for j in range(3)]
        v+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return v
def main():
    hand=json.loads((ROOT/'06_STL/PRINT_SELECTION.json').read_text())['hand']
    r={'version':m.P['revision'],'selection_hand':hand,'date':'2026-10-30','scope':'exported files independently read using VTK and STEP B-rep','files':{},'release':'ENGINEERING_PROTOTYPE_CANDIDATE_NOT_PRODUCTION','pending':['shop slicer orientation/support removal preview','real fan/connector and friction gasket fit','long-term load/creep/vibration','rear mount wiring and cockpit constraints','actual price and print time']}
    all_pass=True
    for path in sorted((ROOT/'06_STL').glob('*.stl')):
        name=path.stem[3:];step=ROOT/'05_STEP'/f'{hand}_{name}.step'
        s=m.cq.importers.importStep(str(step));shape=s.val();bb=shape.BoundingBox()
        read=vtk.vtkSTLReader();read.SetFileName(str(path));read.MergingOn();read.Update();poly=read.GetOutput()
        conn=vtk.vtkPolyDataConnectivityFilter();conn.SetInputData(poly);conn.SetExtractionModeToAllRegions();conn.Update()
        edges=vtk.vtkFeatureEdges();edges.SetInputData(poly);edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
        mass=vtk.vtkMassProperties();mass.SetInputData(poly);mass.Update()
        b=poly.GetBounds();size=[b[1]-b[0],b[3]-b[2],b[5]-b[4]];cadsize=[bb.xlen,bb.ylen,bb.zlen]
        relative=abs(mass.GetVolume()/shape.Volume()-1)
        entry={'STL':str(path.relative_to(ROOT)),'STEP':str(step.relative_to(ROOT)),'STL_sha256':sha(path),'STEP_sha256':sha(step),'bbox_mm':size,'CAD_cm3':shape.Volume()/1000,'PETG_net_g_at_1_27':shape.Volume()/1000*1.27,'step_valid':shape.isValid(),'step_solid_count':len(s.solids().vals()),'vtk_connected_regions':conn.GetNumberOfExtractedRegions(),'vtk_boundary_or_nonmanifold_edges':edges.GetOutput().GetNumberOfCells(),'STL_signed_volume_positive':stl_signed(path)>0,'mesh_cad_relative_volume_difference':relative,'bbox_difference_mm':[abs(x-y) for x,y in zip(size,cadsize)]}
        entry['pass']=entry['step_valid'] and entry['step_solid_count']==1 and entry['vtk_connected_regions']==1 and entry['vtk_boundary_or_nonmanifold_edges']==0 and entry['STL_signed_volume_positive'] and relative<.015 and max(entry['bbox_difference_mm'])<.1
        all_pass &= entry['pass'];r['files'][path.name]=entry
    r['all_exported_files_pass']=bool(all_pass);r['file_count']=len(r['files']);r['total_PETG_net_g_at_1_27']=sum(v['PETG_net_g_at_1_27'] for v in r['files'].values())
    # Quantify unsupported-downward planar regions in the *current* Z-up pose; not a slicer.
    a=m.build_body();risk=[]
    for f in a.val().Faces():
        n=f.normalAt();c=f.Center();bb=f.BoundingBox()
        if n.z<-.98 and c.z>10 and f.Area()>300:risk.append({'area_mm2':f.Area(),'center_mm':c.toTuple(),'bbox_mm':[bb.xlen,bb.ylen,bb.zlen]})
    r['A_Z_up_downward_faces_needing_slicer_review']=risk
    # Realistic non-countersunk head/nut envelope for front bezel, independent of shaft-only tests.
    parts=m.parts();r['front_bezel_hardware_probe']={}
    for x in [-45,45]:
        screw=m.cylinder(2,16,(x,87,31),'Y').union(m.cylinder(4,4,(x,83,31),'Y'))
        r['front_bezel_hardware_probe'][str(x)]={n:m.overlap(screw,q) for n,q in parts.items()}
    (OUT/'01_exported_files_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    manifest={'version':m.P['revision'],'hand':hand,'units':'mm','quantity_per_file':1,'files':[{k:v[k] for k in ['STL','STL_sha256','bbox_mm']} for v in r['files'].values()],'exclude':'assemblies, envelope models, archives and coupons are not main print parts','gate':'shop slicing/support and actual hardware confirmation required before full print'}
    (OUT/'02_print_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'all_files_pass':all_pass,'files':len(r['files']),'net_PETG_g':r['total_PETG_net_g_at_1_27'],'Z_up_downward_faces':risk,'front_hardware':r['front_bezel_hardware_probe']},ensure_ascii=False,indent=2))
    if not all_pass or len(r['files'])!=4:raise SystemExit(1)
if __name__=='__main__':main()
