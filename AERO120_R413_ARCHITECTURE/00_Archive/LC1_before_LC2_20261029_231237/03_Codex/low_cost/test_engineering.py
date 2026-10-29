import unittest,json,hashlib
from pathlib import Path
import model as m
ROOT=Path(__file__).resolve().parents[2]
class EngineeringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads((ROOT/'09_Test_Reports/geometry.json').read_text(encoding='utf8'))
    def test_report_matches_current_sources(self):
        for n,digest in self.r['source_sha256'].items():self.assertEqual(hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest(),digest)
    def test_valid_single_solids(self):
        for n,r in self.r['solids'].items():
            with self.subTest(part=n):self.assertTrue(r['valid']);self.assertEqual(r['solid_count'],1);self.assertGreater(r['volume_cm3'],0)
    def test_both_hand_mesh_topology_and_volume(self):
        for n,r in self.r['meshes'].items():
            with self.subTest(mesh=n):
                self.assertEqual(r['non_manifold_edges'],0);self.assertEqual(r['degenerate_triangles'],0)
                cad=self.r['solids'][n[2:]]['volume_cm3']*1000
                self.assertGreater(r['signed_volume_mm3'],0);self.assertLess(abs(r['signed_volume_mm3']/cad-1),.015)
    def test_all_nominal_part_pairs(self):
        for pair,v in self.r['collisions'].items():
            with self.subTest(pair=pair):self.assertLess(v,1e-4)
    def test_half_degree_motion_samples(self):
        self.assertEqual(len(self.r['motion']),49)
        for s in self.r['motion']:
            for part,v in s['overlap_mm3'].items():
                with self.subTest(angle=s['angle_deg'],part=part):self.assertLess(v,1e-4)
    def test_overtravel_hits_physical_stops(self):
        for a,v in self.r['overtravel_stops'].items():
            with self.subTest(angle=a):self.assertGreater(v,.00001)
    def test_four_fan_depths_and_example_cable(self):
        self.assertEqual(set(self.r['fan_envelopes']),{'25','38','50','55'})
        for t,r in self.r['fan_envelopes'].items():
            for kind,pairs in r.items():
                for part,v in pairs.items():
                    with self.subTest(depth=t,kind=kind,part=part):self.assertLess(v,1e-4)
    def test_both_4040_obstruction_envelopes(self):
        for mode,r in self.r['installation_modes'].items():
            for part,v in r['4040_obstruction_overlaps_mm3'].items():
                with self.subTest(mode=mode,part=part):self.assertLess(v,1e-4)
    def test_hidden_mask_screw_tool_access(self):
        for x,pairs in self.r['mask_screw_tool_access'].items():
            for n,v in pairs.items():
                with self.subTest(x=x,part=n):self.assertLess(v,1e-4)
    def test_volume_budget(self):self.assertLessEqual(self.r['cost_geometry']['new_printed_parts_cm3'],m.P['polymer_volume_budget_cm3'])
    def test_capped_body_has_enclosed_air_cavity(self):
        r=self.r['capped_body_air_closure'];self.assertTrue(r['valid']);self.assertEqual(r['solid_count'],1);self.assertEqual(r['shell_count'],2);self.assertTrue(r['sealed_air_seed_still_void'])
    def test_fixed_interface_hole_centers(self):
        self.assertEqual(m.P['flange_size'],124);self.assertEqual(m.P['flange_thickness'],5);self.assertEqual(m.P['fan_pitch'],105)
        duct=m.build_duct()
        for x in [-52.5,52.5]:
            for y in [-52.5,52.5]:self.assertFalse(duct.val().isInside(m.cq.Vector(x,y,4),1e-6))
    def test_blind_boss_does_not_open_airwall(self):
        duct=m.build_duct()
        for y in [-15,15]:
            for z in [30,50]:
                self.assertTrue(duct.val().isInside(m.cq.Vector(56,y,z),1e-6))
                self.assertFalse(duct.val().isInside(m.cq.Vector(61,y,z),1e-6))
    def test_seal_face_land_volume(self):
        duct=m.build_duct();mask=m.build_mask()
        # Positive material probes immediately before/after gasket, four sides and corners.
        for x,z in [(-56,67),(56,67),(0,39),(0,95),(-52,39),(52,95)]:
            self.assertTrue(duct.val().isInside(m.cq.Vector(x,83.9+m.P['front_shift_y'],z),1e-5))
            self.assertTrue(mask.val().isInside(m.cq.Vector(x,85.2+m.P['front_shift_y'],z),1e-5))
        self.assertTrue(mask.val().isInside(m.cq.Vector(56,85.2+m.P['front_shift_y'],67),1e-5))
if __name__=='__main__':unittest.main(verbosity=2)
