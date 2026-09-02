"""Locate Cling, libclingJupyter, and HPX flags for the Jupyter kernel and %%cling."""

from __future__ import print_function

import ctypes
import glob
import os
import shutil


def _which_cling():
    cling_in_path = shutil.which("cling")
    if not cling_in_path:
        raise RuntimeError("Cannot find cling in $PATH. No cling, no fun.")
    try:
        which = os.readlink(cling_in_path)
        which = os.path.join(os.path.dirname(cling_in_path), which)
    except OSError as exc:
        if getattr(exc, "errno", None) == 22 or exc.args[0] == 22:
            which = cling_in_path
        else:
            raise
    return os.path.abspath(which)


def cling_install_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(_which_cling())))


def find_libcling_jupyter():
    prefix = cling_install_dir()
    names = []
    for folder in ("/bin/libclingJupyter.", "/lib/libclingJupyter.",
                   "/lib64/libclingJupyter.", "/libexec/lib/libclingJupyter."):
        for ext in ("so", "dylib", "dll"):
            names.append(prefix + folder + ext)
    names.extend(glob.glob("/usr/local/lib/libclingJupyter.*"))
    names.extend(glob.glob("/usr/lib/libclingJupyter.*"))
    for path in names:
        if os.access(path, os.R_OK):
            return path
    raise RuntimeError(
        "Cannot find libclingJupyter.{so,dylib,dll} under " + prefix)


def _read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as fd:
        return [line.strip() for line in fd if line.strip()]


def preload_hpx():
    """dlopen HPX (and Boost) so Cling can resolve -lhpx. Returns extra argv flags."""
    for jemalloc in (
            "/usr/lib/x86_64-linux-gnu/libjemalloc.so.2",
            "libjemalloc.so.2"):
        try:
            ctypes.CDLL(jemalloc, ctypes.RTLD_GLOBAL)
            break
        except OSError:
            pass
    # HPX parallel algorithms JIT-compile to __atomic_* helpers.
    for atomic in (
            "/usr/lib/x86_64-linux-gnu/libatomic.so.1",
            "libatomic.so.1"):
        try:
            ctypes.CDLL(atomic, ctypes.RTLD_GLOBAL)
            break
        except OSError:
            pass
    hpx_debug = False
    for line in _read_lines("/usr/hpx-libs.txt"):
        if "libhpxd.so" in line:
            hpx_debug = True
        try:
            ctypes.CDLL(line, ctypes.RTLD_GLOBAL)
        except OSError as exc:
            print("warning: could not preload", line, exc)
    extra = [x.encode("utf-8") for x in _read_lines("/usr/hpx-cling-flags.txt")]
    if extra:
        if b"-latomic" not in extra:
            extra.append(b"-latomic")
        return extra
    if hpx_debug:
        return [b"-DHPX_DEBUG", b"-lhpxd"]
    return [b"-lhpx"]
