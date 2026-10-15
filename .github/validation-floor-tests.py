"""Disposable diagnostic for the oldest ordinary-CPython wheel consumer."""
import hashlib
import os
import pathlib
import subprocess
import sys
import tempfile
import venv

assert sys.version_info[:2] == (3, 8), sys.version
checkout = pathlib.Path(__file__).resolve().parents[1]
wheels = list((checkout / "wheelhouse").glob("*.whl"))
assert len(wheels) == 1, wheels
wheel = wheels[0]
assert "-cp38-abi3-" in wheel.name, wheel
print("Floor artifact:", wheel, hashlib.sha256(wheel.read_bytes()).hexdigest(), flush=True)
with tempfile.TemporaryDirectory(prefix="pynacl-python38-") as tmp:
    venv.create(tmp, with_pip=True)
    python = pathlib.Path(tmp) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "cffi==1.17.1", "pytest==8.3.5", "pytest-xdist==3.6.1", "pytest-cov==5.0.0", "hypothesis==6.113.0"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", "--force-reinstall", str(wheel)], check=True)
    subprocess.run([str(python), str(checkout / ".github/validation-wheel-tests.py")], check=True)
