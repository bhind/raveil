"""Validate functional-only TLRAM endpoint latency diagnostics."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SCHEMA = "raveil.tlram-endpoint-latency-observer/v1"
EVIDENCE_CLASS = "rtl-simulation-functional-diagnostic"
IMPLEMENTATIONS = {
    "rocket-in-order",
    "boom-ooo",
    "boom-ooo-disabled-diagnostic",
}
MARKER = re.compile(
    r"^TLRAM-ENDPOINT-LATENCY-OBSERVER-V1 "
    r"instance=(?P<instance>\S+) "
    r"transactions=(?P<transactions>\d+) "
    r"reads=(?P<reads>\d+) writes=(?P<writes>\d+) other=(?P<other>\d+) "
    r"input_region=(?P<input_region>\d+) output_region=(?P<output_region>\d+) "
    r"other_region=(?P<other_region>\d+) "
    r"min_cycles=(?P<minimum>\d+) max_cycles=(?P<maximum>\d+) "
    r"variable=(?P<variable>[01]) unmatched=(?P<unmatched>\d+) "
    r"source_reuse=(?P<source_reuse>\d+) pending=(?P<pending>\d+) "
    r"evidence=rtl-simulation-functional-diagnostic performance=not-measured "
    r"fixed_latency_claim=0 resource_match_verified=0$"
)


class TlramLatencyObserverError(ValueError):
    """The functional diagnostic is missing, ambiguous, or inconsistent."""


def parse_observer_log(text: str, implementation: str) -> dict[str, object]:
    if implementation not in IMPLEMENTATIONS:
        raise TlramLatencyObserverError("unsupported implementation")
    matches = [match for line in text.splitlines() if (match := MARKER.match(line))]
    if len(matches) != 1:
        raise TlramLatencyObserverError("expected exactly one observer marker")
    values = matches[0].groupdict()
    if not values["instance"].endswith(".raveil_tlram_endpoint_latency_observer"):
        raise TlramLatencyObserverError("observer instance boundary changed")
    numeric = {
        key: int(value)
        for key, value in values.items()
        if key != "instance"
    }
    transactions = numeric["transactions"]
    if transactions <= 0:
        raise TlramLatencyObserverError("observer recorded no completed transactions")
    if transactions != numeric["reads"] + numeric["writes"] + numeric["other"]:
        raise TlramLatencyObserverError("transaction classification is inconsistent")
    if transactions != (
        numeric["input_region"]
        + numeric["output_region"]
        + numeric["other_region"]
    ):
        raise TlramLatencyObserverError("address-region classification is inconsistent")
    if numeric["minimum"] < 1 or numeric["maximum"] < numeric["minimum"]:
        raise TlramLatencyObserverError("observed latency range is invalid")
    if numeric["variable"] != int(numeric["minimum"] != numeric["maximum"]):
        raise TlramLatencyObserverError("latency variability flag is inconsistent")
    for field in ("unmatched", "source_reuse", "pending"):
        if numeric[field] != 0:
            raise TlramLatencyObserverError(f"observer consistency failure: {field}")
    return {
        "schema": SCHEMA,
        "implementation": implementation,
        "observer_boundary": "tlram-single-beat-tilelink-request-to-response",
        "instance": values["instance"],
        "transactions": transactions,
        "reads": numeric["reads"],
        "writes": numeric["writes"],
        "other": numeric["other"],
        "input_region_transactions": numeric["input_region"],
        "output_region_transactions": numeric["output_region"],
        "other_region_transactions": numeric["other_region"],
        "write_path_observed": numeric["writes"] > 0,
        "initiator_and_phase_attribution_available": False,
        "minimum_observed_cycles": numeric["minimum"],
        "maximum_observed_cycles": numeric["maximum"],
        "variable_observed_latency": bool(numeric["variable"]),
        "evidence_class": EVIDENCE_CLASS,
        "performance_claim": False,
        "fixed_latency_claim": False,
        "resource_match_verified": False,
        "matched_comparison_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--implementation", choices=sorted(IMPLEMENTATIONS), required=True)
    args = parser.parse_args()
    observation = parse_observer_log(
        args.log.read_text(encoding="utf-8"), args.implementation
    )
    print(json.dumps(observation, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
