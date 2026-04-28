"""Flow registry: maps flow_type → BaseFlow implementation.

To add a new flow:
  1. Create src/flows/<name>/ with base.py, specialists.py, flow.py
  2. Subclass BaseFlow and set flow_type, description, routing_hints
  3. Add an entry to FLOW_REGISTRY below
  The coordinator, API, and session store need no other changes.
"""

from __future__ import annotations

from src.flows.base import BaseFlow


def _build_registry() -> dict[str, type[BaseFlow]]:
    from src.flows.ercole.flow import ErcoleFlow

    return {
        "ercole": ErcoleFlow,
    }


def get_flow(flow_type: str) -> BaseFlow:
    registry = _build_registry()
    cls = registry.get(flow_type.lower())
    if cls is None:
        raise ValueError(
            f"Unknown flow type: {flow_type!r}. Available: {list(registry)}"
        )
    return cls()


def list_flows() -> list[str]:
    return list(_build_registry())


def get_flow_routing_info() -> list[dict]:
    """Return routing metadata for all registered flows (used by the coordinator)."""
    return [cls.routing_info() for cls in _build_registry().values()]
