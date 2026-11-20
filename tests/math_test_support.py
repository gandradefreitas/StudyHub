"""Shared helpers for the migrated mathematical characterization tests."""

from __future__ import annotations

from typing import Any

ACTUAL_RESULTS: dict[str, str] = {}


def record_actual(name: str, value: Any) -> None:
    """Keep a stable representation for the old/new parity audit."""
    ACTUAL_RESULTS[name] = repr(value)


def assert_legacy_equal(name: str, actual: Any, expected: Any) -> None:
    record_actual(name, actual)
    if isinstance(expected, bool) or expected is None:
        assert actual is expected
    else:
        assert actual == expected


def assert_legacy_error(name: str, call) -> None:
    try:
        call()
    except (ValueError, SyntaxError) as error:
        record_actual(name, f"raises:{type(error).__name__}")
        return
    except Exception as error:  # preserve the old helper's exception policy
        record_actual(name, f"unexpected:{type(error).__name__}")
        raise AssertionError(
            f"{name}: exceção inesperada {type(error).__name__}: {error}"
        ) from error
    record_actual(name, "did_not_raise")
    raise AssertionError(f"{name}: deveria ter sido rejeitada")
