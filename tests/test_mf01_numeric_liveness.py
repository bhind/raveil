import unittest
from raveil import mf01_grid as grid,mf01_flow as flow
from raveil.affine_fold import compile_region
from scripts.mf01_numeric_extra_cases import shared_sign_live_input,wrapped_gemm_bias_relu
from tests import test_mf01_numeric as numeric


class NumericBoundaryTests(unittest.TestCase):
    def test_shared_sign_and_original_operand_survive_two_comparisons(self):
        source,expected=shared_sign_live_input();compiled=grid.compile(source)
        region=compiled['batch']['items'][0]['dag']['jobs'][0]['region']
        self.assertEqual(len(region['nodes']),15)
        self.assertEqual(compile_region(region)[8],16)  # Fifteen map nodes plus the fold.
        self.assertEqual(numeric.execute(source),expected)
        self.assertEqual(grid.reference(source),expected)
    def test_gemm_and_bias_wrap_before_signed_relu(self):
        source,expected=wrapped_gemm_bias_relu();outputs={}
        for name in flow.compile(source)['order']:
            stage=next(x for x in source['stages'] if x['name']==name)
            material=flow.materialize(stage['source'],outputs)
            outputs[name]=dict(rows=3,columns=5,words=numeric.execute(material))
        self.assertEqual(outputs['activation']['words'],expected)
        self.assertEqual(flow.reference(source),[dict(name='activation',rows=3,columns=5,words=expected)])
