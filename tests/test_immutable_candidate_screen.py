"""Independent small exact cases for T-0202 structural/equivalence claims."""
from fractions import Fraction
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'docs/research/probes'))
import immutable_candidate_screen as screen
import pythia_affine_reference as ref


def fraction_rank(rows):
    # Independent column-basis construction over Q, no modular inversion.
    basis = {}
    for column in zip(*rows):
        v = list(map(Fraction,column))
        for pivot,b in sorted(basis.items()):
            factor=v[pivot]
            v=[x-factor*y for x,y in zip(v,b)]
        p=next((i for i,x in enumerate(v) if x),None)
        if p is not None:
            divisor=v[p]
            basis[p]=[x/divisor for x in v]
    return len(basis)


class CandidateScreenTests(unittest.TestCase):
    def test_rank_exact_reference_and_modular_exception(self):
        matrices=([[1,2],[2,4],[3,6]], [[1,0],[0,1],[3,2]],
                  [[0,0],[0,0]], [[0,1,2],[1,0,1],[0,2,4]])
        for matrix in matrices:
            for p in screen.PRIMES:
                self.assertEqual(screen.modular_rank(matrix,p),fraction_rank(matrix))
        # A deficient modular result alone cannot prove deficient rational rank.
        self.assertEqual(screen.modular_rank([[65521]],65521),0)
        self.assertEqual(fraction_rank([[65521]]),1)
        with self.assertRaisesRegex(ValueError,'prime field'):
            screen.modular_rank([[1]],15)

    def test_hadamard_against_direct_matrix(self):
        values=[3,-8,1,6,0,2,-4,9]
        direct=[sum(x*(-1 if (i&j).bit_count()%2 else 1)
                    for j,x in enumerate(values)) for i in range(8)]
        self.assertEqual(screen.hadamard(values),direct)
        self.assertEqual(screen.hadamard(direct),[8*x for x in values])
        with self.assertRaisesRegex(ValueError,'power-of-two'):
            screen.hadamard([1,2,3])

    def test_same_column_only_and_signed_zero(self):
        raw=struct.pack('<4e',1,1,1,1)
        plan=screen.dictionary_plan(raw,2,2)
        actual,mults=screen.shared_products(plan,[0.0,0.0],[2.0,3.0])
        self.assertEqual(actual,[5.0,5.0])
        self.assertEqual(mults,2)  # Never share x0 and x1 merely because c matches.
        signed=screen.dictionary_plan(struct.pack('<2H',0,0x8000),2,1)
        self.assertEqual(len(signed[0][0]),2)
        with self.assertRaisesRegex(ValueError,'nonfinite'):
            screen.dictionary_plan(struct.pack('<H',0x7c00),1,1)

    def test_shared_order_cancellation_and_exact_oracle(self):
        weights=[65504.,-65504.,2.**-24,8.]*2
        raw=struct.pack('<8e',*weights)
        wf,wi=ref.decode(raw); bf,bi=ref.decode(struct.pack('<2e',1.,-1.))
        xf,xi=ref.decode(struct.pack('<4e',8.,8.,2.**-24,-8.))
        result,mults=screen.shared_products(screen.dictionary_plan(raw,2,4),bf,xf)
        self.assertEqual(result,ref.serial(wf,bf,xf));self.assertEqual(mults,4)
        exact,scales=ref.oracle(wi,bi,xi);ref.validate(result,exact,scales)

    def test_generic_da_width_includes_positive_endpoint_and_bias(self):
        max_input=8*(1<<24)
        self.assertGreater(max_input,(1<<27)-1)  # 28 signed bits are insufficient.
        max_total=(65504*8*128+65504)*(1<<48)
        self.assertEqual(max_total.bit_length()+1,76)

    def test_source_failure_before_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'weight.f16').write_bytes(b'\0'*131072)
            with patch.object(screen,'dictionary_plan',side_effect=AssertionError('analysis reached')):
                with self.assertRaisesRegex(ValueError,'SHA-256'):
                    screen.run(p)


if __name__=='__main__':
    unittest.main()
