"""
Backwards-compatible test runner script for Match-Link.
Invokes pytest on tests/ directory.
"""

import sys

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "tests"]))
