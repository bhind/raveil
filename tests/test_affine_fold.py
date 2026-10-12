import copy
import random
import unittest

from raveil.affine_fold import MASK, compile_region, reference, validate_config
from scripts.affine_fold_vectors import vectors, region, load, binary


class AffineFoldTests(unittest.TestCase):
    def setUp(self):
        self.d=region([2,3],4,[8,12],
                      {"a":[0,0,4,0,1],"b":[1,0,0,1,3]},binary("mul"),"x")

    def test_direct_formula_vectors(self):
        cases=vectors()
        self.assertEqual(len(cases),71)
        self.assertEqual(sum(len(c["expected"]) for c in cases if c["mode"]==0),2038)

    def test_random_rectangular_matmul(self):
        rng=random.Random(9210)
        for _ in range(100):
            m,n,k=[rng.randint(1,16) for _ in range(3)]
            d=region([m,n],k,[m*k,k*n],
                     {"a":[0,0,k,0,1],"b":[1,0,0,1,n]},binary("mul"),"x")
            a=[rng.getrandbits(32) for _ in range(m*k)]
            b=[rng.getrandbits(32) for _ in range(k*n)]
            self.assertEqual(reference(d,[a,b]),
                             [sum(a[i*k+t]*b[t*n+j] for t in range(k))&MASK
                              for i in range(m) for j in range(n)])

    def test_duplicate_operand_and_dead_value_register_reuse(self):
        d=region([1,1],1,[1,0],{"a":[0,0,0,0,0]},
                 [load("dead","a"),load("x","a"),
                  dict(id="square",op="mul",args=["x","x"]),
                  dict(id="twice",op="add",args=["square","square"])],"twice")
        c=compile_region(d)
        self.assertEqual(c[8],5)
        self.assertEqual(reference(d,[[MASK],[]]),[2])

    def test_register_pressure_rejects(self):
        nodes=[load(f"l{i}","a") for i in range(9)]
        previous="l0"
        for i in range(1,9):
            nodes.append(dict(id=f"s{i}",op="add",args=[previous,f"l{i}"]))
            previous=f"s{i}"
        # Within instruction bound: all loads retained by a ninth load plus
        # subsequent references cannot fit8; use only six of the references.
        nodes=nodes[:9]+[dict(id="s1",op="add",args=["l0","l1"]),
                         dict(id="s2",op="add",args=["l2","l3"]),
                         dict(id="s3",op="add",args=["l4","l5"]),
                         dict(id="s4",op="add",args=["l6","l7"]),
                         dict(id="s5",op="add",args=["l8","s4"])]
        d=region([1,1],1,[1,0],{"a":[0,0,0,0,0]},nodes,"s5")
        with self.assertRaisesRegex(ValueError,"eight live"):
            compile_region(d)

    def test_strict_scalar_and_shape_bounds(self):
        for field, values in (("shape",([0,1],[1,17],[True,1])),
                              ("extent",(0,65,True)),
                              ("lengths",([325,12],[-1,12],[True,12])),
                              ("fold",("mean",False))):
            for v in values:
                with self.subTest(field=field,value=v):
                    d=copy.deepcopy(self.d);d[field]=v
                    with self.assertRaises(ValueError): compile_region(d)

    def test_affine_bounds_and_unused_words(self):
        c=compile_region(self.d)
        for pos,value in ((9,2),(10,8),(11,MASK),(12,324),(13,324),(19,1),(64,1)):
            with self.subTest(pos=pos):
                bad=c.copy();bad[pos]=value
                with self.assertRaises(ValueError): validate_config(bad)
        for pos in (1,2,3,7,8):
            bad=c.copy();bad[pos]=0
            with self.assertRaises(ValueError): validate_config(bad)

    def test_instruction_admission(self):
        c=compile_region(self.d)
        for pc,word in ((0,0),(0,1<<28 | 7<<22),(0,1<<28 | 1),
                        (1,2<<28 | 7<<22),(2,5<<28 | 1),
                        (3,3<<28 | 1),(3,3<<28 | 7<<22),
                        (3,3<<28 | 1<<25),(2,3<<28)):
            with self.subTest(pc=pc,word=word):
                bad=c.copy();bad[49+pc]=word
                with self.assertRaises(ValueError): validate_config(bad)

    def test_immediates_and_arithmetic_order(self):
        d=region([1,1],1,[1,0],{"a":[0,0,0,0,0]},
                 [load("x","a"),dict(id="y",op="add_imm",args=["x"],imm=1),
                  dict(id="z",op="ge_imm",args=["y"],imm=1)],"z")
        self.assertEqual(reference(d,[[MASK],[]]),[0])
        for x in (-1,1<<22,True):
            d["nodes"][1]["imm"]=x
            with self.assertRaises(ValueError): compile_region(d)

    def test_dependency_and_schema_rejection(self):
        for mutation in ("cycle","duplicate","unknown-view","extra-field","unknown-result"):
            d=copy.deepcopy(self.d)
            if mutation=="cycle": d["nodes"][2]["args"]=["x","a"]
            if mutation=="duplicate": d["nodes"][1]["id"]="a"
            if mutation=="unknown-view": d["nodes"][0]["view"]="z"
            if mutation=="extra-field": d["new"]=1
            if mutation=="unknown-result": d["result"]="z"
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError): compile_region(d)

    def test_cli_uses_same_strict_source_parser(self):
        import contextlib,io,json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from raveil.affine_fold import main
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'region.json';raw=json.dumps(self.d)
            with patch('sys.argv',['affine-fold',str(path)]):
                path.write_text('{"extent":0,'+raw[1:])
                with self.assertRaisesRegex(ValueError,'duplicate evidence field'):main()
                path.write_text(raw);output=io.StringIO()
                with contextlib.redirect_stdout(output):main()
                self.assertEqual(json.loads(output.getvalue())['configuration'],compile_region(self.d))

    def test_input_boundary(self):
        for inputs in ([[0]*8,[0]*11], [[0]*8,[MASK+1]*12], [[0]*8,[True]*12]):
            with self.assertRaises(ValueError): reference(self.d,inputs)


if __name__=="__main__": unittest.main()
