"""General grid workflow with injected host runners; not RTL evidence."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from raveil import grid_kernel as k, project_tiling as t, project_composition as c
from raveil.cli import main
from raveil.project import Project, init_project, encoded, digest, tree, MAX_ENTRIES, MAX_BYTES
from tests.test_project_graph import host_fixture_runner
from tests.test_grid_kernel import grid, rich_kernel


def neighbor_kernel(bias=5):
    return {'schema':k.KERNEL,'graph_id':'editable-neighbor','nodes':[
        {'id':'center','op':'LOAD_U32','address':{'row_delta':0,'column_delta':0}},
        {'id':'west','op':'LOAD_U32','address':{'row_delta':0,'column_delta':-1}},
        {'id':'max','op':'MAX_U32','inputs':['center','west']},
        {'id':'bias','op':'ADD_IMM_U32','input':'max','immediate':bias},
        {'id':'out','op':'STORE_U32','input':'bias'}]}


class GeneralTilingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=init_project(Path(self.temp.name)/'project');self.project=Project(self.root)
        self.save(17,19)

    def save(self, rows, columns, kernel=None):
        self.data=grid(rows,columns)
        self.kernel=kernel or neighbor_kernel()
        (self.root/'inputs/grid.json').write_bytes(encoded(self.data))
        (self.root/'inputs/kernel.json').write_bytes(encoded(self.kernel))

    def run_grid(self, runner=host_fixture_runner, **kw):
        with patch('raveil.project_graph.run_snapshot',side_effect=runner):
            return t.run(self.project,'grid.json',kernel_file='kernel.json',**kw)

    def parent(self,r):return self.root/'tilings'/r['tiling_id']

    def test_arbitrary_rectangles_partial_edges_and_all_boundaries(self):
        for shape,mode in [((1,1),'zero'),((1,64),'wrap'),((64,1),'clamp'),((17,19),'wrap'),((31,33),'zero')]:
            self.save(*shape)
            result=self.run_grid(boundary=mode)
            self.assertEqual(result['status'],'succeeded',result['error'])
            words=self.data['words'];rows,cols=shape;expected=[]
            for r in range(rows):
                for col in range(cols):
                    center=words[r*cols+col]
                    left=words[r*cols+col-1] if col else (0 if mode=='zero' else center if mode=='clamp' else words[r*cols+cols-1])
                    expected.append((max(center,left)+5)&0xffffffff)
            self.assertEqual(result['output'],{'rows':rows,'columns':cols,'words':expected,'sha256':result['output']['sha256']})
            self.assertEqual(t.load(self.project,result['tiling_id']),result)

    def test_full_limit_tree_with_sixteen_children_and_worst_case_values(self):
        self.save(64,64)
        self.data['words']=[0xffffffff]*4096
        (self.root/'inputs/grid.json').write_bytes(encoded(self.data))
        result=self.run_grid(boundary='wrap')
        self.assertEqual(result['status'],'succeeded',result['error'])
        self.assertEqual(len(result['children']),16)
        self.assertEqual(result['output']['words'],[4]*4096)
        manifest=tree(self.parent(result))
        self.assertLess(len(manifest),MAX_ENTRIES)
        size=sum(f.stat().st_size for f in self.parent(result).rglob('*') if f.is_file())
        self.assertLess(size,MAX_BYTES)
        self.assertEqual(t.load(self.project,result['tiling_id']),result)

    def test_check_is_read_only_and_reports_actual_admission(self):
        old=tree(self.root)
        with patch('raveil.project_graph.run_snapshot',side_effect=AssertionError('no execution')):
            preview=t.check(self.project,'grid.json',kernel_file='kernel.json',boundary='clamp')
        self.assertEqual(preview,{'rows':17,'columns':19,'tiles':4,'instructions':5,'boundary':'clamp','graph_id':'editable-neighbor'})
        self.assertEqual(tree(self.root),old)

    def test_invalid_scope_is_rejected_before_attempt_creation(self):
        for bad in ('../kernel.json','bad',None):
            with self.assertRaises(ValueError):t.run(self.project,'grid.json',kernel_file=bad)
        for field,value in [('rows',65),('schema',t.INPUT)]:
            (self.root/'inputs/grid.json').write_bytes(encoded({**self.data,field:value}))
            with self.assertRaises(ValueError):self.run_grid()
        self.save(17,19)
        for mode in ('mirror',None,True,[]):
            with self.assertRaises(ValueError):self.run_grid(boundary=mode)
        malformed=copy.deepcopy(self.kernel);malformed['nodes'][0]['address']['row_delta']=2
        (self.root/'inputs/kernel.json').write_bytes(encoded(malformed))
        with self.assertRaises(ValueError):self.run_grid()
        self.assertFalse((self.root/'tilings').exists())

    def test_input_and_kernel_are_frozen_together_before_execution(self):
        expected=k.reference(self.data,k.compile_kernel(encoded(self.kernel)),'wrap')
        def runner(*a,**kw):
            (self.root/'inputs/grid.json').write_text('{}')
            (self.root/'inputs/kernel.json').write_text('{}')
            return host_fixture_runner(*a,**kw)
        result=self.run_grid(runner,boundary='wrap')
        self.assertEqual(result['status'],'succeeded',result['error'])
        self.assertEqual(result['output']['words'],expected)
        self.assertEqual(t.load(self.project,result['tiling_id']),result)

    def test_edits_compare_complete_snapshots_without_execution_or_writes(self):
        first=self.run_grid(boundary='clamp');old=tree(self.parent(first))
        self.kernel['nodes'][3]['immediate']=7
        (self.root/'inputs/kernel.json').write_bytes(encoded(self.kernel))
        second=self.run_grid(boundary='clamp')
        with patch('raveil.project_graph.run_snapshot',side_effect=AssertionError('no execution')):
            before=tree(self.root)
            report=t.compare(self.project,first['tiling_id'],second['tiling_id'])
            t.inspect(self.project,first['tiling_id']);t.history(self.project)
            self.assertEqual(tree(self.root),before)
        self.assertTrue(report['kernel_changed']);self.assertEqual(report['input_cells_changed'],0)
        self.assertEqual(report['output_cells_changed'],323)
        self.assertEqual(report['changed_cells'][0],[0,0]);self.assertEqual(report['changed_cells'][-1],[16,18])
        self.assertEqual(tree(self.parent(first)),old)

    def test_comparison_reports_boundary_input_and_rejects_shape_build_incomplete(self):
        a=self.run_grid();b=self.run_grid(boundary='wrap')
        report=t.compare(self.project,a['tiling_id'],b['tiling_id'])
        self.assertEqual((report['boundary_before'],report['boundary_after']),('zero','wrap'))
        self.data['words'][0]^=1;(self.root/'inputs/grid.json').write_bytes(encoded(self.data))
        changed=self.run_grid()
        self.assertEqual(t.compare(self.project,a['tiling_id'],changed['tiling_id'])['input_cells_changed'],1)
        self.save(1,1);different=self.run_grid()
        with self.assertRaisesRegex(ValueError,'shape'):t.compare(self.project,a['tiling_id'],different['tiling_id'])
        failed=self.run_grid(cancelled=lambda:True)
        with self.assertRaisesRegex(ValueError,'complete'):t.compare(self.project,different['tiling_id'],failed['tiling_id'])
        def other(*args,**kwargs):
            value=host_fixture_runner(*args,**kwargs);value['receipt']['simulator_sha256']='f'*64;return value
        build=self.run_grid(other)
        with self.assertRaisesRegex(ValueError,'build'):t.compare(self.project,different['tiling_id'],build['tiling_id'])

    def test_failed_edge_tile_retains_evidence_and_fresh_retry(self):
        calls=0
        def fail(*a,**kw):
            nonlocal calls
            calls+=1
            if calls==4:raise ValueError('edge failure')
            return host_fixture_runner(*a,**kw)
        result=self.run_grid(fail)
        self.assertEqual(result['status'],'incomplete');self.assertEqual(len(result['children']),3)
        self.assertIsNone(t.load(self.project,result['tiling_id'])['output'])
        saved=tree(self.parent(result));retry=self.run_grid()
        self.assertEqual(retry['status'],'succeeded');self.assertNotEqual(retry['tiling_id'],result['tiling_id'])
        self.assertEqual(tree(self.parent(result)),saved)

    def test_cancellation_all_variable_tile_boundaries(self):
        self.save(1,17)
        for stop in range(1,6):
            calls=0
            def cancelled():
                nonlocal calls
                calls+=1;return calls==stop
            result=self.run_grid(cancelled=cancelled)
            self.assertEqual(result['status'],'incomplete');self.assertIsNone(result['output'])
            if stop==5:self.assertFalse((self.parent(result)/'record.json').exists())
            else:self.assertIsNone(t.load(self.project,result['tiling_id'])['output'])

    def test_resealed_plan_changes_cannot_forge_extents_halos_or_kernel(self):
        result=self.run_grid();root=self.parent(result)
        original=(root/'plan.json').read_bytes()
        for edit in (lambda x:x.update(boundary='clamp'),lambda x:x.update(rows=16),
                     lambda x:x['tiles'][3].update(rows=16),lambda x:x['tiles'][0].update(slot=True),
                     lambda x:x['tiles'].pop(),lambda x:x.update(kernel_file='../evil.json')):
            plan=json.loads(original);edit(plan);(root/'plan.json').write_bytes(encoded(plan))
            with self.assertRaises(ValueError):t.load(self.project,result['tiling_id'])
        (root/'plan.json').write_bytes(original)
        (root/'kernel.json').write_bytes(encoded(neighbor_kernel(99)))
        with self.assertRaises(ValueError):t.load(self.project,result['tiling_id'])

    def test_resealed_result_dimensions_types_and_children_rejected(self):
        result=self.run_grid();root=self.parent(result)
        for edit in (lambda x:x['output'].update(rows=True),lambda x:x['output'].update(columns=20),
                     lambda x:x['children'].append(x['children'][0]),lambda x:x['children'].__setitem__(1,x['children'][0]),
                     lambda x:x['output']['words'].__setitem__(0,True),lambda x:x.update(schema=t.RESULT)):
            fake=copy.deepcopy(result);edit(fake);raw=encoded(fake)
            (root/'record.json').write_bytes(raw);(root/'record.sha256').write_text(digest(raw)+'\n')
            with self.assertRaises(ValueError):t.load(self.project,result['tiling_id'])

    def test_kernel_symlink_and_build_drift_rejected(self):
        path=self.root/'inputs/kernel.json';raw=path.read_bytes();path.unlink()
        other=Path(self.temp.name)/'kernel.json';other.write_bytes(raw);path.symlink_to(other)
        with self.assertRaises(ValueError):self.run_grid()
        path.unlink();path.write_bytes(raw)
        calls=0
        def drift(*a,**kw):
            nonlocal calls
            calls+=1;result=host_fixture_runner(*a,**kw)
            if calls==3:result['receipt']['rtl_manifest_sha256']='f'*64
            return result
        result=self.run_grid(drift)
        self.assertEqual(result['status'],'incomplete');self.assertIsNone(result['output'])

    def test_cli_generic_run_check_diff_and_inspect(self):
        options=['--project',str(self.root),'--input','grid.json','--kernel','kernel.json','--boundary','wrap']
        before=tree(self.root)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','tile-check',*options]),0)
        self.assertEqual(json.loads(out.getvalue())['tiles'],4);self.assertEqual(tree(self.root),before)
        with patch('raveil.project_graph.run_snapshot',side_effect=host_fixture_runner),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','tile-run',*options]),0)
        identity=out.getvalue().split('tiling=')[1].split()[0]
        with patch('raveil.project_graph.run_snapshot',side_effect=AssertionError('no execution')),contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['project','tile-diff',identity,identity,'--project',str(self.root)]),0)
        self.assertEqual(json.loads(out.getvalue())['output_cells_changed'],0)
        self.assertIn('output=17x19',t.inspect(self.project,identity))


if __name__=='__main__':unittest.main()
