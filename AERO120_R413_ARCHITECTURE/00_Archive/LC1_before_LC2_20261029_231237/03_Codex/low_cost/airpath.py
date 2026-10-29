"""Exact B-rep closure diagnostic, not a physical leak/flow test."""
import model as m
def body_closure(duct):
    q=duct.union(m.cylinder(56,3,(0,0,-1)))
    for x in [-52.5,52.5]:
        for y in [-52.5,52.5]:q=q.union(m.cylinder(5,7,(x,y,-1)))
    end=84+m.P['front_shift_y']
    q=q.union(m.box(116,3,60,(0,end+.5,67))).clean()
    shells=q.val().Shells()
    return {'valid':q.val().isValid(),'solid_count':len(q.solids().vals()),'shell_count':len(shells),'shell_volumes_mm3':[m.cq.Solid.makeSolid(s).Volume() for s in shells],
            'sealed_air_seed_still_void':not q.val().isInside(m.cq.Vector(0,0,30),1e-6),
            'method':'A only: exact B-rep with temporary caps over inlet, outlet and four fan screw ports; expect one solid and two shells, one inner air cavity',
            'limitations':'Does not verify assembled A-B seam, moving pivot leakage, print porosity, fastener sealing or physical airtightness'}
