#!/usr/bin/env python3
"""Build a reusable MF01 runtime from existing offline tools; never install."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil.project_fold import build
from raveil.project import encoded
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    args=parser.parse_args()
    print(encoded(build(args.directory)).decode(),end="")
