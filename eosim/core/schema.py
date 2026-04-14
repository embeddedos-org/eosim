# SPDX-License-Identifier: MIT
"""Platform schema validation constants and helpers."""
from typing import List, Dict

VALID_ARCHES = [
    "arm", "arm64", "aarch64", "riscv64", "x86_64",
    "mipsel", "xtensa", "microblaze", "arc", "powerpc",
]

VALID_ENGINES = [
    "renode", "qemu", "eosim", "xplane", "gazebo", "openfoam",
]

VALID_DOMAINS = [
    "automotive", "medical", "industrial", "consumer", "aerospace",
    "iot", "robotics", "defense", "energy", "telecom",
    "aerodynamics", "physiology", "finance", "weather", "gaming",
]

VALID_MODELING = [
    "deterministic", "stochastic", "discrete-event", "continuous",
    "hybrid", "agent-based", "cfd", "monte-carlo",
    "finite-element", "particle-based",
]

VALID_CLASSES = ["mcu", "sbc", "devboard"]


def validate_platform(data: Dict) -> List[str]:
    errors = []

    if "name" not in data or not data.get("name"):
        errors.append("missing required field: name")
    if "arch" not in data or not data.get("arch"):
        errors.append("missing required field: arch")
    if "engine" not in data or not data.get("engine"):
        errors.append("missing required field: engine")

    if data.get("arch") and data["arch"] not in VALID_ARCHES:
        errors.append("invalid arch: %s" % data["arch"])

    if data.get("engine") and data["engine"] not in VALID_ENGINES:
        errors.append("invalid engine: %s" % data["engine"])

    if data.get("class") and data["class"] not in VALID_CLASSES:
        errors.append("invalid class: %s" % data["class"])

    if data.get("domain") and data["domain"] not in VALID_DOMAINS:
        errors.append("invalid domain: %s" % data["domain"])

    if data.get("modeling") and data["modeling"] not in VALID_MODELING:
        errors.append("invalid modeling: %s" % data["modeling"])

    return errors
