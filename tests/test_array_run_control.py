"""Host lifecycle and immutable-proof regressions; fixtures are not RTL evidence."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from raveil import run_control as c, project as p, project_array as a
from raveil import project_fold as f, fold_dag as d, fold_bridge as bridge
from raveil.cli import main
from tests import test_project_dag_batch as fixtures
from tests.test_array_program import program


class ControlTests(unittest.TestCase):
    def test_finite_budget_validation_and_no_global_state_leak(self):
        for value in (True, False, 0, -.1, .009, 86401, float('nan'), float('inf'), '1'):
            with self.assertRaises(ValueError): c.Control(value)
        outer, inner = c.Control(), c.Control()
        with outer.active():
            self.assertIs(c.current(), outer)
            with inner.active(): self.assertIs(c.current(), inner)
            self.assertIs(c.current(), outer)
        self.assertIsNone(c.current())

    def test_real_signals_deferred_repeated_and_restored(self):
        old = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
        control = c.Control()
        with control.active(signals=True):
            os.kill(os.getpid(), signal.SIGINT); os.kill(os.getpid(), signal.SIGINT)
            os.kill(os.getpid(), signal.SIGTERM)
            with self.assertRaises(c.Stopped) as caught: c.checkpoint()
            self.assertEqual(caught.exception.code, 130)
        self.assertEqual(old, {s: signal.getsignal(s) for s in old})

    def test_overall_and_coupled_budget_without_reset(self):
        clock = Mock(return_value=10.)
        with patch.object(c.time, 'monotonic', clock):
            control = c.Control(3)
            with control.active():
                clock.return_value=12
                with self.assertRaises(c.Stopped) as caught:
                    with c.coupled_deadline(11): pass
                self.assertEqual(caught.exception.reason, 'coupled job timeout')
                c.checkpoint()
                clock.return_value=14
                with self.assertRaises(c.Stopped) as caught: c.checkpoint()
                self.assertEqual(caught.exception.reason, 'overall timeout')

    def test_wait_cancels_before_another_poll_and_legacy_wait_unchanged(self):
        control=c.Control(); process=Mock(args=['owned']); calls=[]
        def waiting(timeout):
            calls.append(timeout); control.request(); raise subprocess.TimeoutExpired('owned',timeout)
        process.wait.side_effect=waiting
        with control.active(), self.assertRaises(c.Stopped): c.wait(process,240)
        self.assertEqual(calls,[.1])
        process.wait.side_effect=None; process.wait.return_value=0
        self.assertEqual(c.wait(process,240),0); process.wait.assert_called_with(timeout=240)

    def test_container_cleanup_survives_repeated_stop_requests(self):
        control=c.Control(); process=Mock(args=['docker']); process.poll.return_value=None
        def waiting(timeout):
            if timeout==30: return 0
            control.request(); raise subprocess.TimeoutExpired('docker',timeout)
        process.wait.side_effect=waiting
        def cleanup(*args,**kwargs):
            control.request(); return Mock(returncode=0,stdout=args[0][3].encode(),stderr=b'')
        with control.active(), patch.object(f.subprocess,'Popen',return_value=process), \
             patch.object(f.subprocess,'run',side_effect=cleanup) as remove, self.assertRaises(c.Stopped):
            f._container(['docker','run','--rm','image'],stdout=None,stderr=None)
        process.kill.assert_called_once(); self.assertEqual(remove.call_count,1)
        self.assertEqual(remove.call_args.args[0][:3],['docker','rm','-f'])
        self.assertTrue(remove.call_args.kwargs['start_new_session'])

    def test_unfinished_client_absence_is_not_cleanup_proof(self):
        for code in (0,1):
            control=c.Control();process=Mock(args=['docker']);process.poll.return_value=None
            def waiting(timeout):
                if timeout==30:return 0
                control.request();raise subprocess.TimeoutExpired('docker',timeout)
            process.wait.side_effect=waiting
            absent=Mock(returncode=code,stdout=b'',stderr=b'No such container')
            with control.active(),patch.object(f.subprocess,'Popen',return_value=process), \
                 patch.object(f.subprocess,'run',return_value=absent),self.assertRaises(f.CleanupUncertain):
                f._container(['docker','run','--rm','image'],stdout=None,stderr=None)
        process=Mock();process.poll.return_value=0;process.wait.return_value=0
        with patch.object(f.subprocess,'Popen',return_value=process),patch.object(f.subprocess,'run',return_value=absent):
            self.assertEqual(f._container(['docker','run','--rm','image'],stdout=None,stderr=None),0)

    def test_creation_acknowledgement_allows_auto_removed_container(self):
        for cid,success in ((b'a'*64,True),(b'a'*64+b'\n',True),(b'a'*63,False),(b'x'*64,False),(b'a'*66,False)):
            control=c.Control();process=Mock(args=['docker']);process.poll.return_value=None
            def start(command,**kwargs):
                Path(command[command.index('--cidfile')+1]).write_bytes(cid)
                return process
            def waiting(timeout):
                if timeout==30:return 0
                control.request();raise subprocess.TimeoutExpired('docker',timeout)
            process.wait.side_effect=waiting
            with control.active(),patch.object(f.subprocess,'Popen',side_effect=start), \
                 patch.object(f.subprocess,'run',return_value=Mock(returncode=0,stdout=b'',stderr=b'No such container')):
                with self.assertRaises(c.Stopped if success else f.CleanupUncertain):
                    f._container(['docker','run','--rm','image'],stdout=None,stderr=None)

    def test_uncertain_container_cleanup_overrides_stop(self):
        control=c.Control(); process=Mock(args=['docker']); process.poll.return_value=0
        def waiting(timeout): control.request(); raise subprocess.TimeoutExpired('docker',timeout)
        process.wait.side_effect=waiting
        with control.active(), patch.object(f.subprocess,'Popen',return_value=process), \
             patch.object(f.subprocess,'run',return_value=Mock(returncode=1,stderr=b'daemon unavailable')), \
             self.assertRaises(f.CleanupUncertain):
            f._container(['docker','run','--rm','image'],stdout=None,stderr=None)

    def test_real_owned_probe_timeout_reaps_process(self):
        control=c.Control(.05); original=subprocess.Popen; owned=[]
        def start(*args,**kwargs):
            process=original(*args,**kwargs); owned.append(process); return process
        with control.active(), patch.object(c.subprocess,'Popen',side_effect=start), self.assertRaises(c.Stopped):
            c.version([sys.executable,'-c','import time; time.sleep(30)'])
        self.assertEqual(len(owned),1); self.assertIsNotNone(owned[0].poll())
        self.assertTrue(owned[0].stdout.closed); self.assertTrue(owned[0].stderr.closed)

    def test_probe_failure_and_success_and_legacy_timeout(self):
        with c.Control(5).active():
            self.assertEqual(c.version([sys.executable,'-c','print("version")']),'version\n')
            with self.assertRaises(subprocess.CalledProcessError):
                c.version([sys.executable,'-c','raise SystemExit(7)'])
        with patch.object(c.subprocess,'check_output',return_value='v') as probe:
            self.assertEqual(c.version(['qemu','--version']),'v')
        probe.assert_called_once_with(['qemu','--version'],text=True,timeout=15)

    def test_uart_wait_and_buffered_credit_observe_stop(self):
        control=c.Control(); reader=object.__new__(bridge.Reader)
        reader.deadline=time.monotonic()+90; reader.selector=Mock(); reader.buffer=bytearray(b'>')
        def select(timeout): control.request(); return []
        reader.selector.select.side_effect=select
        with control.active(), self.assertRaises(c.Stopped): reader.chunk()
        self.assertEqual(reader.selector.select.call_count,1)
        with c.Control().active() as other:
            other.request()
            with self.assertRaises(c.Stopped):reader.credit()
        self.assertEqual(reader.buffer,bytearray(b'>'))

    def test_uart_timeout_class_and_process_local_timeout(self):
        reader=object.__new__(bridge.Reader);reader.deadline=0
        with self.assertRaises(TimeoutError):reader.chunk()
        with c.Control().active(),self.assertRaises(c.Stopped) as caught:reader.chunk()
        self.assertEqual(caught.exception.code,124)
        with c.Control().active(),self.assertRaises(c.Stopped) as caught:c.wait(Mock(),0)
        self.assertEqual(caught.exception.code,124)

    def test_probe_and_qemu_cleanup_uncertainty_close_pipes(self):
        process=Mock();process.poll.return_value=None
        process.communicate.side_effect=subprocess.TimeoutExpired('probe',.1)
        process.wait.side_effect=subprocess.TimeoutExpired('probe',2)
        control=c.Control()
        def stop(*args,**kwargs):control.request();return process
        with control.active(),patch.object(c.subprocess,'Popen',side_effect=stop),self.assertRaises(f.CleanupUncertain):
            c.version(['probe'])
        process.stdout.close.assert_called_once();process.stderr.close.assert_called_once()
        process=Mock();process.poll.return_value=None;reader=Mock()
        process.wait.side_effect=[subprocess.TimeoutExpired('qemu',2),0]
        d._cleanup(process,reader);process.terminate.assert_called_once();process.kill.assert_called_once()
        process=Mock();process.poll.return_value=None;reader=Mock()
        process.wait.side_effect=subprocess.TimeoutExpired('qemu',2)
        with self.assertRaises(f.CleanupUncertain):d._cleanup(process,reader)
        process.stdin.close.assert_called_once();process.stdout.close.assert_called_once();reader.close.assert_called_once()

    def test_repeated_real_process_group_interrupt_does_not_kill_cleanup(self):
        code = r"""
import json,os,signal,subprocess,sys
from pathlib import Path
from unittest.mock import patch
from raveil import run_control as c,project_fold as f
root=Path(sys.argv[1]);real_start=subprocess.Popen;real_run=subprocess.run;owned=[]
def start(cmd,**kwargs):
 if cmd[0]=='docker':
  cmd=[sys.executable,'-c',"from pathlib import Path; import time; Path(%r).write_text('ready'); time.sleep(30)" % str(root/'running')]
 proc=real_start(cmd,**kwargs);owned.append(proc);return proc
def remove(cmd,**kwargs):
 code="from pathlib import Path; import time,os; Path(%r).write_text(str(os.getpgrp())); time.sleep(.3); Path(%r).write_text('done')" % (str(root/'cleanup'),str(root/'done'))
 result=real_run([sys.executable,'-c',code],**kwargs)
 result.stdout=(cmd[3]+'\n').encode();return result
control=c.Control()
try:
 with control.active(signals=True),patch.object(f.subprocess,'Popen',side_effect=start),patch.object(f.subprocess,'run',side_effect=remove):
  f._container(['docker','run','--rm','image'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
except c.Stopped as error:
 assert error.code==130
 assert all(proc.poll() is not None for proc in owned)
 assert (root/'done').read_text()=='done'
 assert int((root/'cleanup').read_text())!=os.getpgrp()
 print('cleanup survived repeated process-group interrupts')
else:raise AssertionError('expected stop')
"""
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            process=subprocess.Popen([sys.executable,'-B','-c',code,directory],stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True,start_new_session=True)
            def wait_file(name):
                end=time.monotonic()+10
                while not (root/name).exists():
                    if process.poll() is not None:raise AssertionError(process.communicate())
                    if time.monotonic()>end:raise AssertionError('missing '+name)
                    time.sleep(.01)
            try:
                wait_file('running');os.killpg(process.pid,signal.SIGINT)
                wait_file('cleanup');os.killpg(process.pid,signal.SIGINT);os.killpg(process.pid,signal.SIGINT)
                out,err=process.communicate(timeout=10)
                self.assertEqual(process.returncode,0,err);self.assertIn('cleanup survived',out)
            finally:
                if process.poll() is None:process.kill();process.wait(timeout=2)
                process.stdout.close();process.stderr.close()

    def test_progress_has_no_output_and_commit_prevents_late_cancel(self):
        stream=io.StringIO(); control=c.Control(stream=stream); control.attempt='test'
        with control.active():
            c.event('pass',index=1,total=3); control.committed=True
            control.request(); c.checkpoint()
        event=json.loads(stream.getvalue()); self.assertEqual(event['attempt'],'test')
        self.assertNotIn('outputs',event); self.assertEqual(event['index'],1)


class ArrayControlTests(unittest.TestCase):
    save=fixtures.BatchTests.save
    fake=fixtures.BatchTests.fake
    def setUp(self):
        fixtures.BatchTests.setUp(self)
        self.source=program();self.source['schema']='raveil.array-program/v2'
        (self.project.root/'inputs/program.json').write_bytes(p.encoded(self.source))

    def execute(self,control,callback=None):
        with control.active(), patch.object(d,'run',side_effect=callback or self.fake):
            return a.run(self.project,'program.json',self.kernel,self.build)

    def test_cancel_after_child_and_fresh_retry_preserve_entire_failed_tree(self):
        control=c.Control()
        def first(*args):
            result=self.fake(*args);control.request();return result
        with self.assertRaises(c.Stopped):self.execute(control,first)
        root=self.project.root/'arrays'/control.attempt
        self.assertFalse((root/'record.json').exists());before=p.tree(root)
        retry=self.execute(c.Control());self.assertEqual(retry['status'],'succeeded')
        self.assertNotEqual(retry['id'],control.attempt);self.assertEqual(before,p.tree(root))
        with patch('subprocess.Popen',side_effect=AssertionError('saved read executed')):
            self.assertEqual(sorted(x['status'] for x in a.history(self.project)),['succeeded','unsealed'])

    def test_stop_before_attempt_and_during_final_verification(self):
        control=c.Control();control.request()
        with self.assertRaises(c.Stopped):self.execute(control)
        self.assertNotIn('arrays',self.project.workspace.ls('/'))
        control=c.Control();original=a._inspect
        def inspect(*args):control.request();return original(*args)
        with patch.object(a,'_inspect',side_effect=inspect),self.assertRaises(c.Stopped):self.execute(control)
        self.assertFalse((self.project.root/'arrays'/control.attempt/'record.json').exists())

    def test_last_precommit_checkpoint_and_postcommit_interrupt(self):
        control=c.Control();original=p.write_new
        def pending(path,data,*args,**kwargs):
            result=original(path,data,*args,**kwargs)
            if path.name=='record.sha256' and path.parent.parent.name=='arrays':control.request()
            return result
        with patch.object(p,'write_new',side_effect=pending),self.assertRaises(c.Stopped):self.execute(control)
        self.assertFalse((self.project.root/'arrays'/control.attempt/'record.json').exists())
        control=c.Control();link=os.link
        def committed(src,dst,*args,**kwargs):
            result=link(src,dst,*args,**kwargs)
            if Path(dst).parent.parent.name=='arrays':control.request()
            return result
        with patch.object(a.os,'link',side_effect=committed):record=self.execute(control)
        self.assertTrue(control.committed);self.assertEqual(a.load(self.project,record['id']),record)

    def test_cli_exit_codes_empty_stdout_and_attempt_diagnostics(self):
        argv=['project','array-run','--project',str(self.project.root),'--kernel',str(self.kernel),'--build',str(self.build)]
        for signum,expected in ((signal.SIGINT,130),(signal.SIGTERM,143)):
            def stop(*args):c.current().request(signum);c.checkpoint()
            out,err=io.StringIO(),io.StringIO()
            with patch.object(d,'run',side_effect=stop),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                self.assertEqual(main(argv),expected)
            self.assertEqual(out.getvalue(),'');diagnostic=json.loads(err.getvalue())
            self.assertIsNotNone(diagnostic['attempt']);self.assertIsNone(diagnostic['outputs'])
            self.assertFalse((self.project.root/'arrays'/diagnostic['attempt']/'record.json').exists())
        out,err=io.StringIO(),io.StringIO()
        def expire(*args):c.current().deadline=0;c.checkpoint()
        with patch.object(d,'run',side_effect=expire),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            self.assertEqual(main(argv),124)
        self.assertEqual(json.loads(err.getvalue())['reason'],'overall timeout');self.assertEqual(out.getvalue(),'')

    def test_cli_invalid_timeout_no_attempt_and_progress_only_stderr(self):
        argv=['project','array-run','--project',str(self.project.root),'--kernel',str(self.kernel),'--build',str(self.build)]
        for value in ('nan','inf','0','86401'):
            with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main([*argv,'--timeout-seconds',value]),2)
        self.assertNotIn('arrays',self.project.workspace.ls('/'))
        out,err=io.StringIO(),io.StringIO()
        with patch.object(d,'run',side_effect=self.fake),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            self.assertEqual(main([*argv,'--progress','--summary']),0)
        self.assertEqual(json.loads(out.getvalue())['status'],'succeeded')
        events=[json.loads(line) for line in err.getvalue().splitlines()]
        self.assertEqual(events[0]['event'],'snapshot');self.assertEqual(events[-1]['event'],'verify')
        self.assertTrue(all('outputs' not in event for event in events))

if __name__=='__main__':unittest.main()
