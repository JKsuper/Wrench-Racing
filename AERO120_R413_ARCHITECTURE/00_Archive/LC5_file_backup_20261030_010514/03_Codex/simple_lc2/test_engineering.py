import unittest,json,hashlib
from pathlib import Path
import model as m
ROOT=Path(__file__).resolve().parents[2]
class Engineering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=json.loads((ROOT/'09_Test_Reports/geometry.json').read_text(encoding='utf8'))
    def test_source_matches_report(self):
        for n,h in self.r['source_sha256'].items():self.assertEqual(hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest(),h)
    def test_valid_single_parts(self):
        for n,s in self.r['solids'].items():
            with self.subTest(part=n):self.assertTrue(s['valid']);self.assertEqual(s['count'],1)
    def test_three_print_STLs(self):self.assertEqual(len(list((ROOT/'06_STL').glob('*.stl'))),3)
    def test_print_meshes(self):
        for n,s in self.r['stl'].items():
            with self.subTest(mesh=n):self.assertEqual(s['bad_edges'],0);self.assertEqual(s['degenerate_triangles'],0);self.assertGreater(s['signed_volume_mm3'],0)
    def test_nominal_part_collisions(self):
        for n,v in self.r['collisions'].items():
            with self.subTest(pair=n):self.assertLess(v,1e-4)
    def test_pitch_motion(self):
        self.assertEqual(len(self.r['motion']),49)
        for r in self.r['motion']:
            for n,v in r['overlap_mm3'].items():
                with self.subTest(angle=r['angle'],part=n):self.assertLess(v,1e-4)
    def test_physical_stops(self):
        for a,v in self.r['overtravel'].items():
            with self.subTest(angle=a):self.assertGreater(v,1e-5)
    def test_fan_38_to_40_and_dimensional_stress_probe(self):
        for d,r in self.r['fan_fit'].items():
            for n,v in r['overlap_mm3'].items():
                with self.subTest(depth=d,part=n):self.assertLess(v,1e-4)
            self.assertGreaterEqual(r['bottom_free_mm'],1.5)
    def test_capped_pressure_airpath(self):
        r=self.r['airpath'];self.assertTrue(r['valid']);self.assertEqual(r['solids'],1);self.assertEqual(r['shells'],2);self.assertTrue(r['air_seed_is_void'])
    def test_both_installations_and_stock_envelopes(self):
        for mode,r in self.r['installation'].items():
            for n,pairs in r.items():
                for part,v in pairs.items():
                    with self.subTest(mode=mode,reference=n,part=part):self.assertLess(v,1e-4)
    def test_tolerance_allowances(self):
        r=self.r['clearances'];self.assertGreaterEqual(r['fan_side_per_side_nominal_mm'],.79);self.assertGreaterEqual(r['fan_side_per_side_for_120_4mm_frame_mm'],.59);self.assertEqual(r['axial_chamber_mm'],43)
    def test_M4x16_stack_has_full_nut_height(self):
        r=self.r['pivot_stack'];self.assertGreaterEqual(r['nominal_projection_mm'],1);self.assertLessEqual(r['stack_to_nut_end_mm'],r['screw_underhead_mm'])
    def test_M4_pivot_hole_size(self):self.assertEqual(m.P['pivot_hole_diameter'],4.8)
    def test_large_port_keeps_upper_and_lower_wall(self):
        shell=m.build_body().val()
        self.assertEqual(self.r['wire_port']['opening_mm'],[18,14])
        for z in [-34,-14]:self.assertTrue(shell.isInside(m.cq.Vector(0,-62,z),1e-6))
    def test_four_way_mount_geometries(self):
        self.assertEqual(len(self.r['four_way_mounts']),8)
        for n,r in self.r['four_way_mounts'].items():
            for k in ['cap_shell_overlap','profile_shell_overlap','profile_cap_overlap']:
                with self.subTest(mode=n,pair=k):self.assertLess(r[k],1e-4)
    def test_M4x16_base_stack(self):self.assertGreaterEqual(self.r['base_stack']['M4x16_projection_mm'],1)
    def test_wire_port(self):self.assertTrue(self.r['wire_port']['drill_probe_void'])
    def test_four_pin_connector_passage_before_fan_installation(self):
        for y,v in self.r['connector_passage'].items():
            with self.subTest(y=y):self.assertLess(v,1e-4)
    def test_pivot_bores_are_through(self):self.assertTrue(all(self.r['pivot_bores_through'].values()))
    def test_base_vertical_assembly_path(self):
        for d,v in self.r['cradle_insertion_path_mm3'].items():
            with self.subTest(offset_y=d):self.assertLess(v,1e-4)
    def test_one_piece_printed_base_mount(self):self.assertEqual(self.r['solids']['C_printed_base_mount']['count'],1);self.assertEqual(len(self.r['base_screw_centers']),4)
    def test_four_base_bolts_align(self):
        for center,pairs in self.r['base_bolt_routes'].items():
            for part,v in pairs.items():
                with self.subTest(center=center,part=part):self.assertLess(v,1e-4)
if __name__=='__main__':unittest.main(verbosity=2)
