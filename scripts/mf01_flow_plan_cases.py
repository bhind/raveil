"""Owned partition-rescue and aggregate-infeasibility cases."""
from raveil.mf01_flow import SCHEMA
from scripts.mf01_grid_affine_cases import matmul
from scripts.mf01_flow_cases import product


def rescue():
    first,ab=matmul(3,50,8,(1,1));second,_=matmul(3,9,50,(1,1));second['inputs'][0]={'from':'first'}
    expected=product(ab,second['inputs'][1]['words'],3,9,50)
    return dict(schema=SCHEMA,stages=[dict(name='second',source=second),dict(name='first',source=first)],outputs=['second']),expected


def impossible():
    first,_=matmul(17,19,64);second,_=matmul(17,1,19);second['inputs'][0]={'from':'first'}
    return dict(schema=SCHEMA,stages=[dict(name='first',source=first),dict(name='second',source=second)],outputs=['second'])
