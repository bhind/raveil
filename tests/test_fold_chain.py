import copy
import ctypes as C
import struct
import unittest
import zlib
from raveil import fold_chain as chain,fold_bridge as bridge
from tests.test_fold_session import Session,session
from tests.test_sonatine_fold import Request
from tests import test_sonatine_fold as contract_tests
from scripts.affine_fold_vectors import vectors


def example(count=3,large=False):
    d=session(count);d['schema']='raveil.fold-chain.v1'
    if large:
        v=next(v for v in vectors() if v['name']=='add-16x16')
        for job in d['jobs']:job['region']=copy.deepcopy(v['descriptor']);job['inputs']=copy.deepcopy(v['inputs'])
    for i in range(1,count):d['jobs'][i]['inputs']=[{'from':f'job-{i-1}'},{'from':f'job-{i-1}'}]
    return d


class Chain(C.Structure):
    _fields_=[('jobs',Session),('sources',C.c_uint32*8),('masks',C.c_uint32*8)]


class ChainCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract_tests.FoldContractTests.setUpClass.__func__(cls)
        cls.lib.raveil_fold_chain_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Chain)]
        cls.lib.raveil_fold_chain_decode.restype=C.c_bool
        cls.lib.raveil_fold_bridge_encode.argtypes=[C.POINTER(Request),C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
        cls.lib.raveil_fold_bridge_encode.restype=C.c_bool
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def decode(self,blob):
        value=Chain();return self.lib.raveil_fold_chain_decode(blob,len(blob),C.byref(value)),value
    def test_max_chain_and_full_admission(self):
        for n in range(1,9):
            blob,children=chain.encode(example(n,True),99,list(range(1,n+1)))
            ok,c=self.decode(blob);self.assertTrue(ok);self.assertEqual(c.jobs.count,n)
            self.assertEqual(list(c.sources)[:n],[0xffffffff]+list(range(n-1)))
            self.assertEqual(list(c.masks)[:n],[0]+[3]*(n-1))
            for i,child in enumerate(children):self.assertEqual(blob[c.jobs.offsets[i]:c.jobs.offsets[i]+c.jobs.lengths[i]],child)
    def test_every_truncation_and_corruption(self):
        blob,_=chain.encode(example(2),99,[1,2])
        for n in range(len(blob)):self.assertFalse(self.decode(blob[:n])[0])
        for i in range(len(blob)):
            bad=bytearray(blob);bad[i]^=1;self.assertFalse(self.decode(bytes(bad))[0])
    def test_rehashed_invalid_links_and_nonzero_placeholders(self):
        blob,children=chain.encode(example(2),99,[1,2]);second=32+len(children[0]);child=second+8
        for offset,value in [(24,0),(28,4),(second,1),(second,0xffffffff),(second+4,0),(second+4,4),(child+292,7)]:
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value)
            if offset>=child:struct.pack_into('<I',bad,child+len(children[1])-8,zlib.crc32(bad[child:child+len(children[1])-8]))
            struct.pack_into('<I',bad,len(bad)-8,zlib.crc32(bad[:-8]))
            self.assertFalse(self.decode(bytes(bad))[0],offset)
    def test_materialized_encoder_matches_host_all_vectors(self):
        for v in vectors():
            if v['mode']!=0:continue
            blob=bridge.request_bytes(v['config'],v['inputs'],7);request=Request()
            self.assertTrue(self.lib.raveil_fold_decode(blob,len(blob),C.byref(request)))
            target=C.create_string_buffer(2892);size=C.c_size_t()
            self.assertFalse(self.lib.raveil_fold_bridge_encode(C.byref(request),target,len(blob)-1,C.byref(size)))
            self.assertTrue(self.lib.raveil_fold_bridge_encode(C.byref(request),target,len(target),C.byref(size)))
            self.assertEqual(target.raw[:size.value],blob)
    def test_host_rejects_forward_unknown_distinct_and_extent(self):
        for value in ({'from':'missing'},{'from':'job-1'},{'from':1}):
            d=example(2);d['jobs'][1]['inputs'][0]=value
            with self.assertRaises(ValueError):chain.validate(d)
        d=example(3);d['jobs'][2]['inputs'][0]={'from':'job-0'}
        with self.assertRaises(ValueError):chain.validate(d)
        d=example(2,True);d['jobs'][1]['region']=example(1)['jobs'][0]['region']
        with self.assertRaises(ValueError):chain.validate(d)


class ChainStateTests(unittest.TestCase):
    def test_bank_versions_and_both_input_aliases(self):
        d=example(8,True);model=chain.State(d)
        for i in range(8):
            job,source,destination=model.resolve(i);expected=chain.reference(job['region'],job['inputs'])
            if i:self.assertEqual(job['inputs'][0],job['inputs'][1]);self.assertEqual(source,(i-1)%2)
            model.commit(i,destination,expected,True)
            self.assertEqual(destination,i%2)
        self.assertEqual(model.versions,[5,5])
    def test_failed_producer_is_not_last_success_and_fault_preserves_banks(self):
        d=example(3);m=chain.State(d);m.commit(0,0,[7],True);saved=copy.deepcopy(m.banks)
        m.commit(1,1,[14],False);self.assertEqual(m.banks,saved);self.assertEqual(m.versions,[2,1])
        self.assertIsNone(m.resolve(2))
    def test_stale_producer_rejected_but_other_bank_remains_readable(self):
        d=example(4);d['jobs'][3]['inputs']=[{'from':'job-0'},{'from':'job-0'}]
        m=chain.State(d)
        for i in range(3):m.commit(i,i%2,[i+7],True)
        self.assertIsNone(m.resolve(3))
        d['jobs'][3]['inputs']=[{'from':'job-1'},{'from':'job-1'}]
        job,source,destination=m.resolve(3);self.assertEqual((source,destination),(1,0));self.assertEqual(job['inputs'],[[8],[8]])
