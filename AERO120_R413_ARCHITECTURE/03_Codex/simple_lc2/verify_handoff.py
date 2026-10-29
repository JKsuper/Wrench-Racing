from pathlib import Path
import json,hashlib
import model
import vtk
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    r=ROOT/'12_Prototype_Review';packet=r/'PRINT_SHOP_RIGHT_LC8'
    manifest=json.loads((packet/'05_FILE_MANIFEST.json').read_text(encoding='utf8'))
    assert len(manifest['parts'])==4
    for entry in manifest['parts']:
        assert sha(packet/entry['file'])==entry['sha256']==sha(ROOT/'06_STL'/entry['file'])
    coupons={}
    for p in (r/'OPTIONAL_FIT_COUPONS_NOT_PRODUCT').glob('*.stl'):
        reader=vtk.vtkSTLReader();reader.SetFileName(str(p));reader.MergingOn();reader.Update()
        edges=vtk.vtkFeatureEdges();edges.SetInputData(reader.GetOutput());edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
        conn=vtk.vtkPolyDataConnectivityFilter();conn.SetInputData(reader.GetOutput());conn.SetExtractionModeToAllRegions();conn.Update()
        v={'sha256':sha(p),'regions':conn.GetNumberOfExtractedRegions(),'bad_edges':edges.GetOutput().GetNumberOfCells()}
        assert v['regions']==1 and v['bad_edges']==0
        coupons[p.name]=v
    (r/'04_handoff_and_coupon_verification.json').write_text(json.dumps({'main_files_identical_to_current_STL':True,'main_file_count':4,'optional_coupons':coupons},indent=2),encoding='utf8')
    print('PASS: 4 handoff STL hashes match current production candidates; '+str(len(coupons))+' optional coupon meshes closed and single-connected.')
if __name__=='__main__':main()
