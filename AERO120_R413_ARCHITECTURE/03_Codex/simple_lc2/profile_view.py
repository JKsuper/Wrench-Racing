from pathlib import Path
import model as m
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
ROOT=Path(__file__).resolve().parents[2]
q=m.build_cradle().intersect(m.box(20,70,44,(75,0,-18)))
section=m.cq.Workplane('YZ').newObject([q.val()]).section(75)
fig,ax=plt.subplots(figsize=(10,7))
for e in section.val().Edges():
    p=[e.positionAt(i/60).toTuple() for i in range(61)]
    ax.plot([v[1] for v in p],[v[2] for v in p],color='#344c60',lw=2)
for y,z in [(0,-29),(0,-9),(20,-29)]:
    ax.add_patch(Circle((y,z),9,fill=False,linestyle='--',edgecolor='#b57632',lw=1.5))
    ax.plot(y,z,'+',color='#344c60')
ax.plot([0,0],[-29,-9],color='#488c69',lw=1);ax.text(-3,-19,'20',ha='right',fontsize=11)
ax.plot([0,20],[-29,-29],color='#488c69',lw=1);ax.text(10,-32,'20',ha='center',fontsize=11)
ax.text(-31,9,'3 x diameter 7 mm through holes; choose TWO for each installation',fontsize=11)
ax.text(-31,-49,'Plate: 6 mm thick / 68 mm wide / 44 mm tall\nDashed: diameter 18 mm washer envelope (thickness 1.6 mm checked)\nM4 / M5 / M6 bolts + matching T nuts and large washers; load/creep not certified.',fontsize=10)
ax.set_aspect('equal');ax.set_xlim(-38,38);ax.set_ylim(-56,14);ax.set_xlabel('Y mm');ax.set_ylabel('Z mm');ax.grid(alpha=.15);ax.set_title('LC8 - actual CAD mounting-face section at X=75 mm')
fig.tight_layout();fig.savefig(ROOT/'10_Previews/profile_mount_M4_M5_M6.png',dpi=150);plt.close(fig)
