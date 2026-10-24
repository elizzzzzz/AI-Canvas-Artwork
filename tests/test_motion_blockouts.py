import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MotionBlockoutTests(unittest.TestCase):
 def setUp(self):
  self.w=json.loads((ROOT/'production/workflow-v1.json').read_text());self.m=json.loads((ROOT/'production/motion-blockouts/manifest-v1.json').read_text())
 def test_exact_42_action_clips_and_24fps_boundaries(self):
  expected={c['key'] for s in self.w['shots'] if s.get('action_scene') for c in s['clips']};actual={c['clip_key'] for c in self.m['clips']}
  self.assertEqual(actual,expected);self.assertEqual(len(actual),42)
  for c in self.m['clips']: self.assertEqual(c['sample_count'],c['duration_seconds']*24+1);self.assertEqual(c['camera']['mode'],'first_person');self.assertTrue(c['camera']['path_points'])
 def test_motion_evidence_files_have_current_hashes(self):
  for c in self.m['clips']:
   for a in c['evidence'].values():
    p=ROOT/a['path'];self.assertTrue(p.is_file(),a['path']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),a['sha256'],a['path'])
 def test_motion_drafts_are_not_approvals(self):
  self.assertEqual(self.m['status'],'motion_blockouts_v1_pending_24fps_review');self.assertTrue(all(not c['approved_for_generation'] for c in self.m['clips']))
 def test_workflow_motion_reference_matches_manifest(self):
  r=self.w['motion_blockouts']['manifest'];self.assertEqual(r['sha256'],hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
