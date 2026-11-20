"""Test setup.

The first version of this project served Chennai, and most of the older tests are written against the
Chennai pack (ward 115, the CMWSSB charter, and so on). So the tests start on the Chennai pack. Tests for
the Goa pack use the `goa` fixture, which switches to it for one test and then switches back.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "complaint_tools"))

from complaintrouter import common  # noqa: E402

common.set_district("chennai")


@pytest.fixture
def goa():
    """Run one test on the Goa pack (the default for the real portal)."""
    common.set_district("goa")
    try:
        yield
    finally:
        common.set_district("chennai")
