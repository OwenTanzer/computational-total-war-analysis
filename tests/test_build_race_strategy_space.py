import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

from ctw_analysis.build_race_strategy_space import ARTIFACTS, ROOT, validate_source_lock, verify_artifacts


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = {'git_commit': 'abc', 'snapshot': {'patch': '8.1.1', 'steam_build_id': 1, 'unit_scale': 'ultra'}}
        (self.root / 'lock.json').write_text(json.dumps(self.lock))
        (self.root / 'context_catalog.json').write_text(json.dumps({'snapshot': self.lock['snapshot']}))

    def validate(self):
        return validate_source_lock(self.root, self.root / 'lock.json')

    def test_matching_commit_and_snapshot_are_required(self):
        with patch('subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'abc\n'),
                                                 subprocess.CompletedProcess([], 0, '')]):
            self.assertEqual(self.validate(), self.lock)
        with patch('subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'different\n'),
                                                 subprocess.CompletedProcess([], 0, '')]):
            with self.assertRaisesRegex(RuntimeError, 'commit mismatch'):
                self.validate()

    def test_modified_source_or_missing_git_is_rejected(self):
        with patch('subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'abc\n'),
                                                 subprocess.CompletedProcess([], 0, ' M data/source.csv')]):
            with self.assertRaisesRegex(RuntimeError, 'modified tracked'):
                self.validate()
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, 'git checkout'):
                self.validate()

    def test_wrong_snapshot_is_rejected(self):
        (self.root / 'context_catalog.json').write_text(json.dumps({'snapshot': {}}))
        with patch('subprocess.run', side_effect=[subprocess.CompletedProcess([], 0, 'abc\n'),
                                                 subprocess.CompletedProcess([], 0, '')]):
            with self.assertRaisesRegex(RuntimeError, 'snapshot mismatch'):
                self.validate()

    def test_regeneration_gate_detects_changed_and_obsolete_files(self):
        a, b = self.root / 'a', self.root / 'b'
        a.mkdir(); b.mkdir()
        for name in ARTIFACTS:
            (a / name).write_bytes(b'same'); (b / name).write_bytes(b'same')
        verify_artifacts(a, b)
        (a / 'jsd_report.json').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'Regeneration mismatch'):
            verify_artifacts(a, b)
        (a / 'obsolete.csv').write_bytes(b'extra')
        with self.assertRaisesRegex(RuntimeError, 'contract mismatch'):
            verify_artifacts(a, b)

    @unittest.skipUnless(os.environ.get('CTW_TEST_ROOT'), 'CTW_TEST_ROOT is not set')
    def test_real_locked_source_and_preserved_capabilities(self):
        import numpy as np
        import pandas as pd
        from ctw_analysis import race_features as rf
        from ctw_analysis.janus_distance import block_weighted_matrix
        source = Path(os.environ['CTW_TEST_ROOT'])
        validate_source_lock(source)
        rf.configure_source(source)
        units = rf.attach_lookup_flags(rf.load_units())
        scores, _ = rf.build_unit_scores(units)
        views, _ = rf.aggregate_features(scores)
        self.assertEqual(len(units), 972)
        _, weighted = block_weighted_matrix(views)
        # Compare to the independent pre-refactor reviewed baseline in git.
        import io
        baseline = subprocess.run(['git', 'show', 'fb17eb88c3a5f9f5707245ecfea9fa36d65518f1:studies/race_strategy_space/results/8.1.1/race_feature_triplets.csv'],
                                  cwd=ROOT, check=True, text=True, capture_output=True).stdout
        previous = pd.read_csv(io.StringIO(baseline), index_col=0).rename(columns=lambda c: c.replace('__access', '__cost_access'))
        np.testing.assert_allclose(views[weighted.columns], previous[weighted.columns], rtol=1e-10, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
