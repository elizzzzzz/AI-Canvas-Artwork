import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DashboardTests(unittest.TestCase):
 def test_dashboard_matches_ledgers(self):
  d=json.loads((ROOT/'docs/DASHBOARD.json').read_text());cat=json.loads((ROOT/'production/asset-library/catalog-v1.json').read_text());sc=json.loads((ROOT/'production/scene-blockouts/manifest-v1.json').read_text());wf=json.loads((ROOT/'production/workflow-v1.json').read_text());me=json.loads((ROOT/'production/motion-evidence-v1/manifest-v1.json').read_text())
  self.assertEqual(d['assets']['total'],len(cat['assets']));self.assertEqual(d['scenes']['canonical'],len(sc['scenes']));self.assertEqual(d['storyboard']['logical_shots'],len(wf['shots']));self.assertEqual(d['motion_evidence']['selected_clips'],me['clip_count']);self.assertEqual(d['verification']['latest_tests_passed'],50);self.assertEqual(d['verification']['latest_tests_total'],50)
 def test_readme_contains_regenerable_dashboard_markers(self):
  text=(ROOT/'README.md').read_text();self.assertIn('<!-- PROJECT-DASHBOARD:START -->',text);self.assertIn('<!-- PROJECT-DASHBOARD:END -->',text);self.assertIn('项目数据看板',text)
if __name__=='__main__':unittest.main()
