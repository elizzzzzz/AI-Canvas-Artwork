import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MotionEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.w=json.loads((ROOT/'production/workflow-v1.json').read_text());self.m=json.loads((ROOT/'production/motion-evidence-v1/manifest-v1.json').read_text())
 def test_selected_three_clips_have_exact_frame_counts(self):
  self.assertEqual({x['clip_key'] for x in self.m['clips']},{'EP01-S07-01','EP02-S07-01','EP03-S05-01','EP01-S02-01','EP02-S05-01','EP03-S10-01'})
  for summary in self.m['clips']:
   entry=json.loads((ROOT/summary['manifest']['path']).read_text())
   self.assertEqual(len(entry['samples']),entry['sample_count']);self.assertEqual(entry['target_fps'],24);self.assertFalse(entry['approved_for_generation'])
 def test_each_sample_has_current_rgb_depth_and_id_hashes(self):
  for summary in self.m['clips']:
   entry=json.loads((ROOT/summary['manifest']['path']).read_text())
   for n,sample in enumerate(entry['samples']):
    self.assertEqual(sample['frame'],n);self.assertLess(abs(sample['time_seconds']-n/24),1e-5)
    for label in ('rgb','depth_mm','object_ids','object_id_map'):
     p=ROOT/sample[label]['path'];self.assertTrue(p.is_file(),p);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),sample[label]['sha256'],p)
 def test_workflow_evidence_reference_is_fresh(self):
  ref=self.w['motion_evidence']['manifest'];p=ROOT/ref['path'];self.assertEqual(ref['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
