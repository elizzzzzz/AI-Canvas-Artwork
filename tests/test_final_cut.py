import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FinalCutTests(unittest.TestCase):
 def test_continuity_doc_and_preview_exist(self):
  self.assertTrue((ROOT/'docs/FINAL-CUT-CONTINUITY.md').is_file())
  self.assertTrue((ROOT/'production/final-cut-v1/qiniu-langya-continuity-preview-v1.mp4').is_file())
 def test_three_chapters_are_named(self):
  text=(ROOT/'docs/FINAL-CUT-CONTINUITY.md').read_text()
  for s in ('第一集《梅岭旧令》','第二集《麒麟锦囊》','第三集《入京》','燕字残角','封泥/云令匣'):
   self.assertIn(s,text)
if __name__=='__main__': unittest.main()
