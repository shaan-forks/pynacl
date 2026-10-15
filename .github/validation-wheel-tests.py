"""Disposable diagnostic: run all tests against the installed artifact."""
import importlib.metadata
import pathlib
import shutil
import subprocess
import sys
import tempfile

import nacl
import nacl._sodium

checkout = pathlib.Path(__file__).resolve().parents[1]
for module in (nacl, nacl._sodium):
    path = pathlib.Path(module.__file__).resolve()
    print("Installed module:", path, flush=True)
    assert checkout not in path.parents, path
print("Installed wheel:", importlib.metadata.distribution("PyNaCl").read_text("WHEEL"), flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-xdist", "pytest-cov", "hypothesis"], check=True)
subprocess.run([sys.executable, "-m", "pip", "freeze", "--all"], check=True)
with tempfile.TemporaryDirectory(prefix="pynacl-wheel-tests-") as tmp:
    shutil.copytree(checkout / "tests", pathlib.Path(tmp) / "tests")
    subprocess.run([sys.executable, "-m", "pytest", "-n", "2", "--dist=worksteal", "-rs", "tests"], cwd=tmp, check=True)
