import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class ActionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.workflow=json.loads((ROOT/'production/workflow-v1.json').read_text())
        self.manifest=json.loads((ROOT/'production/action-coverage-v1.json').read_text())

    def test_every_episode_exceeds_fifty_percent_action_seconds(self):
        self.assertEqual(len(self.manifest['episodes']),3)
        for ep in self.manifest['episodes']:
            self.assertGreaterEqual(ep['ratio'],0.5)
            self.assertEqual(ep['action_seconds'],sum(x['seconds'] for x in ep['action_shots']))

    def test_action_seconds_match_storyboard_durations(self):
        for ep in (1,2,3):
            shots=[s for s in self.workflow['shots'] if s['episode']==ep]
            total=sum(s['duration'] for s in shots)
            action=sum(s['duration'] for s in shots if s['action_scene'])
            row=next(x for x in self.manifest['episodes'] if x['episode']==ep)
            self.assertEqual(row['total_seconds'],total)
            self.assertEqual(row['action_seconds'],action)

    def test_action_clips_keep_first_person_safety(self):
        for shot in self.workflow['shots']:
            for clip in shot['clips']:
                if clip['action_scene']:
                    self.assertIn('ACTION_CAMERA_SAFETY:',clip['prompt'])
                    self.assertIn('第一人称',clip['prompt'])
                    self.assertGreater(clip['action_phase'],0)

    def test_action_manifest_is_referenced_by_workflow(self):
        ref=self.workflow['action_coverage']['manifest']
        path=ROOT/ref['path']
        self.assertEqual(ref['sha256'],__import__('hashlib').sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':unittest.main()
