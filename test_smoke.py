import os
import tempfile
from pathlib import Path

tmp = tempfile.TemporaryDirectory()
os.environ["LOCALAPPDATA"] = tmp.name

import footprint_cleaner as fc

s = fc.Store()
rows = s.targets()
assert len(rows) == 6
assert any(r["identifier"] == "LinkedIn" and r["protected"] == 1 for r in rows)
assert any(r["identifier"] == "Gim Tyme / gim.tyme" and r["status"] == "RECOVER" for r in rows)
print("smoke test passed")
