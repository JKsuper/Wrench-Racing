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
    ax.annotate('Wire + rubber grommet\n7 mm candidate port',xy=(-62.6,-18),xytext=(-91,10),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('Metal cap: 110 mm open inlet\nfan guard supplied separately',xy=(59,-40),xytext=(15,-58),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('Integrated shell + STRIKE nose\nno removable nose joint / no small nut traps',xy=(5,95),xytext=(-73,112),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.annotate('One moving twin louver\n+/-12 deg nominal',xy=(83,81),xytext=(76,113),arrowprops={'arrowstyle':'->'},fontsize=10)
    for a,b in [((0,10),(0,45)),((0,45),(45,67)),((45,76),(78,79)),((45,55),(78,54))]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#4d9caa','lw':2})
    ax.text(-85,-72,'Nominal clear chamber: 43 mm | square cavity: 121.6 mm | pressure-side fan foam: 1 mm\nActual CAD section at X=0; arrows show orientation only. No strength / leakage / airflow certification.',fontsize=10)
    ax.set_aspect('equal');ax.set_xlim(-96,130);ax.set_ylim(-80,132);ax.set_xlabel('Y mm (outlet to the right)');ax.set_ylabel('Z mm');ax.grid(alpha=.15)
    ax.set_title('AERO120 LC2 - actual center section, internal 38-40 mm fan',fontsize=15)
    fig.tight_layout();fig.savefig(ROOT/'10_Previews/center_section_dimensions.png',dpi=150);plt.close(fig)
if __name__=='__main__':main()
