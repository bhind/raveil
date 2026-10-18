#!/usr/bin/env python3
"""Read one saved array with the selected engine; prohibit execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.engine.resolve()))
    from raveil import project as p, project_array as a
    with patch('subprocess.Popen', side_effect=AssertionError('saved inspection executed')):
        record = a.load(p.Project(args.workspace), args.identity)
    print(json.dumps(dict(id=record['id'], status=record['status'],
                          record_sha256=hashlib.sha256(p.encoded(record)).hexdigest())))


if __name__ == '__main__': main()
