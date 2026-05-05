"""LangGraph checkpointer backed by PostgreSQL for multi-turn conversation state."""
from __future__ import annotations

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Module-level reference, set during app lifespan
_checkpointer: AsyncPostgresSaver | None = None


def get_checkpointer() -> AsyncPostgresSaver | None:
    return _checkpointer


def set_checkpointer(cp: AsyncPostgresSaver | None) -> None:
    global _checkpointer
    _checkpointer = cp
