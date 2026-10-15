"""Disposable artifact-reuse consumer check, without rebuilding PyNaCl."""

import hashlib
import os
import pathlib
import platform
import subprocess
import sys
import sysconfig
import tempfile
import venv

assert sys.version_info[:2] == (3, 15), sys.version
free_threaded = os.environ["EXPECTED_FREE_THREADED"] == "true"
assert bool(sysconfig.get_config_var("Py_GIL_DISABLED")) == free_threaded
assert (
    platform.machine().casefold() == os.environ["EXPECTED_MACHINE"].casefold()
)
print(
    "Consumer:",
    sys.version,
    platform.platform(),
    platform.machine(),
    flush=True,
)
checkout = pathlib.Path(__file__).resolve().parents[1]
wheels = list((checkout / "wheelhouse").glob("*.whl"))
assert len(wheels) == 1, wheels
wheel = wheels[0]
assert ("-cp315-cp315t-" if free_threaded else "-cp38-abi3-") in wheel.name, (
    wheel
)
print(
    "Exact 3.15 artifact:",
    wheel,
    hashlib.sha256(wheel.read_bytes()).hexdigest(),
    flush=True,
)
with tempfile.TemporaryDirectory(prefix="pynacl-artifact315-") as tmp:
    venv.create(tmp, with_pip=True, symlinks=os.name != "nt")
    python = pathlib.Path(tmp) / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "cffi==2.1.1",
            "pytest==9.1.1",
            "pytest-xdist==3.8.0",
            "pytest-cov==7.1.0",
            "hypothesis==6.169.4",
        ],
        check=True,
    )
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            str(wheel),
        ],
        check=True,
    )
    check_mode = """
import os, platform, subprocess, sys, sysconfig
expected = os.environ['EXPECTED_FREE_THREADED'] == 'true'
assert sys.version_info[:2] == (3, 15), sys.version
assert bool(sysconfig.get_config_var('Py_GIL_DISABLED')) == expected
assert platform.machine().casefold() == os.environ['EXPECTED_MACHINE'].casefold()
import nacl._sodium
assert sys._is_gil_enabled() == (not expected)
print('Imported extension:', nacl._sodium.__file__, 'GIL:', sys._is_gil_enabled(), flush=True)
if sys.platform == 'darwin':
    slices = subprocess.check_output(['lipo', '-archs', nacl._sodium.__file__], text=True).split()
    print('Mach-O slices:', slices, flush=True)
    assert set(slices) == {'arm64', 'x86_64'}, slices
"""
    subprocess.run([str(python), "-c", check_mode], cwd=tmp, check=True)
    subprocess.run([str(python), "-m", "pip", "check"], check=True)
    subprocess.run(
        [str(python), str(checkout / ".github/validation-wheel-tests.py")],
        check=True,
    )
