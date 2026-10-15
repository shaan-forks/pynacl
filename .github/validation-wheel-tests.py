"""Disposable diagnostic: run all tests against the installed artifact."""

import importlib.metadata
import pathlib
import shutil
import subprocess
import sys
import sysconfig
import tempfile

import nacl._sodium

import nacl


def assert_installed(path, site_roots, source_root):
    assert source_root not in path.parents, path
    assert any(root in path.parents for root in site_roots), path


checkout = pathlib.Path(__file__).resolve().parents[1]
site_roots = {
    pathlib.Path(sysconfig.get_path(name)).resolve()
    for name in ("purelib", "platlib")
}
for module in (nacl, nacl._sodium):
    path = pathlib.Path(module.__file__).resolve()
    print("Installed module:", path, flush=True)
    assert_installed(path, site_roots, checkout / "src")
print(
    "Installed wheel:",
    importlib.metadata.distribution("PyNaCl").read_text("WHEEL"),
    flush=True,
)
subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "pytest",
        "pytest-xdist",
        "pytest-cov",
        "hypothesis",
    ],
    check=True,
)
subprocess.run([sys.executable, "-m", "pip", "freeze", "--all"], check=True)
with tempfile.TemporaryDirectory(prefix="pynacl-wheel-tests-") as tmp:
    shutil.copytree(checkout / "tests", pathlib.Path(tmp) / "tests")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-n",
            "2",
            "--dist=worksteal",
            "-rs",
            "tests",
        ],
        cwd=tmp,
        check=True,
    )
