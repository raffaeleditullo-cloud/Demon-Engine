import pytest
from demon_engine import DemonEngine

@pytest.fixture
def engine():
    """Fixture providing a configured DemonEngine instance for scenario tests."""
    return DemonEngine(phase_damping=1.25, antipattern_penalty=0.85)
