"""Draw a real X=0 CAD section; flow arrows indicate direction only, not CFD."""
from pathlib import Path
import model as m
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[2]
def main():
    parts=m.parts();refs=m.reference_parts();fig,ax=plt.subplots(figsize=(12,9))
    fan=Rectangle((-60,-38),120,40,facecolor='#dbe0e5',edgecolor='#58636e',linewidth=1)
    ax.add_patch(fan)
    shapes=[(parts['A_integrated_shell'],'#597f94',1.8),(parts['B_twin_louver'],'#24525c',2),(parts['C_metal_cap_mount_NOT_PRINT'],'#70757a',2)]
    for n in ['fan_face_foam_REFERENCE','base_foam_REFERENCE','cap_seal_REFERENCE']:shapes.append((refs[n],'#609a75',2))
    for s,color,width in shapes:
        section=m.cq.Workplane('YZ').newObject([s.val()]).section()
        for edge in section.val().Edges():
            points=[edge.positionAt(i/32).toTuple() for i in range(33)]
            ax.plot([p[1] for p in points],[p[2] for p in points],color=color,linewidth=width)
    ax.annotate('120 x 120 x 40 fan envelope\n38 mm uses thicker ONE-PIECE base foam',xy=(0,-18),xytext=(-40,-27),fontsize=10)
    ax.annotate('4P connector port: 14 x 10 mm\nremovable slit soft seal',xy=(-62.6,-24),xytext=(-91,10),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('Metal cap: 110 mm open inlet\nfan guard supplied separately',xy=(59,-40),xytext=(15,-58),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('Integrated shell + STRIKE nose\nno removable nose joint / no small nut traps',xy=(5,95),xytext=(-73,112),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('One moving twin louver\n+/-12 deg nominal',xy=(83,81),xytext=(76,113),arrowprops={'arrowstyle':'->'},fontsize=10)
    for a,b in [((0,10),(0,45)),((0,45),(45,67)),((45,76),(78,79)),((45,55),(78,54))]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#4d9caa','lw':2})
    ax.text(-85,-72,'Nominal clear chamber: 43 mm | square cavity: 121.6 mm | pressure-side fan foam: 1 mm\nActual CAD section at X=0; arrows show orientation only. No strength / leakage / airflow certification.',fontsize=10)
    ax.set_aspect('equal');ax.set_xlim(-96,130);ax.set_ylim(-80,132);ax.set_xlabel('Y mm (outlet to the right)');ax.set_ylabel('Z mm');ax.grid(alpha=.15)
    ax.set_title('AERO120 LC3 - actual center section, internal 38-40 mm fan',fontsize=15)
    fig.tight_layout();fig.savefig(ROOT/'10_Previews/center_section_dimensions.png',dpi=150);plt.close(fig)
def outlet_detail():
    import numpy as np
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb
    p=m.parts();clip=m.box(180,65,90,(0,91,67));data=[]
    direction=np.array([.24,1,.25]);direction/=np.linalg.norm(direction)
    right=np.cross([0,0,1],direction);right/=np.linalg.norm(right);up=np.cross(direction,right)
    light=np.array([-.3,1,1]);light/=np.linalg.norm(light)
    for n,color in [('A_integrated_shell','#8babbf'),('B_twin_louver','#344e5d')]:
        shape=p[n].intersect(clip).val();vs,fs=shape.tessellate(.3);v=np.array([x.toTuple() for x in vs])
        for f in fs:
            tri=v[list(f)];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=max(np.linalg.norm(normal),1e-12)
            shade=.55+.45*abs(float(normal@light));rgb=np.clip(np.array(to_rgb(color))*shade,0,1)
            data.append((float((tri@direction).mean()),np.column_stack((tri@right,tri@up)),rgb))
    data.sort(key=lambda x:x[0]);fig,ax=plt.subplots(figsize=(11,7));ax.add_collection(PolyCollection([d[1] for d in data],facecolors=[d[2] for d in data],edgecolors='none',antialiased=False))
    ax.autoscale_view();ax.set_aspect('equal');ax.margins(.08);ax.axis('off');ax.set_title('AERO120 LC3 | STRIKE outlet detail - actual CAD crop',fontsize=16)
    fig.text(.5,.035,'Chevron center ridge / swept upper & lower brows / deep twin outlets\nSame two printed parts; nominal +/-12 deg louver clearance checked.',ha='center',fontsize=11)
    fig.tight_layout(rect=(0,.08,1,.98));fig.savefig(ROOT/'10_Previews/STRIKE_outlet_detail.png',dpi=160);plt.close(fig)
if __name__=='__main__':main();outlet_detail()
