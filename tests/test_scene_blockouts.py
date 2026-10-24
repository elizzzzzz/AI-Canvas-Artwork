"""Structural checks for scene drafts; these are not human geometry approval."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tools.asset_library import scene, node, scene_triangles
from tools.scene_blockouts import build_stages, load_glb_asset, camera_clipped_scene, clip_near_polygon

ROOT=Path(__file__).resolve().parents[1]


class SceneBlockoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stages=build_stages()

    def test_actual_imported_glb_bounds_match_catalog_in_author_frame(self):
        catalog=json.loads((ROOT/'production/asset-library/catalog-v1.json').read_text())
        for a in catalog['assets']:
            with self.subTest(asset=a['id']):
                triangles,_,_=scene_triangles(load_glb_asset(a))
                self.assertTrue(np.allclose([triangles.min(axis=(0,1)),triangles.max(axis=(0,1))],a['bounds_m'],atol=2e-6))

    def test_all_seven_stages_use_unique_instances_and_real_assets(self):
        self.assertEqual({s.key for s in self.stages},{'SC0'+str(i) for i in range(1,8)})
        for s in self.stages:
            self.assertEqual(len(s.instances),len({i['instance_id'] for i in s.instances}))
            self.assertTrue(all(i['asset_id'] in s.sources for i in s.instances))
            tri,_,_=scene_triangles(s.model)
            self.assertTrue(np.isfinite(tri).all())
            self.assertFalse(s.model['extras']['approved_for_generation'])

    def test_pov_owner_body_is_absent_from_every_narrative_camera(self):
        owners={'梅长苏':'CH-MCS','林殊':'CH-LS','谢听云':'CH-XTY'}
        for s in self.stages:
            self.assertEqual(s.camera['mode'],'first_person')
            self.assertNotIn(owners[s.camera['pov_owner']],{i['asset_id'] for i in s.instances})
            self.assertEqual(s.camera['path_status'],'not_animated_no_clip_motion_approval')

    def test_gate_opening_is_not_filled_with_a_solid_wall(self):
        s=next(s for s in self.stages if s.key=='SC07')
        walls=[i for i in s.instances if i['asset_id']=='AR-GATEWALL']
        self.assertTrue(all(abs(i['position_m'][0])>=8 for i in walls))
        doors=[i for i in s.instances if i['asset_id']=='AR-GATELEAF']
        self.assertEqual(len(doors),2)
        self.assertTrue(all(i['rotation_degrees'][2]==90 for i in doors))

    def test_cart_wheel_and_axle_datums_are_equal(self):
        for s in self.stages:
            if not s.supports:continue
            wheel=next(i for i in s.instances if i['instance_id']=='wheel_left')
            axle=next(i for i in s.instances if i['instance_id']=='axle_01')
            self.assertAlmostEqual(wheel['position_m'][2]+.515,axle['position_m'][2]+.05)
            self.assertAlmostEqual(wheel['position_m'][2],0)

    def test_near_plane_crossing_triangle_is_clipped_not_dropped(self):
        points=[np.array([-1,-1,0.]),np.array([1,1,0.]),np.array([-1,1,0.])]
        polygon=clip_near_polygon(points,np.array([0,0,0.]),np.array([0,1,0.]),.1)
        self.assertEqual(len(polygon),4)
        self.assertTrue(all(p[1]>=.1-1e-9 for p in polygon))

    def test_clipping_preserves_instance_labels_and_finite_geometry(self):
        s=self.stages[0];camera=s.camera
        result=camera_clipped_scene(s.model,camera['eye'],camera['target'])
        self.assertEqual(len(result['nodes']),len(s.model['nodes']))
        self.assertEqual([n['extras'] for n in result['nodes']],[n['extras'] for n in s.model['nodes']])
        triangles,_,_=scene_triangles(result)
        self.assertTrue(np.isfinite(triangles).all())
        eye=np.array(camera['eye']);f=np.array(camera['target'])-eye;f/=np.linalg.norm(f)
        self.assertTrue((((triangles-eye)@f)>=.06-1e-8).all())




class SceneDraftGateTests(unittest.TestCase):
    def test_actual_scene_manifest_and_sources_match(self):
        from tools.geometry_preflight import load_scene_blockouts
        blueprint=json.loads((ROOT/'production/workflow-v1.json').read_text())
        manifest=load_scene_blockouts(blueprint,ROOT)
        self.assertEqual(manifest['scene_count'],7)
        self.assertTrue(all(item['approval'] is None for item in manifest['scenes']))

    def test_scene_dependency_change_invalidates_previous_source_hash(self):
        import copy
        from tools.geometry_preflight import source_hash
        blueprint=json.loads((ROOT/'production/workflow-v1.json').read_text())
        before=source_hash(blueprint['shots'][0],blueprint)
        changed=copy.deepcopy(blueprint)
        changed['scene_blockouts']['manifest']['sha256']='0'*64
        self.assertNotEqual(before,source_hash(changed['shots'][0],changed))

    def test_changed_scene_model_is_blocked_with_unchanged_manifest(self):
        import hashlib
        from tools.geometry_preflight import load_scene_blockouts,EVIDENCE_KEYS
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'mesh.data').write_bytes(b'synthetic-test-only-scene')
            artifact={'path':'mesh.data','sha256':hashlib.sha256((root/'mesh.data').read_bytes()).hexdigest()}
            manifest={'scenes':[{'scene_key':'SC0'+str(i),'files':{k:artifact for k in EVIDENCE_KEYS},'source_assets':{}} for i in range(1,8)]}
            (root/'manifest.json').write_text(json.dumps(manifest))
            blueprint={'scene_blockouts':{'manifest':{'path':'manifest.json','sha256':hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()}}}
            self.assertEqual(len(load_scene_blockouts(blueprint,root)['scenes']),7)
            (root/'mesh.data').write_bytes(b'changed-test-only-scene')
            with self.assertRaisesRegex(ValueError,'file changed'):
                load_scene_blockouts(blueprint,root)


if __name__=='__main__':unittest.main()
