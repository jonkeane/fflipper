import pytest
import os
import tempfile
from pathlib import Path

from fflipper.utils import *

def test_fetch_resource():
    # because we go up two levels, we expected flipper/flipper in this path.
    path_out = fetch_resource(Path(__file__)) / "some" / "path"

    assert "fflipper/fflipper/some/path" in str(path_out)