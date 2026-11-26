"""Shared pytest setup.

Guard: the test run must never create leo_data/ (the real database folder).
If it did not exist when the run started, it must not exist when it ends.
"""

import pytest

from leo.config import PROJECT_ROOT

LEO_DATA = PROJECT_ROOT / "leo_data"


# Check leo_data/ once around the whole test session.
@pytest.fixture(scope="session", autouse=True)
def leo_data_is_not_created():
    existed_before = LEO_DATA.exists()
    yield
    if not existed_before:
        assert not LEO_DATA.exists(), "the test run created leo_data/"


# Every test starts and ends with tracing off (the do-nothing tracer).
@pytest.fixture(autouse=True)
def tracing_off():
    from leo.ops import tracing

    tracing.set_tracer(tracing.NullTracer())
    tracing.reset_warning()
    yield
    tracing.set_tracer(tracing.NullTracer())
    tracing.reset_warning()


# No background model load (M2.3 fix) may outlive a test.
@pytest.fixture(autouse=True)
def no_background_load():
    from leo.llm import background_load

    yield
    background_load.wait(5)
    background_load._state["thread"] = None
