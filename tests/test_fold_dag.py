import copy,ctypes as C,random,struct,unittest,zlib
from raveil import fold_dag as d
from tests.test_fold_session import Session
from tests import test_sonatine_fold as contract_tests
from scripts.fold_dag_cases import job,linked,graph,scenarios,rejected_graphs,raw_encode


class Dag(C.Structure):
    _fields_=[('jobs',Session),('sources',(C.c_uint32*2)*8),('destinations',(C.c_uint32*2)*8),
              ('chunks',C.c_uint32*8),('last_use',C.c_uint32*8),('output',C.c_uint32),('input_offsets',(C.c_uint32*2)*8)]


class DagContractTests(unittest.TestCase):
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
            self.assertEqual(list(actual.sources[i]),plan['sources'][i]);self.assertEqual(actual.chunks[i],plan['chunks'][i])
            self.assertEqual(list(actual.destinations[i])[:actual.chunks[i]],plan['slots'][i]);self.assertEqual(actual.last_use[i],plan['last_use'][i])
    def test_all_accepted_fixtures_and_exact_four_refs(self):
        for name,g,_ in scenarios():
            with self.subTest(name=name):self.compare(g)
    def test_five_refs_and_capacity_reject_before_dispatch(self):
        for name,g in rejected_graphs().items():
            with self.subTest(name=name):
                with self.assertRaises(ValueError):d.compile_plan(g)
                self.assertFalse(self.decode(raw_encode(g))[0])
    def test_pinned_output_and_unequal_object_versions(self):
        g=next(g for name,g,_ in scenarios() if name=='unequal-versions-pinned-output');m=d.State(g)
        for i in range(len(g['jobs'])):
            j,reads,writes=m.resolve(i);m.commit(i,writes,d.reference(j['region'],j['inputs']),True)
        self.assertEqual([o['version'] for o in m.final()['objects']],[4,2]);self.assertEqual(m.plan['slots'][3],[2])
    def test_randomized_plans_match_c_and_do_not_reuse_live_reads(self):
        rng=random.Random(216)
        for _ in range(200):
            jobs=[]
            for i in range(rng.randint(1,8)):
                j=job(f'j{i}',128)
                for b in range(2):
                    if i and rng.random()<.7:j['inputs'][b]={'from':f'j{rng.randrange(i)}'}
                jobs.append(j)
            g=graph(jobs,jobs[rng.randrange(len(jobs))]['name']);self.compare(g);plan=d.compile_plan(g)
            for i,srcs in enumerate(plan['sources']):
                reads={slot for src in srcs if src!=0xffffffff for slot in plan['slots'][src]}
                self.assertFalse(reads.intersection(plan['slots'][i]))
    def test_every_truncation_corruption_and_rehashed_header(self):
        g=graph([job('a',1),job('b',1,linked('a'))]);blob,_=d.encode(g,99,[1,2])
        for n in range(len(blob)):self.assertFalse(self.decode(blob[:n])[0])
        for i in range(len(blob)):
            bad=bytearray(blob);bad[i]^=1;self.assertFalse(self.decode(bytes(bad))[0])
        for offset,value in [(4,2),(12,9),(24,2),(28,1),(32,0)]:
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value);struct.pack_into('<I',bad,len(bad)-8,zlib.crc32(bad[:-8]))
            self.assertFalse(self.decode(bytes(bad))[0])
    def test_invalid_links_extents_and_output_names(self):
        g=graph([job('a',1),job('b',1,linked('a'))])
        for output in ['missing',1]:
            bad=copy.deepcopy(g);bad['output']=output
            with self.assertRaises(ValueError):d.validate(bad)
        for source in ['b','missing',1]:
            bad=copy.deepcopy(g);bad['jobs'][1]['inputs'][0]={'from':source}
            with self.assertRaises(ValueError):d.validate(bad)
        bad=copy.deepcopy(g);bad['jobs'][1]=job('b',128,linked('a'))
        with self.assertRaises(ValueError):d.validate(bad)
    def test_failed_producer_and_no_output_fallback(self):
        g=graph([job('a',1),job('b',1,linked('a'))]);m=d.State(g)
        m.commit(0,1,[7],False);self.assertIsNone(m.resolve(1));self.assertFalse(m.final()['available'])
        self.assertEqual(m.versions,[1]*8);self.assertEqual(m.final()['output'],[])


class DagPreviewAndReaderTests(unittest.TestCase):
    def test_preview_exposes_deduplicated_refs_and_pinned_output(self):
        g=next(g for n,g,_ in scenarios() if n=='diamond');preview=d.preview(g)
        self.assertEqual([j['references'] for j in preview['jobs']],[1,2,2,3])
        self.assertEqual(preview['jobs'][0]['last_use'],2)
        self.assertTrue(preview['jobs'][-1]['pinned_output'])
    def test_uart_line_bound_is_explicit_and_finite(self):
        from raveil.fold_bridge import Reader
        for length,limit,ok in [(8192,8192,True),(8193,8192,False),(8500,16384,True),(16385,16384,False)]:
            reader=Reader.__new__(Reader);reader.buffer=bytearray(b'x'*length+b'\n');reader.line_limit=limit
            if ok:self.assertEqual(len(reader.line()),length)
            else:
                with self.assertRaises(ValueError):reader.line()
        for limit in [True,8191,16385]:
            with self.assertRaises(ValueError):Reader(None,None,0,line_limit=limit)
