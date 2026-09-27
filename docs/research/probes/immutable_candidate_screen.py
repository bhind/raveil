#!/usr/bin/env python3
"""T-0202 prospective structural screen and known-CSE witness. No timing/search."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import platform
import struct

import pythia_affine_reference as ref
from pythia_compiler_controls import source_arrays, f32_bytes

PRIMES = (65521, 65519)


def digest(raw):
    return sha256(raw).hexdigest()


def prime(p):
    return p >= 2 and all(p % k for k in range(2, int(p**0.5)+1))


def modular_rank(rows, p):
    ref.require(prime(p), 'prime field required')
    ref.require(rows and rows[0] and all(len(r) == len(rows[0]) for r in rows), 'matrix shape')
    a = [[v % p for v in row] for row in rows]
    rank = 0
    for col in range(len(a[0])):
        pivot = next((i for i in range(rank, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, p)
        a[rank] = [(v * inv) % p for v in a[rank]]
        for i in range(rank+1, len(a)):
            factor = a[i][col]
            if factor:
                a[i] = [(x-factor*y) % p for x,y in zip(a[i],a[rank])]
        rank += 1
        if rank == len(a):
            break
    return rank


def hadamard(values):
    n = len(values)
    ref.require(n > 0 and n & (n-1) == 0, 'power-of-two size required')
    result = list(values)
    width = 1
    while width < n:
        for start in range(0,n,2*width):
            for j in range(width):
                a,b = result[start+j],result[start+j+width]
                result[start+j],result[start+j+width] = a+b,a-b
        width *= 2
    return result


def odd_part(integer):
    value = abs(integer)
    return value // (value & -value) if value else 0


def dictionary_plan(raw, rows, columns):
    ref.require(len(raw) == rows * columns * 2, 'dictionary source shape')
    bits = [v[0] for v in struct.iter_unpack('<H', raw)]
    for bit in bits:
        ref.half_integer(bit)
    dictionaries, indices = [], []
    for col in range(columns):
        values, lookup, ids = [], {}, []
        for row in range(rows):
            bit = bits[row*columns+col]
            if bit not in lookup:
                lookup[bit] = len(values)
                values.append(bit)
            ids.append(lookup[bit])
        dictionaries.append(values)
        indices.append(ids)
    return dictionaries, indices


def shared_products(plan, bias, inputs):
    dictionaries, indices = plan
    ref.require(len(inputs) == len(dictionaries) == len(indices), 'shared input shape')
    output = list(bias)
    mults = 0
    for x, values, ids in zip(inputs, dictionaries, indices):
        ref.require(len(ids) == len(bias), 'shared row shape')
        coeffs = [struct.unpack('<e', struct.pack('<H', b))[0] for b in values]
        products = [ref.f32(c*x) for c in coeffs]
        mults += len(products)
        for r, index in enumerate(ids):
            output[r] = ref.f32(output[r]+products[index])
    return output, mults


def run(source):
    (wf, wi),(bf,bi) = source_arrays(source)
    # Build from the verified values, preserving binary16 sign bits including zero.
    raw = struct.pack('<'+str(len(wf))+'e', *wf)
    plan = dictionary_plan(raw, ref.ROWS, ref.COLS)
    dictionaries, indices = plan
    counts = [len(c) for c in dictionaries]
    rows = [wi[r*ref.COLS:(r+1)*ref.COLS] for r in range(ref.ROWS)]
    bits = [v[0] for v in struct.iter_unpack('<H',raw)]
    rank = {str(p): modular_rank(rows,p) for p in PRIMES}
    forms = []
    for j in range(0,ref.COLS,2):
        pairs = Counter((rows[r][j], rows[r][j+1]) for r in range(ref.ROWS))
        forms.append(ref.ROWS-len(pairs))
    transformed = [hadamard(row) for row in rows]
    bad_f32 = 0
    for row in transformed:
        for value in row:
            rounded = ref.f32(value/(1 << 31))  # W*H/128, source scale 2^-24.
            numerator,denominator = rounded.as_integer_ratio()
            bad_f32 += numerator * (1 << 31) != value * denominator
    cases = []
    for name, input_raw, (xf,xi) in ref.inputs():
        exact,scales = ref.oracle(wi,bi,xi)
        actual,mults = shared_products(plan,bf,xf)
        repeated,_ = shared_products(plan,bf,xf)
        serial = ref.serial(wf,bf,xf)
        for outputs in (actual,repeated,serial):
            ref.validate(outputs,exact,scales)
        ref.require(f32_bytes(actual) == f32_bytes(serial) == f32_bytes(repeated), 'CSE changed serial result')
        ref.require(mults == sum(counts), 'product accounting mismatch')
        cases.append({'input':name,'input_sha256':digest(input_raw),'output_sha256':digest(f32_bytes(actual))})
    abs_unique = sum(len({abs(rows[r][j]) for r in range(ref.ROWS)}) for j in range(ref.COLS))
    odd_unique = sum(len({odd_part(rows[r][j]) for r in range(ref.ROWS)}) for j in range(ref.COLS))
    total = ref.ROWS*ref.COLS
    # Explicit hypothetical packed format; Python objects are not this format.
    packed = {'dictionary_f32_bytes':4*sum(counts), 'local_u16_id_bytes':2*total,
              'column_u32_offset_bytes':4*(ref.COLS+1), 'bias_f32_bytes':4*ref.ROWS}
    offsets, offset = [0],0
    for n in counts:
        offset += n
        offsets.append(offset)
    identity = b''.join(struct.pack('<H',v) for c in dictionaries for v in c)
    identity += b''.join(struct.pack('<H',v) for c in indices for v in c)
    identity += struct.pack('<129I',*offsets)
    da = []
    for group in (4,8):
        table_entries = ref.ROWS*(ref.COLS//group)*(1 << group)
        # Generic finite-F16 coefficient grid: 41 signed bits; group sums need more.
        sum_bits = 41 + (group.bit_length()-1)
        entry_bytes = (sum_bits+7)//8
        da.append({'group':group,'table_entries':table_entries,'generic_signed_entry_bits':sum_bits,
                   'packed_table_bytes':table_entries*entry_bytes,
                   'unoptimized_29_bitplane_lookups':29*ref.ROWS*(ref.COLS//group)})
    return {'schema':'raveil.immutable-candidate-screen/v1','task':'T-0202',
            'evidence_class':'host-functional and analytical',
            'environment':{'python':platform.python_version(),'platform':platform.platform()},
            'probe_sha256':digest(Path(__file__).read_bytes()),
            'reference_sha256':digest(Path(ref.__file__).read_bytes()),
            'plan_sha256':digest((Path(__file__).parent.parent/'reviews/T-0202-screen-plan.md').read_bytes()),
            'source_revision':ref.REVISION,'source_sha256':{k:v[1] for k,v in ref.FILES.items()},
            'shape':[ref.ROWS,ref.COLS],'coefficient_uses':total,
            'zero_coefficients':sum(v==0 for v in wi),
            'duplicate_rows':ref.ROWS-len(set(map(tuple,rows))),
            'dictionary':{'products_per_call':sum(counts),'products_saved':total-sum(counts),
                          'adds_per_call':total,'indexed_product_uses_per_call':total,
                          'column_counts':counts,'plan_sha256':digest(identity),
                          'packed_format':packed,'packed_total_bytes':sum(packed.values()),
                          'baseline_widened_w_b_bytes':264192,
                          'max_column_product_scratch_bytes':4*max(counts),
                          'product_scratch_stores_per_call':sum(counts),
                          'u16_id_and_product_reads_per_call':total,
                          'implemented_as':'Python functional witness, not packed/native optimized runtime'},
            'factoring_counts':{'absolute_unique_per_column_total':abs_unique,
                                'odd_significand_unique_per_column_total':odd_unique,
                                'negative_uses':sum(v<0 for v in wi),
                                'nonzero_uses':sum(v!=0 for v in wi),
                                'nontrivial_power_of_two_scale_uses':sum(
                                    (abs(v)&-abs(v)).bit_length()-1 != 24 for v in wi if v)},
            'adjacent_pairs':{'repeated_occurrences':sum(forms),'per_pair':forms,
                              'search_scope':'only disjoint adjacent columns; no exhaustive CSE claim'},
            'rank_mod_primes':rank,'exact_rank_lower_bound':max(rank.values()),
            'dense_rank_factor_multiplies_at_128':(ref.ROWS+ref.COLS)*128,
            'hadamard':{'transform_additions':896,'transformed_zeros':sum(v==0 for row in transformed for v in row),
                        'coefficients_not_exact_f32':bad_f32,'search_scope':'one preselected H basis only'},
            'distributed_arithmetic':{'exact_input_grid_signed_bits':29,'generic_exact_accumulator_signed_bits':76,
                                      'unpartitioned_entries_per_row':str(1 << ref.COLS),'partition_examples':da},
            'functional_inputs':len(cases),'validated_components':len(cases)*ref.ROWS*3,
            'bitwise_equal_to_serial':True,'cases':cases,'timing_measured':False,
            'holdouts_evaluated':False,'novel_mechanism_selected':False,'hardware_advantage_established':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.source_dir),indent=2,sort_keys=True))
