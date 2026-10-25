import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FinalCutTests(unittest.TestCase):
 def test_continuity_docs_and_previews_exist(self):
  for p in ['docs/FINAL-CUT-CONTINUITY.md','docs/FINAL-CUT-LOCK.md','production/final-cut-v1/qiniu-langya-continuity-preview-v1.mp4','production/final-cut-v1/EP01-previs-v1.mp4','production/final-cut-v1/EP02-previs-v1.mp4','production/final-cut-v1/EP03-previs-v1.mp4']:
   self.assertTrue((ROOT/p).is_file(),p)
 def test_three_chapters_and_shared_anchors_are_named(self):
  text=(ROOT/'docs/FINAL-CUT-CONTINUITY.md').read_text()
  for s in ('第一集《梅岭旧令》','第二集《麒麟锦囊》','第三集《入京》','燕字残角','封泥/云令匣'):
   self.assertIn(s,text)
if __name__=='__main__':unittest.main()
