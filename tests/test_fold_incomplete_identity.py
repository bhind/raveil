import unittest
from unittest.mock import patch
from raveil import project as p,project_fold as f
from tests import test_project_fold as fixtures


class IncompleteIdentityTests(unittest.TestCase):
    setUp=fixtures.FoldProjectTests.setUp
    save=fixtures.FoldProjectTests.save
    fake=fixtures.FoldProjectTests.fake
    run_fixture=fixtures.FoldProjectTests.run_fixture
    reseal=fixtures.FoldProjectTests.reseal
    def test_missing_build_after_precancel_still_valid(self):
        record=self.run_fixture(cancelled=lambda:True);root=self.project.root/'folds'/record['id']
        self.assertFalse((root/'build').exists())
        with patch('subprocess.Popen',side_effect=AssertionError('saved load executed')):self.assertEqual(f.load(self.project,record['id']),record)
    def test_incomplete_plan_requires_well_formed_build_identity(self):
        for value in [True,1.0,None,{},'fixture','G'*64,'f'*63]:
            record=self.run_fixture(cancelled=lambda:True);path=self.project.root/'folds'/record['id']/'plan.json'
            plan=f._json(path.read_bytes());plan['build_sha256']=value;path.write_bytes(p.encoded(plan));self.reseal(record)
            with self.subTest(value=value),patch('subprocess.Popen',side_effect=AssertionError('saved load executed')),self.assertRaises(ValueError):f.load(self.project,record['id'])
    def test_nonobject_options_reject_cleanly(self):
        for value in [None,True,1]:
            record=self.run_fixture(cancelled=lambda:True);path=self.project.root/'folds'/record['id']/'plan.json'
            plan=f._json(path.read_bytes());plan['options']=value;path.write_bytes(p.encoded(plan));self.reseal(record)
            with self.subTest(value=value),self.assertRaises(ValueError):f.load(self.project,record['id'])
