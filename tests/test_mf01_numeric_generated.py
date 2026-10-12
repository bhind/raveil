import contextlib,copy,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import mf01_grid_generated as h


class SignedGeneratedTests(unittest.TestCase):
    def invoke(self,root):
        with patch.object(sys,'argv',['generated','--numeric','signed32','--seed','229','--count','1000','--output',str(root)]),contextlib.redirect_stdout(io.StringIO()):
            h.main()

    def test_default_unsigned_source_bytes_preserved(self):
        raw=h.p.encoded(list(h.generated(226,24)))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'5753af86c0e96e303f68051d2be2d9d2b97f42d2ed8d7167cb75d9ca9db6fac1')

    def test_expectations_do_not_call_production_compiler_or_oracles(self):
        with patch.object(h.g,'compile',side_effect=AssertionError('compiler called')),patch.object(h.g,'reference',side_effect=AssertionError('oracle called')),patch.object(h.d,'reference',side_effect=AssertionError('lowered oracle called')),patch.object(h.g,'lower_numeric',side_effect=AssertionError('lowering called')):
            cases=list(h.generated(229,96,'signed32'))
        self.assertEqual(len(cases),96)
        self.assertTrue(any(c['numeric_diagnostics']['signed_changed_cells'] for c in cases))
        self.assertEqual({c['source']['schema'] for c in cases},{h.g.SCHEMA_V4})

    def test_signed_and_unsigned_counterfactuals_match_separate_source_interpreter(self):
        compared=0
        for case in h.generated(229,96,'signed32'):
            source=case['source']
            try:h.g.compile(source)
            except ValueError as exc:
                self.assertIn(str(exc),{'tile input rectangle exceeds324 words','grid needs more than sixteen independent tiles'})
                continue
            self.assertEqual(h.g.reference(source),case['expected'])
            mutant=copy.deepcopy(source)
            for node in mutant['kernel']['nodes']+mutant.get('post',{}).get('nodes',[]):
                if node['op']=='max_i32':node['op']='max'
                elif node['op']=='relu_i32':node.update(op='add_imm',imm=0)
            self.assertEqual(h.g.reference(mutant),case['numeric_diagnostics']['counterfactual'])
            compared+=1
        self.assertGreater(compared,0)  # Rejected original partitions are checked above; no false-green empty comparison.

    def test_selected_categories_are_sensitive_and_use_all_declared_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';self.invoke(root)
            summary=json.loads((root/'summary.json').read_text())
        self.assertEqual(len(summary['selection']),24)
        self.assertEqual(summary['observable_signed_placements'],['kernel-max','kernel-relu','post-relu'])
        self.assertGreater(summary['counts']['sources_without_admission'],0)
        for item in summary['selection'].values():
            d=item['numeric_diagnostics']
            self.assertGreater(item['distinct_words'],1)
            self.assertGreater(d['signed_changed_cells'],0)
            self.assertGreater(d['outside_samples'],0)
            self.assertTrue(all(d['input_changed_cells']))

    def test_nonconstant_but_insensitive_cases_cannot_satisfy_selection(self):
        generated=h.generated
        def insensitive(seed,count,numeric):
            for case in generated(seed,count,numeric):
                case['numeric_diagnostics']['signed_changed_cells']=0
                yield case
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h,'generated',side_effect=insensitive),self.assertRaisesRegex(AssertionError,'missing signed-sensitive'):
                self.invoke(root)
            self.assertFalse((root/'summary.json').exists())

    def test_unobserved_operation_placement_cannot_report_coverage(self):
        generated=h.generated
        def missing(seed,count,numeric):
            for case in generated(seed,count,numeric):
                case['numeric_diagnostics']['operation_changed_cells']['post-relu']=0
                yield case
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            with patch.object(h,'generated',side_effect=missing),self.assertRaisesRegex(AssertionError,'missing observable signed'):
                self.invoke(root)
            self.assertFalse((root/'summary.json').exists())
