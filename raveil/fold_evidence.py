"""Strict JSON and structural equality for integer-only MF01 evidence.

This validates representation, not provenance: transcript and executable checks
remain the responsibility of each verifier. Object field order is immaterial.
"""
import json


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate evidence field: {key}")
        result[key] = value
    return result


def _noninteger(token):
    raise ValueError(f"noninteger number in MF01 evidence: {token}")


def loads(text):
    """Reject duplicate fields, floating-point spellings and non-JSON numbers."""
    return json.loads(text, object_pairs_hook=_object,
                      parse_float=_noninteger, parse_constant=_noninteger)


def same(actual, expected):
    """Compare JSON trees without Python's bool/int/float coercion."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (all(type(key) is str for key in actual) and
                actual.keys() == expected.keys() and
                all(same(actual[key], value) for key, value in expected.items()))
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            same(a, b) for a, b in zip(actual, expected))
    return type(expected) in (str, int, bool, type(None)) and actual == expected
