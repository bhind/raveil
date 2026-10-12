#!/usr/bin/env python3
"""Actual bounded-range QEMU/RTL acceptance using existing offline tools."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.fold_dag_acceptance import main
from scripts.fold_dag_range_cases import scenarios,rejected_graphs,raw_encode
if __name__=='__main__':main(cases=scenarios,rejections=rejected_graphs,encoder=raw_encode)
