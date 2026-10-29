"""Make a clean right-side prototype handoff; optional coupons are clearly segregated."""
from pathlib import Path
import shutil,json,hashlib,csv
import model as m
ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'12_Prototype_Review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    audit=json.loads((REVIEW/'01_exported_files_audit.json').read_text(encoding='utf8'))
    if not audit['all_exported_files_pass'] or audit['selection_hand']!='R':raise RuntimeError('Review intended for the independently audited right-side prototype')
    packet=REVIEW/'PRINT_SHOP_RIGHT_LC8';packet.mkdir(exist_ok=True)
    files=[]
    for path in sorted((ROOT/'06_STL').glob('*.stl')):
        if sha(path)!=audit['files'][path.name]['STL_sha256']:raise RuntimeError('STL changed after independent review')
        dst=packet/path.name;shutil.copy2(path,dst);files.append({'file':path.name,'quantity':1,'sha256':sha(dst),'units':'mm'})
    (packet/'05_FILE_MANIFEST.json').write_text(json.dumps({'version':m.P['revision'],'hand':'R','parts':files,'status':'FIRST_ENGINEERING_PROTOTYPE; shop slicing and material/hardware fit signoff still required'},indent=2),encoding='utf8')
    coupons=REVIEW/'OPTIONAL_FIT_COUPONS_NOT_PRODUCT';coupons.mkdir(exist_ok=True)
    p=m.parts();regions={
        'COUPON_A_axis':('A_integrated_shell',m.box(10,16,16,(59,83,67))),
        'COUPON_B_axis':('B_twin_louver',m.box(8,16,16,(52,83,67))),
        'COUPON_fan_corner':('A_integrated_shell',m.box(19,19,47,(54.5,54.5,-16.5)))}
    coupon_info=[]
    for name,(part,clip) in regions.items():
        q=p[part].intersect(clip).clean()
        for i,s in enumerate(q.solids().vals(),1):
            filename=f'{name}_{i}.stl';s.exportStl(str(coupons/filename),tolerance=.06,angularTolerance=.1,ascii=False)
            m.cq.exporters.export(m.cq.Workplane(obj=s),str(coupons/f'{name}_{i}.step'))
            coupon_info.append({'file':filename,'valid':s.isValid(),'PETG_net_g':s.Volume()/1000*1.27,'scope':'fit only; not a strength specimen or finished product'})
    (coupons/'00_READ_FIRST.md').write_text('# 可选接口试片，不是产品零件\n\n仅用于M4转轴孔/夹持和风扇角部配合，先与实物螺钉螺母及风扇试配。不要把这些试片混入四件产品的打印数量。不能用试片证明整机强度或整圈气密。各文件独立打印、自动落平台，不要按装配坐标合并。\n',encoding='utf8')
    (REVIEW/'03_optional_coupon_summary.json').write_text(json.dumps(coupon_info,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'handoff_files':len(files),'coupon_files':len(coupon_info),'coupons':coupon_info},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
