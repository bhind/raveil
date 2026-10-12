import copy,json,unittest
from unittest.mock import patch
from raveil import sonatine_fold as s
from tests import test_sonatine_fold as fixtures
from scripts.mf01_bridge_saved_audit import duplicate


class StandaloneEvidenceTests(unittest.TestCase):
    setUp=fixtures.ReceiptTests.setUp
    fake_run=fixtures.ReceiptTests.fake_run
    fixture=fixtures.ReceiptTests.fixture
    def test_typed_result_fields(self):
        root=self.fixture();original=json.loads((root/'receipt.json').read_text())
        for key,value in [('approved',1),('status',1.0),('sequence',True),('output',[float(x) for x in original['result']['output']])]:
            receipt=copy.deepcopy(original);receipt['result'][key]=value;(root/'receipt.json').write_text(json.dumps(receipt))
            with self.subTest(key=key),patch('subprocess.Popen',side_effect=AssertionError('saved verify executed')),self.assertRaises(ValueError):s.verify(root)
    def test_duplicate_fields_after_rehash(self):
        root=self.fixture();original=(root/'receipt.json').read_bytes();receipt=json.loads(original)
        for filename,key in [('receipt.json','schema'),('region.json','fold')]:
            path=root/filename;raw=path.read_bytes();path.write_bytes(duplicate(raw,key))
            if filename!='receipt.json':
                record=copy.deepcopy(receipt);record['files'][filename]=s.digest(path);(root/'receipt.json').write_text(json.dumps(record))
            with self.subTest(filename=filename),self.assertRaises(ValueError):s.verify(root)
            path.write_bytes(raw);(root/'receipt.json').write_bytes(original)
    def test_malformed_metadata_and_empty_version_reject_cleanly(self):
        root=self.fixture();original=json.loads((root/'receipt.json').read_text())
        for key,value in [('execution_directory',None),('qemu_executable',True),('files',None),('result',[]),('qemu_version',False)]:
            receipt=copy.deepcopy(original);receipt[key]=value;(root/'receipt.json').write_text(json.dumps(receipt))
            with self.subTest(key=key),self.assertRaises(ValueError):s.verify(root)
        (root/'qemu-version.txt').write_text('');original['files']['qemu-version.txt']=s.digest(root/'qemu-version.txt');(root/'receipt.json').write_text(json.dumps(original))
        with self.assertRaises(ValueError):s.verify(root)
