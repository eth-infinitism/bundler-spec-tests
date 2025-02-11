from dataclasses import dataclass, field
from typing import List, Optional, Dict, TypeAlias


@dataclass
class AltMempoolException:
    role: Optional[str] = field(default=None)
    address: Optional[str] = field(default=None)
    depths: Optional[List[int]] = field(default=None)
    enterOpcode: Optional[List[str]] = field(default=None)
    enterMethodSelector: Optional[str] = field(default=None)


@dataclass
class AltMempoolConfigRule:
    enabled: bool
    exceptions: List[AltMempoolException]


AltMempoolConfig: TypeAlias = Dict[str, Dict[str, AltMempoolConfigRule]]


@dataclass
class AltMempoolCase:
    name: str
    config: AltMempoolConfig
    assert_revert: bool


def alt_mempool_case_id_function(case: AltMempoolCase):
    name = f"{case.name}"
    for mempool_id, rules in case.config.items():
        name += f"<<{mempool_id}:"
        for rule_name, rule_config in rules.items():
            name += f"[{rule_name}/{rule_config.enabled}/{len(rule_config.exceptions)}]"
        name += ">>"
    return name


alt_mempool_cases = [
    AltMempoolCase(
        name="JustTestingCase",
        config={
            "1": {
                "OP-011": AltMempoolConfigRule(True, [AltMempoolException("account")]),
            }
        },
        assert_revert=False,
    )
]
