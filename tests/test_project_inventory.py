"""Behavioral and race regressions for bounded project inventories."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from raveil import project as p
from raveil.workspace import WorkspaceError


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base/'source'
        self.root.mkdir()

    def test_exact_manifest_copy_empty_directories_and_binary(self):
        (self.root/'empty').mkdir()
        nested = self.root/'a'/'b'; nested.mkdir(parents=True)
        (nested/'data').write_bytes(b'\0\xff' * 40000)
        (self.root/'z').write_bytes(b'z')
        expected = {'/a': 'directory', '/a/b': 'directory',
                    '/a/b/data': p.digest(b'\0\xff' * 40000),
                    '/empty': 'directory', '/z': p.digest(b'z')}
        copy = self.base/'copy'
        self.assertEqual(p.tree(self.root, copy), expected)
        self.assertEqual(list(p.tree(copy)), list(expected))
        self.assertEqual((copy/'a/b/data').read_bytes(), b'\0\xff' * 40000)
        with self.assertRaises(FileExistsError): p.tree(self.root, copy)

    def test_exact_total_entry_and_byte_limits(self):
        (self.root/'d').mkdir(); (self.root/'d/x').write_bytes(b'ab')
        self.assertEqual(len(p.tree(self.root, max_bytes=2, max_entries=2)), 2)
        for limits in ({'max_bytes': 1}, {'max_entries': 1}):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                p.tree(self.root, **limits)

    def test_directory_limit_counts_excluded_files(self):
        for i in range(256): (self.root/f'{i:03}').touch()
        self.assertEqual(len(p.tree(self.root)), 256)
        (self.root/'record.json').touch()
        with self.assertRaisesRegex(WorkspaceError, '256'):
            p.tree(self.root, exclude_root_files=frozenset({'record.json'}))

    def test_path_byte_limit(self):
        (self.root/'ééé').touch()
        with patch('raveil.workspace.MAX_PATH_BYTES', 6), self.assertRaises(WorkspaceError):
            p.tree(self.root)

    def test_root_only_exclusions_and_invalid_excluded_types(self):
        (self.root/'record.json').write_bytes(b'ignored')
        (self.root/'d').mkdir(); (self.root/'d/record.json').write_bytes(b'x')
        options = dict(exclude_root_files=frozenset({'record.json'}), max_bytes=1)
        self.assertEqual(p.tree(self.root, **options),
                         {'/d': 'directory', '/d/record.json': p.digest(b'x')})
        (self.root/'record.json').unlink(); (self.root/'record.json').mkdir()
        with self.assertRaises(ValueError): p.tree(self.root, **options)

    def test_symlinks_and_fifo_reject(self):
        other = self.base/'other'; other.write_bytes(b'outside')
        for name in ('x', 'record.json'):
            link = self.root/name; link.symlink_to(other)
            with self.assertRaisesRegex(WorkspaceError, 'symlinks'):
                p.tree(self.root, exclude_root_files=frozenset({'record.json'}))
            link.unlink()
        os.mkfifo(self.root/'fifo')
        with self.assertRaises(WorkspaceError): p.tree(self.root)
        link = self.base/'link'; link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(WorkspaceError): p.tree(link)

    def test_file_replacement_between_stat_and_open_rejects(self):
        path = self.root/'data'; path.write_bytes(b'old')
        real = os.open
        def replace(name, flags, *args, **kwargs):
            if name == 'data':
                path.rename(self.root/'old'); path.write_bytes(b'new')
            return real(name, flags, *args, **kwargs)
        with patch.object(p.os, 'open', side_effect=replace), self.assertRaises(WorkspaceError):
            p.tree(self.root)

    def test_symlink_replacement_between_stat_and_open_rejects(self):
        path = self.root/'data'; path.write_bytes(b'old')
        outside = self.base/'outside'; outside.write_bytes(b'secret')
        real = os.open
        def replace(name, flags, *args, **kwargs):
            if name == 'data': path.unlink(); path.symlink_to(outside)
            return real(name, flags, *args, **kwargs)
        with patch.object(p.os, 'open', side_effect=replace), self.assertRaises(OSError):
            p.tree(self.root)

    def test_growth_is_bounded_and_rejected(self):
        path = self.root/'data'; path.write_bytes(b'x')
        real = os.read; requests = []
        def grow(fd, size):
            requests.append(size)
            if len(requests) == 1: path.write_bytes(b'x' * 10000)
            return real(fd, size)
        with patch.object(p.os, 'read', side_effect=grow), self.assertRaises(ValueError):
            p.tree(self.root, max_bytes=4)
        self.assertEqual(requests, [5])

    def test_same_size_content_change_during_read_rejects(self):
        path = self.root/'data'; path.write_bytes(b'old')
        real = os.read; changed = False
        def mutate(fd, size):
            nonlocal changed
            data = real(fd, size)
            if not changed:
                changed = True; path.write_bytes(b'new')
                info = path.stat(); os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns+1000000))
            return data
        with patch.object(p.os, 'read', side_effect=mutate), self.assertRaises(WorkspaceError):
            p.tree(self.root)

    def test_root_and_ancestor_replacement_during_read_reject(self):
        for root_change in (False, True):
            with self.subTest(root_change=root_change):
                root = self.base/str(root_change); (root/'d').mkdir(parents=True)
                (root/'d/data').write_bytes(b'x'); real = os.read; changed = False
                def mutate(fd, size):
                    nonlocal changed
                    data = real(fd, size)
                    if not changed:
                        changed = True; target = root if root_change else root/'d'
                        target.rename(self.base/('moved'+str(root_change))); target.mkdir()
                    return data
                with patch.object(p.os, 'read', side_effect=mutate), self.assertRaises(WorkspaceError):
                    p.tree(root)

    def test_new_directory_entry_during_read_rejects(self):
        (self.root/'data').write_bytes(b'x'); real = os.read
        def mutate(fd, size):
            result = real(fd, size); (self.root/'added').touch(); return result
        with patch.object(p.os, 'read', side_effect=mutate), self.assertRaises(WorkspaceError):
            p.tree(self.root)

    def test_descriptors_closed_on_interrupt_and_read_failure(self):
        (self.root/'d').mkdir(); (self.root/'d/data').write_bytes(b'x')
        real_open, real_close = os.open, os.close
        for failure in (KeyboardInterrupt(), OSError('read failed')):
            opened = set()
            def opening(*args, **kwargs):
                fd = real_open(*args, **kwargs); opened.add(fd); return fd
            def closing(fd):
                opened.remove(fd); return real_close(fd)
            with patch.object(p.os, 'open', side_effect=opening), \
                 patch.object(p.os, 'close', side_effect=closing), \
                 patch.object(p.os, 'read', side_effect=failure), \
                 self.assertRaises(type(failure)):
                p.tree(self.root)
            self.assertEqual(opened, set())

    def test_deep_tree_and_descriptor_exhaustion_fail_closed(self):
        import errno
        nested = self.root
        for _ in range(64):
            nested /= 'd'; nested.mkdir()
        (nested/'data').write_bytes(b'x')
        self.assertEqual(len(p.tree(self.root)), 65)
        real_open, real_close = os.open, os.close
        opened = set()
        def opening(*args, **kwargs):
            if len(opened) == 4: raise OSError(errno.EMFILE, 'descriptor limit')
            fd = real_open(*args, **kwargs); opened.add(fd); return fd
        def closing(fd):
            opened.remove(fd); return real_close(fd)
        with patch.object(p.os, 'open', side_effect=opening), \
             patch.object(p.os, 'close', side_effect=closing), self.assertRaises(OSError):
            p.tree(self.root)
        self.assertEqual(opened, set())

    def test_checkpoint_cancellation_prevents_copy_publication(self):
        (self.root/'data').write_bytes(b'x')
        copy = self.base/'copy'
        with patch.object(p.run_control, 'checkpoint', side_effect=KeyboardInterrupt), \
             self.assertRaises(KeyboardInterrupt): p.tree(self.root, copy)
        self.assertEqual(list(copy.iterdir()), [])


if __name__ == '__main__': unittest.main()
