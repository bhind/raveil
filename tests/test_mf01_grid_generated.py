import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import mf01_grid_generated as h


class GeneratedHarnessTests(unittest.TestCase):
    def invoke(self,root,count=24):
        with patch.object(sys,'argv',['generated','--count',str(count),'--output',str(root)]):h.main()

    def test_unexpected_rejection_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h.g,'compile',side_effect=ValueError('injected compiler regression')):
                with self.assertRaisesRegex(AssertionError,'unexpected admission rejection'):self.invoke(root)
            self.assertFalse((root/'summary.json').exists())
            self.assertEqual(json.loads((root/'failure.json').read_text())['error'],'injected compiler regression')

    def test_all_rejected_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h.g,'compile',side_effect=ValueError('tile input rectangle exceeds324 words')):
                with self.assertRaisesRegex(AssertionError,'no admitted partition'):self.invoke(root)
            self.assertFalse((root/'summary.json').exists())

    def test_missing_category_cannot_report_success(self):
        compile_original=h.g.compile
        def missing(value):
            if value['boundary']=='zero' and value['kernel']['fold']=='sum' and 'post' not in value and len(value['inputs'])==1:
                raise ValueError('tile input rectangle exceeds324 words')
            return compile_original(value)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h.g,'compile',side_effect=missing):
                with self.assertRaisesRegex(AssertionError,'missing declared source categories'):self.invoke(root)
            self.assertFalse((root/'summary.json').exists())

    def test_numerical_mismatch_is_retained_and_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h,'execute_host',return_value=[-1]):
                with self.assertRaisesRegex(AssertionError,'differential mismatch'):self.invoke(root)
            failure=json.loads((root/'failure.json').read_text())
            self.assertEqual(failure['actual'],[-1]);self.assertIn('source',failure['case'])
            self.assertFalse((root/'summary.json').exists())

    def test_declared_inputs_are_both_used_in_all_categories(self):
        cases=list(h.generated(226,24));categories=set()
        for case in cases:
            source=case['source'];count=len(source['inputs'])
            self.assertEqual({view['input'] for view in source['kernel']['views'].values()},set(range(count)))
            categories.add((source['boundary'],source['kernel']['fold'],'post' in source,count))
        self.assertEqual(len(categories),24)
