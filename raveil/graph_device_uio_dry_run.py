"""Read-only conversion of a verified sealed request into a UIO transport plan."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
from .graph_device_dynamic_sealed import verify
from .graph_device_axi4lite import _aperture, _verify_abis


def plan(bundle: Path, device: str, repository: Path) -> dict:
    match = re.fullmatch(r"/dev/uio(0|[1-9][0-9]{0,8})", device) if isinstance(device, str) else None
    if match is None:
        raise ValueError("UIO dry-run device must be a canonical /dev/uioN path")
    sealed = verify(bundle, repository)
    _verify_abis()
    aperture = _aperture()
    areas = aperture["apertures"]
    # This conversion is deliberately only a relative plan; the checked
    # contract supplies every address value and no transport primitive exists.
    result = {"schema": "raveil.graph-device-uio-dry-run/v1", "graph_id": sealed["manifest"]["graph_id"],
            "seed": sealed["manifest"]["seed"], "device": device, "aperture_bytes": max(int(item["limit"]) for item in areas.values()),
            "execution_namespace": int(areas["execution"]["base"]), "affine_namespace": int(areas["configuration"]["base"]), "program_namespace": int(areas["program"]["base"]),
            "request_sha256": sealed["manifest"]["request_sha256"], "program_sha256": sealed["manifest"]["program_sha256"],
            "affine_sha256": sealed["manifest"]["files"]["affine.bin"]["sha256"], "input_sha256": sealed["manifest"]["files"]["input.bin"]["sha256"],
            "seal_sha256": sealed["seal_sha256"], "device_opened": 0, "mmap": 0, "mmio": 0, "performance": "not-measured"}
    result["evidence_class"] = "host-functional"
    result["non_claims"] = ["no device open", "no mmap", "no MMIO", "performance not measured"]
    result["plan_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    return result
