"""Patch the split output: expose submit_lock from helpers and fix router import."""
import glob
import os

HELPERS = "helpers.py"
patch = "\n\n# 进程内并发锁（与 database._submit_lock 同一实例，保证发奖原子性）\nfrom .database import get_submit_lock\n\nsubmit_lock = get_submit_lock()\n"
with open(HELPERS, "r", encoding="utf-8") as f:
    h = f.read()
if "submit_lock = get_submit_lock()" not in h:
    with open(HELPERS, "a", encoding="utf-8") as f:
        f.write(patch)

old_imp = "from ..database import get_db, get_submit_lock, submit_lock"
new_imp = "from ..database import get_db, get_submit_lock"
for f in glob.glob("routers/*.py"):
    if os.path.basename(f) == "__init__.py":
        continue
    with open(f, "r", encoding="utf-8") as fh:
        s = fh.read()
    if old_imp in s:
        s = s.replace(old_imp, new_imp)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(s)
        print("patched", f)
print("done")
