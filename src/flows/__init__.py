"""Flow registry: maps flow_type → BaseFlow implementation."""

from __future__ import annotations

from src.flows.base import BaseFlow


def get_flow(flow_type: str) -> BaseFlow:
    from src.flows.ercole.flow import ErcoleFlow

    FLOW_REGISTRY: dict[str, type[BaseFlow]] = {
        "ercole": ErcoleFlow,
    }

    cls = FLOW_REGISTRY.get(flow_type.lower())
    if cls is None:
        raise ValueError(
            f"Unknown flow type: {flow_type!r}. Available: {list(FLOW_REGISTRY)}"
        )
    return cls()


def list_flows() -> list[str]:
    return ["ercole"]
