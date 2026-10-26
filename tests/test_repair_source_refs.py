"""Changed revision files must not be accepted on their old declared hash."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.geometry_preflight import load_repair_source_refs
class RepairSourceReferenceTests(unittest.TestCase):
 def test_changed_geometry_blocks_even_if_top_plan_is_unchanged(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);mesh=root/'model.glb';mesh.write_bytes(b'original')
   plan=root/'plan.json';plan.write_text(json.dumps({'model':{'path':'model.glb','sha256':hashlib.sha256(mesh.read_bytes()).hexdigest()}}))
   blueprint={'shots':[{'repair_v5':{'source_files':{'plan':{'path':'plan.json','sha256':hashlib.sha256(plan.read_bytes()).hexdigest()}}}}]}
   self.assertEqual(load_repair_source_refs(blueprint,root),2)
   mesh.write_bytes(b'changed')
   with self.assertRaises(ValueError):load_repair_source_refs(blueprint,root)
 def test_missing_revision_file_fails(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):load_repair_source_refs({'shots':[{'repair_v5':{'source_files':{'plan':{'path':'missing.json','sha256':'0'*64}}}}]},Path(d))
 def test_unmodified_legacy_workflow_has_no_new_refs(self):
  self.assertEqual(load_repair_source_refs({'shots':[{}]},Path('.')),0)
