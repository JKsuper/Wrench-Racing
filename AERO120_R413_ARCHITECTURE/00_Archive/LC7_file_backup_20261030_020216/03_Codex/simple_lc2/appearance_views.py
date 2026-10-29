"""Native CAD render, colour illustration and old/new corner sections."""
from pathlib import Path
import model as m
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
ROOT=Path(__file__).resolve().parents[2]
def draw_cad(items,path,title,direction=(.55,.65,1),footer=''):
    # A real depth-buffered renderer is essential for nested shells and raised lettering.
    import vtk
    renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1)
    for shape,color in items:
        vertices,faces=shape.val().tessellate(.25);points=vtk.vtkPoints()
        for v in vertices:points.InsertNextPoint(*v.toTuple())
        cells=vtk.vtkCellArray()
        for f in faces:
            tri=vtk.vtkTriangle()
            for i,j in enumerate(f):tri.GetPointIds().SetId(i,j)
            cells.InsertNextCell(tri)
        poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly);normals.ConsistencyOn();normals.AutoOrientNormalsOn()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*to_rgb(color));actor.GetProperty().SetAmbient(.22);actor.GetProperty().SetDiffuse(.78);actor.GetProperty().SetSpecular(.12);actor.GetProperty().SetSpecularPower(20)
        renderer.AddActor(actor)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(1600,1300);window.SetMultiSamples(8);window.AddRenderer(renderer)
    camera=renderer.GetActiveCamera();camera.SetPosition(*(np.array(direction)*300));camera.SetFocalPoint(0,15,30);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn();renderer.ResetCamera();camera.Zoom(1.0)
    header=vtk.vtkTextActor();header.SetInput(title);header.GetTextProperty().SetFontSize(25);header.GetTextProperty().SetColor(.08,.08,.08);header.SetDisplayPosition(30,1250);renderer.AddViewProp(header)
    note=vtk.vtkTextActor();note.SetInput(footer);note.GetTextProperty().SetFontSize(16);note.GetTextProperty().SetColor(.15,.15,.15);note.SetDisplayPosition(30,25);renderer.AddViewProp(note)
    window.Render();capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff();capture.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()
def main():
    p=m.parts();logo=m.front_brand()
    # White lettering is an illustrative paint/dual-colour treatment of real relief geometry.
    cover=m.build_cosmetic(brand=False)
    items=[(p['A_integrated_shell'],'#424b54'),(p['B_twin_louver'],'#283d48'),(p['C_printed_base_mount'],'#5c6670'),(cover,'#ed772b'),(logo,'#f4f4ef')]
    draw_cad(items,ROOT/'10_Previews/Wrench_Racing_front_bezel.png','LC7 | Wrench Racing - removable outlet bezel',direction=(.32,1,.42),footer='Actual CAD geometry; orange front bezel + white lettering are a colour illustration. STL has no assigned filament colour.\nFour wide reinforced corners; mechanical strength and print tolerances remain untested.')
    draw_cad([(cover,'#ed772b'),(logo,'#f4f4ef')],ROOT/'10_Previews/front_bezel_only.png','LC7 | universal front bezel + 0.8 mm raised branding',direction=(.12,1,.12),footer='3 mm plate / front-only colour trim / two independent M4 fasteners\nOne universal part for left and right. White lettering shown as optional finishing.')
    oldpath=ROOT/'11_Manufacturing/LC5_corner_reference.step'
    if oldpath.exists():
        old=m.cq.importers.importStep(str(oldpath));clip=m.box(40,40,32,(63,63,-30))
        new=p['A_integrated_shell'].intersect(clip)
        m.cq.exporters.export(new,str(ROOT/'11_Manufacturing/LC7_corner_reference.step'))
        fig,axes=plt.subplots(1,2,figsize=(12,6))
        for ax,shape,title,edge in zip(axes,[old,new],['LC5: narrow corner ear','LC7: broad pad joined to two walls'],[74,77]):
            section=m.cq.Workplane('XY').newObject([shape.val()]).section(-36.5)
            for e in section.val().Edges():
                pts=[e.positionAt(i/40).toTuple() for i in range(41)];ax.plot([p[0] for p in pts],[p[1] for p in pts],color='#386b85',lw=2)
            ax.annotate('',xy=(edge,68),xytext=(70.4,68),arrowprops={'arrowstyle':'<->','color':'#c25525'})
            ax.text(68,65.5,f'{edge-70.4:.1f} mm outer ligament',fontsize=9,color='#a34820')
            ax.set_title(title);ax.set_aspect('equal');ax.set_xlim(47,80);ax.set_ylim(47,80);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.grid(alpha=.15)
        fig.suptitle('Actual CAD sections at Z=-36.5 mm; upper root ribs not shown',fontsize=13);fig.tight_layout();fig.savefig(ROOT/'10_Previews/corner_reinforcement_comparison.png',dpi=150);plt.close(fig)
if __name__=='__main__':main()
