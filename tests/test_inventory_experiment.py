import unittest
from scripts.inventory_experiment import schedule, summarize, require_equivalent


class InventoryExperimentTests(unittest.TestCase):
    def test_complete_balanced_paired_order(self):
        rows = schedule(['a','b','c'])
        self.assertEqual(len(rows),18)
        self.assertEqual(rows[:4],[dict(case='a',repeat=0,variant='old'),
                                  dict(case='a',repeat=0,variant='new'),
                                  dict(case='b',repeat=0,variant='new'),
                                  dict(case='b',repeat=0,variant='old')])
        for name in ('a','b','c'):
            self.assertEqual({(r['repeat'],r['variant']) for r in rows if r['case']==name},
                             {(i,v) for i in range(3) for v in ('old','new')})

    def test_median_and_pair_not_pooled_or_unmatched(self):
        rows=[{**r,'elapsed_seconds':([2,4,100] if r['variant']=='old' else [1,3,5])[r['repeat']]}
              for r in schedule(['a'])]
        result=summarize(rows)[0]
        self.assertEqual(result['median_seconds'],dict(old=4,new=3))
        self.assertEqual(result['reduction'],.25)
        self.assertEqual([r['new_over_old'] for r in result['pairs']],[.5,.75,.05])
        for invalid in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):summarize(invalid)

    def test_trace_change_rejects_even_with_identical_counts(self):
        import copy
        metrics = dict(outputs=[], sessions=2, jobs=2, rtl_active_cycles=10,
                       reads=3, writes=2, transactions=5, interface_payload_bytes=20,
                       kernel_sha256='a'*64, build_sha256='b'*64,
                       job_metrics=[dict(trace_sha256='c'*64), dict(trace_sha256='d'*64)])
        previous = require_equivalent(None, metrics)
        self.assertEqual(require_equivalent(previous, metrics), previous)
        changed = copy.deepcopy(metrics)
        changed['job_metrics'][1]['trace_sha256']='e'*64
        with self.assertRaisesRegex(ValueError, 'trace'): require_equivalent(previous,changed)
        changed = copy.deepcopy(metrics); changed['job_metrics'].reverse()
        with self.assertRaises(ValueError): require_equivalent(previous,changed)
