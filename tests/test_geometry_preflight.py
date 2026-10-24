"""Evidence gate tests, not a physics solver or proof about generated pixels."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
try:
    from tools.geometry_preflight import assess_entry
except ModuleNotFoundError:
    assess_entry = None


class GeometryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(assess_entry, '3D production evidence preflight is not implemented')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = {}
        for key in ('model', 'scene', 'camera', 'preview', 'depth', 'object_ids'):
            p = self.root / (key + '.data')
            p.write_bytes(('synthetic-test-only-' + key).encode())
            self.paths[key] = {'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        from tools.geometry_preflight import BASE_CHECKS, VIDEO_CHECKS
        checks = {k: True for k in (*BASE_CHECKS, *VIDEO_CHECKS)}
        report = {'scope': 'CLIP-01', 'revision': 'r1', 'source_sha256': 'a' * 64,
                  'files': copy.deepcopy(self.paths), 'checks': checks,
                  'sample_fps': 24, 'sample_count': 49,
                  'samples': [{'frame': n, 'time_seconds': n / 24, 'checks': checks.copy()} for n in range(49)]}
        p = self.root / 'report.json'
        p.write_text(json.dumps(report))
        self.entry = {'key': 'CLIP-01', 'kind': 'clip', 'duration': 2, 'target_fps': 24,
                      'revision': 'r1', 'status': 'approved', 'source_sha256': 'a' * 64,
                      'evidence': copy.deepcopy(self.paths),
                      'report': {'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()},
                      'approval': {'reviewer': 'test-fixture', 'approved_at': '2026-10-24',
                                   'revision': 'r1', 'source_sha256': 'a' * 64}}

        from tools.geometry_preflight import artifact_set_hash
        self.entry['approval']['artifact_set_sha256'] = artifact_set_hash(self.entry)

    def rewrite_report(self, change):
        p = self.root / 'report.json'
        doc = json.loads(p.read_text())
        change(doc)
        p.write_text(json.dumps(doc))
        self.entry['report']['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()

    def test_complete_evidence_can_pass(self):
        self.assertEqual(assess_entry(self.entry, self.root, 'a' * 64), [])

    def test_no_review_cannot_pass(self):
        self.entry['status'] = 'pending_modeling'
        self.entry['approval'] = None
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_stale_source_cannot_pass(self):
        self.assertTrue(assess_entry(self.entry, self.root, 'b' * 64))

    def test_mutated_model_cannot_pass(self):
        (self.root / 'model.data').write_bytes(b'changed scale')
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_approval_must_bind_the_exact_artifact_set(self):
        self.entry['approval']['artifact_set_sha256'] = '0' * 64
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_missing_orientation_or_occlusion_check_cannot_pass(self):
        self.rewrite_report(lambda d: d['checks'].pop('critical_visibility'))
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_missing_frame_cannot_pass(self):
        self.rewrite_report(lambda d: d['samples'].pop(21))
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_one_frame_contact_failure_blocks_whole_clip(self):
        self.rewrite_report(lambda d: d['samples'][17]['checks'].update(contact_support=False))
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))

    def test_outside_repository_evidence_rejected(self):
        self.entry['evidence']['model']['path'] = '../external.obj'
        self.assertTrue(assess_entry(self.entry, self.root, 'a' * 64))


if __name__ == '__main__':
    unittest.main()
