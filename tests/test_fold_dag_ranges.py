import copy
import ctypes as C
import random
import struct
import unittest
import zlib
from raveil import fold_dag as d
from tests.test_fold_dag import Dag
from tests import test_sonatine_fold as contract_tests
from scripts.fold_dag_range_cases import job,link,ranged,scenarios,rejected_graphs,raw_encode


class RangeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract_tests.FoldContractTests.setUpClass.__func__(cls)
        cls.lib.raveil_fold_dag_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Dag)]
        cls.lib.raveil_fold_dag_decode.restype=C.c_bool
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def decode(self,blob):
        result=Dag();return self.lib.raveil_fold_dag_decode(blob,len(blob),C.byref(result)),result
    def compare(self,g):
        plan=d.compile_plan(g);blob,_=d.encode(g,99,list(range(1,len(g['jobs'])+1)));ok,actual=self.decode(blob)
        self.assertTrue(ok);self.assertEqual(actual.output,plan['output'])
        for i in range(len(g['jobs'])):
            self.assertEqual(list(actual.sources[i]),plan['sources'][i]);self.assertEqual(list(actual.input_offsets[i]),plan['offsets'][i])
            self.assertEqual(list(actual.destinations[i])[:actual.chunks[i]],plan['slots'][i]);self.assertEqual(actual.last_use[i],plan['last_use'][i])
    def test_owned_cases_match_c_and_sliced_values(self):
        for name,g,_ in scenarios():
            with self.subTest(name=name):
                self.compare(g);model=d.State(g)
                for i,j in enumerate(g['jobs']):
                    resolved,reads,writes=model.resolve(i)
                    for b,operand in enumerate(j['inputs']):
                        if isinstance(operand,dict):
                            src=model.plan['sources'][i][b];start=operand.get('offset',0);length=operand.get('length',len(model.producers[src][1]))
                            self.assertEqual(resolved['inputs'][b],model.producers[src][1][start:start+length])
                    self.assertFalse(reads&writes);self.assertLessEqual(reads.bit_count()+writes.bit_count(),4)
                    model.commit(i,writes,d.reference(resolved['region'],resolved['inputs']),True)
                self.assertTrue(model.final()['available'])
        g=next(scenarios())[1];self.assertEqual(d.preview(g)['jobs'][-1]['references'],3)
        self.assertEqual(d.preview(g)['jobs'][-1]['read_objects'],[2,3])
    def test_invalid_ranges_and_five_refs_reject_in_both(self):
        for name,g in rejected_graphs().items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):d.compile_plan(g)
                self.assertFalse(self.decode(raw_encode(g))[0])
        for value in [-1,True,1.0,'0']:
            g=next(scenarios())[1];g['jobs'][2]['inputs'][0]['offset']=value
            with self.assertRaises(ValueError):d.compile_plan(g)
        g=next(scenarios())[1];g['schema']='raveil.fold-dag.v1'
        with self.assertRaises(ValueError):d.compile_plan(g)
    def test_random_ranges_lifetimes_and_dedup_match_c(self):
        rng=random.Random(219)
        for _ in range(200):
            jobs=[job('a',256),job('b',256)]
            for i in range(rng.randint(1,6)):
                n=rng.choice([1,128]);operands=[]
                for b in range(2):
                    source=rng.randrange(len(jobs));size=jobs[source]['region']['shape'][0]*jobs[source]['region']['shape'][1]
                    if size<n:operands.append([3]*n)
                    else:operands.append(link(jobs[source]['name'],rng.randrange(size-n+1),n))
                jobs.append(job(f'j{i}',n,operands))
            g=ranged(jobs)
            try:d.compile_plan(g)
            except ValueError:self.assertFalse(self.decode(raw_encode(g))[0])
            else:self.compare(g)
    def test_literal_reserved_fields_and_wire_range_overflow(self):
        g=next(scenarios())[1];blob=bytearray(raw_encode(g))
        for offset,value in [(36,1),(40,0),(32,0),(4,3)]:
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value);struct.pack_into('<I',bad,len(bad)-8,zlib.crc32(bad[:-8]))
            self.assertFalse(self.decode(bytes(bad))[0])
        for size in range(len(blob)):self.assertFalse(self.decode(bytes(blob[:size]))[0])
    def test_full_producer_lifetime_and_failure_remain_conservative(self):
        g=next(scenarios())[1];model=d.State(g)
        resolved,reads,writes=model.resolve(0);model.commit(0,writes,d.reference(resolved['region'],resolved['inputs']),False)
        resolved,reads,writes=model.resolve(1);model.commit(1,writes,d.reference(resolved['region'],resolved['inputs']),True)
        self.assertIsNone(model.resolve(2));self.assertFalse(model.final()['available'])
        self.assertEqual(model.plan['last_use'][:2],[2,2])
    def test_maximum_v2_envelope(self):
        g=ranged([job(f'j{i}',256) for i in range(8)])
        for j in g['jobs']:j['region']['lengths']=[324,324];j['inputs']=[list(range(324)),list(range(324))]
        blob,_=d.encode(g,99,list(range(1,9)));self.assertEqual(len(blob),23368);self.compare(g)
