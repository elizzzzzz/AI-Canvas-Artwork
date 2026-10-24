"""Tests for reusable geometry, GLB export and real scene assembly invariants."""
import unittest
import tempfile
import json
import struct
from pathlib import Path
try:
    from tools.asset_library import build_catalog, build_asset, scene_triangles, write_glb, p01_assembly
except ModuleNotFoundError:
    build_catalog = None


class AssetLibraryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_catalog, 'Reusable 3D asset library is not implemented')

    def test_all_catalog_entries_have_unique_ids_and_scene_links(self):
        cat=build_catalog()
        self.assertGreaterEqual(len(cat), 90)
        self.assertEqual(len({a['id'] for a in cat}),len(cat))
        self.assertTrue(all(a['scene_keys'] and a['source_basis'] for a in cat))

    def test_every_asset_contains_finite_non_degenerate_triangles(self):
        import numpy as np
        for a in build_catalog():
            with self.subTest(asset=a['id']):
                triangles,_,_=scene_triangles(build_asset(a))
                self.assertTrue(np.isfinite(triangles).all())
                self.assertGreater(len(triangles),0)
                area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
                self.assertTrue((area>1e-10).all())

    def test_hand_has_five_separate_finger_roots(self):
        a=next(a for a in build_catalog() if a['id']=='HAND-MCS-R')
        nodes=build_asset(a)['nodes']
        self.assertEqual(sum(n['name'].startswith('finger_root_') for n in nodes),5)

    def test_horse_has_four_distinct_leg_groups(self):
        a=next(a for a in build_catalog() if a['id']=='AN-HORSE')
        self.assertEqual(sum(n['name'].startswith('leg_root_') for n in build_asset(a)['nodes']),4)

    def test_chest_hinge_retains_same_world_axis(self):
        import numpy as np
        a=next(a for a in build_catalog() if a['id']=='PR-CHEST')
        from tools.asset_library import world_transforms
        scenes=[build_asset(a,opening_angle=v) for v in (0,90,100)]
        axes=[]
        for sc in scenes:
            i=next(i for i,n in enumerate(sc['nodes']) if n['name']=='lid_hinge_root')
            axes.append(world_transforms(sc)[i][:3,3])
        self.assertTrue(all(np.allclose(axes[0],x) for x in axes))

    def test_paper_and_token_have_actual_thickness(self):
        for key in ('PR-REPORT','PR-TOKEN'):
            a=next(a for a in build_catalog() if a['id']==key)
            tri,_,_=scene_triangles(build_asset(a))
            self.assertGreater(tri[:,:,2].max()-tri[:,:,2].min(),0.0001)

    def test_glb_has_embedded_buffer_and_coordinate_conversion_root(self):
        a=next(a for a in build_catalog() if a['id']=='PR-CHEST')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'chest.glb';write_glb(build_asset(a),p)
            data=p.read_bytes();magic,version,length=struct.unpack('<4sII',data[:12])
            self.assertEqual((magic,version,length),(b'glTF',2,len(data)))
            size,kind=struct.unpack('<II',data[12:20]);self.assertEqual(kind,0x4E4F534A)
            doc=json.loads(data[20:20+size]);self.assertNotIn('uri',doc['buffers'][0])
            self.assertEqual(doc['nodes'][0]['name'],'AUTHOR_Z_UP_TO_GLTF_Y_UP')
            self.assertTrue(doc['accessors'])

    def test_table_contacts_chest_and_scene_contains_hand_and_report(self):
        sc=p01_assembly()
        ids={n.get('extras',{}).get('instance_id') for n in sc['nodes']}
        self.assertTrue({'chest_01','report_01','token_01','hand_left','hand_right','table_01'}<=ids)
        checks=sc['extras']['assembly_checks']
        self.assertAlmostEqual(checks['tabletop_z'],checks['chest_bottom_z'],places=7)
        self.assertFalse(sc['extras']['approved_for_generation'])



class LibraryProductionGateTests(unittest.TestCase):
    def test_real_catalog_and_exact_67_clip_map_pass_integrity_check(self):
        from tools.geometry_preflight import load_asset_library
        root = Path(__file__).resolve().parents[1]
        blueprint = json.loads((root / 'production/workflow-v1.json').read_text())
        catalog = load_asset_library(blueprint, root)
        self.assertEqual(len(catalog['assets']), 100)
        self.assertTrue(all(not a['production_approval'] for a in catalog['assets']))

    def test_library_scopes_are_all_present_and_remain_blocked(self):
        from tools.geometry_preflight import expected_sources, assess_entry
        root = Path(__file__).resolve().parents[1]
        blueprint = json.loads((root / 'production/workflow-v1.json').read_text())
        catalog = json.loads((root / 'production/asset-library/catalog-v1.json').read_text())
        expected = expected_sources(blueprint, catalog)
        manifest = json.loads((root / 'production/geometry/coverage-v1.json').read_text())
        entries = [e for e in manifest['entries'] if e['key'].startswith('LIB:')]
        self.assertEqual(len(entries), 100)
        for entry in entries:
            self.assertTrue(assess_entry(entry, root, expected[entry['key']]))

    def test_asset_library_reference_change_invalidates_existing_shot_source(self):
        import copy
        from tools.geometry_preflight import source_hash
        root = Path(__file__).resolve().parents[1]
        blueprint = json.loads((root / 'production/workflow-v1.json').read_text())
        before = source_hash(blueprint['shots'][0], blueprint)
        changed = copy.deepcopy(blueprint)
        changed['asset_library']['catalog']['sha256'] = '0' * 64
        self.assertNotEqual(before, source_hash(changed['shots'][0], changed))

    def test_changed_mesh_is_rejected_even_if_catalog_still_has_old_hash(self):
        import hashlib
        from tools.geometry_preflight import load_asset_library
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'mesh.glb').write_bytes(b'synthetic-test-only')
            catalog = {'asset_count': 1, 'assets': [{'id': 'TEST', 'file': 'mesh.glb',
                       'sha256': hashlib.sha256(b'synthetic-test-only').hexdigest()}]}
            (root / 'catalog.json').write_text(json.dumps(catalog))
            (root / 'mapping.json').write_text(json.dumps({'shots': []}))
            def ref(name):
                return {'path': name, 'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest()}
            blueprint = {'shots': [], 'asset_library': {'catalog': ref('catalog.json'), 'shot_map': ref('mapping.json')}}
            self.assertEqual(load_asset_library(blueprint, root)['asset_count'], 1)
            (root / 'mesh.glb').write_bytes(b'changed-test-only-geometry')
            with self.assertRaisesRegex(ValueError, 'file changed'):
                load_asset_library(blueprint, root)


if __name__ == '__main__':
    unittest.main()
