#!/usr/bin/env python3
"""T-0201 offline compiler controls; private artifacts, no timing or downloads."""
import argparse
from collections import Counter
import ctypes
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import struct
import subprocess

import pythia_affine_reference as ref

FLAGS = ['-std=c11', '-O3', '-fno-fast-math', '-ffp-contract=off', '-fPIC']
MODES = ('serial', 'fma4')


def digest(data):
    return sha256(data).hexdigest()


def source_arrays(source):
    arrays = []
    for name, (length, expected) in ref.FILES.items():
        raw = (source / name).read_bytes()
        ref.require(len(raw) == length, 'source byte length mismatch')
        ref.require(digest(raw) == expected, 'source SHA-256 mismatch')
        arrays.append(ref.decode(raw))
    return arrays


def f32_bytes(values):
    return struct.pack('<' + str(len(values)) + 'f', *values)


def generate(weights, bias, fixed, mode):
    ref.require(mode in MODES, 'unknown reduction mode')
    ref.require(len(weights) == ref.ROWS * ref.COLS and len(bias) == ref.ROWS, 'parameter shape')
    preamble = '#include <fenv.h>\n#include <stddef.h>\n'
    if fixed:
        # Every literal exactly describes the widened source binary16 value.
        for name, values in (('W', weights), ('B', bias)):
            preamble += 'static const float ' + name + '[] = {\n'
            preamble += ',\n'.join(','.join(v.hex() + 'f' for v in values[i:i+8])
                                  for i in range(0, len(values), 8)) + '\n};\n'
    signature = 'void affine(const float *restrict w, const float *restrict b, const float *restrict x, float *restrict y)'
    body = '\n  for (int r=0; r<512; ++r) {\n'
    if mode == 'serial':
        body += '    float s=b[r];\n    for (int j=0; j<128; ++j) s=s+w[r*128+j]*x[j];\n    y[r]=s;\n'
    else:
        body += '    float s0=0, s1=0, s2=0, s3=0;\n    for (int j=0; j<128; j+=4) {\n'
        for k in range(4):
            body += f'      s{k}=__builtin_fmaf(w[r*128+j+{k}],x[j+{k}],s{k});\n'
        body += '    }\n    y[r]=((s0+s1)+(s2+s3))+b[r];\n'
    body += '  }\n'
    if fixed:
        body = body.replace('w[', 'W[').replace('b[', 'B[')
    result = preamble + signature + ' {' + body + '}\n'
    result += 'int nearest(void) { return fegetround()==FE_TONEAREST; }\n'
    return result


def object_sections(raw):
    """Read Mach-O64 little-endian section sizes/relocations, not resident cost."""
    ref.require(len(raw) >= 32 and struct.unpack_from('<I', raw)[0] == 0xfeedfacf, 'expected Mach-O64 object')
    ncmds = struct.unpack_from('<I', raw, 16)[0]
    cursor, sections = 32, []
    for _ in range(ncmds):
        cmd, size = struct.unpack_from('<II', raw, cursor)
        ref.require(size >= 8 and cursor + size <= len(raw), 'malformed load command')
        if cmd == 0x19:
            count = struct.unpack_from('<I', raw, cursor + 64)[0]
            ref.require(size >= 72 + 80 * count, 'malformed section table')
            for index in range(count):
                at = cursor + 72 + 80 * index
                name = raw[at:at+16].split(b'\0')[0].decode('ascii')
                segment = raw[at+16:at+32].split(b'\0')[0].decode('ascii')
                section_size = struct.unpack_from('<Q', raw, at+40)[0]
                relocations = struct.unpack_from('<I', raw, at+60)[0]
                sections.append({'segment': segment, 'section': name,
                                 'bytes': section_size, 'file_offset': struct.unpack_from('<I', raw, at+48)[0],
                                 'relocations': relocations})
        cursor += size
    return sections


def kernel_assembly(assembly):
    body = assembly.split('_affine:', 1)[1].split('.cfi_endproc', 1)[0]
    instructions = []
    for line in body.splitlines():
        match = re.fullmatch(r'([a-z][a-z0-9.]*)(?:\s+(.*))?', line.split('//', 1)[0].strip())
        if match:
            instructions.append((match.group(1) + ' ' + (match.group(2) or '')).strip())
    ref.require(bool(instructions), 'missing kernel instructions')
    return {'static_instruction_histogram': dict(sorted(Counter(x.split()[0] for x in instructions).items())),
            'static_instruction_count': len(instructions),
            'normalized_kernel_sha256': digest('\n'.join(instructions).encode())}


def command(args, cwd, log):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    log.append({'argv': args, 'exit_code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr})
    (cwd/'commands.json').write_text(json.dumps(log, indent=2)+'\n')
    ref.require(result.returncode == 0, 'compiler/tool failed; retained commands.json')
    return result.stdout


def run(source, output):
    # Verify all private inputs before creating any generated source or invoking clang.
    (wf, wi), (bf, bi) = source_arrays(source)
    ref.require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'requires Darwin arm64')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)  # Never replace prior evidence.
    log = []
    compiler = command(['xcrun', '--find', 'clang'], output, log).strip()
    version = command([compiler, '--version'], output, log).strip()
    sdk = command(['xcrun', '--show-sdk-path'], output, log).strip()
    build_flags = [*FLAGS, '-isysroot', sdk]
    cf = ctypes.c_float
    ptr = ctypes.POINTER(cf)
    w, b = (cf * len(wf))(*wf), (cf * len(bf))(*bf)
    vectors = list(ref.inputs())
    blas = ref.blas_control(wf, bf)
    oracle_cases = []
    for name, raw, (xf, xi) in vectors:
        exact, scales = ref.oracle(wi, bi, xi)
        baseline = blas(xf)
        ref.validate(baseline, exact, scales)
        oracle_cases.append((name, raw, xf, exact, scales, baseline))
    variants = []
    for mode in MODES:
        for fixed in (False, True):
            name = ('fixed' if fixed else 'runtime') + '-' + mode
            code = generate(wf, bf, fixed, mode)
            (output/(name+'.c')).write_text(code)
            command([compiler, *build_flags, '-c', name+'.c', '-o', name+'.o'], output, log)
            command([compiler, *build_flags, '-S', name+'.c', '-o', name+'.s'], output, log)
            command([compiler, '-isysroot', sdk, '-dynamiclib', name+'.o', '-o', name+'.dylib'], output, log)
            lib = ctypes.CDLL(str(output/(name+'.dylib')))
            lib.nearest.restype = ctypes.c_int
            ref.require(lib.nearest() == 1, 'FE_TONEAREST required')
            sections = object_sections((output/(name+'.o')).read_bytes())
            if fixed:
                obj = (output/(name+'.o')).read_bytes()
                constants = b''.join(obj[s['file_offset']:s['file_offset']+s['bytes']]
                                     for s in sections if s['section'] == '__const')
                # Inspect compiler output without exported getters that would force
                # otherwise unused constants to survive in the measured object.
                ref.require(f32_bytes(wf) in constants and f32_bytes(bf) in constants,
                            'compiled parameter identity mismatch')
            lib.affine.argtypes = [ptr, ptr, ptr, ptr]
            lib.affine.restype = None
            cases = []
            for label, raw, xf, exact, scales, baseline in oracle_cases:
                x = (cf * ref.COLS)(*xf)
                results = []
                for poison in (float('nan'), 123.0):
                    y = (cf * ref.ROWS)(*([poison]*ref.ROWS))
                    lib.affine(w, b, x, y)
                    values = list(y)
                    ref.validate(values, exact, scales)
                    results.append(f32_bytes(values))
                ref.require(results[0] == results[1], 'fresh output overwrite mismatch')
                cases.append({'input': label, 'input_sha256': digest(raw), 'output_sha256': digest(results[0]),
                              'bitwise_equal_to_accelerate': results[0] == f32_bytes(baseline)})
            files = {suffix: {'bytes': (output/(name+suffix)).stat().st_size,
                             'sha256': digest((output/(name+suffix)).read_bytes())}
                     for suffix in ('.c', '.o', '.s', '.dylib')}
            variants.append({'name': name, 'compiled_parameter_identity_checked': fixed,
                             'FE_TONEAREST': True, 'cases': cases, 'files': files,
                             'object_sections': sections,
                             **kernel_assembly((output/(name+'.s')).read_text())})
    for mode in MODES:
        pair = [v for v in variants if v['name'].endswith('-'+mode)]
        ref.require(pair[0]['cases'] == pair[1]['cases'], 'runtime/fixed pair output mismatch')
    result = {'schema': 'raveil.compiler-controls/v1', 'task': 'T-0201', 'evidence_class': 'host-functional',
              'compiler_version': version, 'compiler_sha256': digest(Path(compiler).read_bytes()),
              'flags': build_flags, 'sdk': sdk, 'link_flags': ['-dynamiclib'],
              'environment': {'platform': platform.platform(), 'python': platform.python_version()},
              'probe_sha256': digest(Path(__file__).read_bytes()),
              'reference_sha256': digest(Path(ref.__file__).read_bytes()),
              'source_revision': ref.REVISION, 'source_sha256': {k: v[1] for k,v in ref.FILES.items()},
              'widened_parameters_sha256': digest(f32_bytes(wf)+f32_bytes(bf)),
              'source_parameter_bytes': 132096, 'widened_parameter_bytes': 264192,
              'input_bytes': 512, 'output_bytes': 2048, 'c_bias_copy_bytes': 0,
              'accelerate_bias_copy_bytes': 2048,
              'gamma': [ref.GAMMA_N, ref.GAMMA_D], 'variants': variants,
              'functional_inputs': len(vectors), 'c_component_checks': 4*2*8*512,
              'accelerate_component_checks': 8*512,
              'pair_bitwise_equal': True, 'fresh_output_overwrite_checked': True,
              'timing_measured': False, 'holdouts_evaluated': False, 'novel_mechanism': False,
              'exhaustive_compiler_search': False, 'hardware_advantage_established': False}
    (output/'receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.source_dir, args.output_dir), indent=2, sort_keys=True))
