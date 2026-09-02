#!/usr/bin/env python3
"""Write /usr/hpx-libs.txt and /usr/hpx-cling-flags.txt after HPX is installed."""

import os
import subprocess
import sys

SEARCH_ROOTS = ["/usr/local", "/usr"]
SKIP_DIR_PARTS = {
    "src", "llvm-project", "cling-src", "hpx-src", "build", "share/doc",
    "include",
}
WANTED = [
    "libboost_atomic.so",
    "libboost_context.so",
    "libboost_filesystem.so",
    "libboost_program_options.so",
    "libboost_system.so",
    "libboost_thread.so",
    "libhpx_core.so",
    "libhpx.so",
    "libhpxd.so",
]


def skip_dir(path):
    parts = set(path.split(os.sep))
    return bool(parts & {"llvm-project", "cling-src", "hpx-src", "CMakeFiles"})


def find_libs():
    found = {}
    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, files in os.walk(root):
            if skip_dir(dirpath):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in {
                "src", "CMakeFiles", "share", "include", "doc"}]
            for name in files:
                for wanted in WANTED:
                    if name == wanted or name.startswith(wanted + "."):
                        if wanted not in found:
                            found[wanted] = os.path.join(dirpath, name)
    return found


def pkg_config(*args):
    env = os.environ.copy()
    paths = [
        "/usr/local/lib/pkgconfig",
        "/usr/local/lib64/pkgconfig",
        "/usr/lib/pkgconfig",
        "/usr/lib/x86_64-linux-gnu/pkgconfig",
    ]
    existing = env.get("PKG_CONFIG_PATH", "")
    env["PKG_CONFIG_PATH"] = ":".join(paths + ([existing] if existing else []))
    try:
        out = subprocess.check_output(["pkg-config", *args], env=env, text=True)
        return out.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def main():
    libs = find_libs()
    with open("/usr/hpx-libs.txt", "w") as fd:
        for key in WANTED:
            if key in libs:
                fd.write(libs[key] + "\n")
                print("preload", libs[key])

    cflags = (pkg_config("--cflags", "hpx_application")
              or pkg_config("--cflags", "hpx_application_release"))
    libflags = (pkg_config("--libs", "hpx_application")
                or pkg_config("--libs", "hpx_application_release"))
    skip = {
        "-lhpx_wrap", "-lhpx_init", "-Wl,-wrap=main",
        "/usr/local/lib/libhpx_wrap.a", "/usr/local/lib/libhpx_init.a",
        "/usr/local/lib64/libhpx_wrap.a", "/usr/local/lib64/libhpx_init.a",
    }
    flags = ["-DHPX_APPLICATION_EXPORTS", "-I/usr/local/include"]
    flags += cflags
    flags += ["-L/usr/local/lib", "-L/usr/local/lib64"]
    flags += libflags
    flags += ["-latomic"]
    seen = set()
    with open("/usr/hpx-cling-flags.txt", "w") as fd:
        for flag in flags:
            if flag in skip or flag.endswith("libhpx_wrap.a") or flag.endswith("libhpx_init.a"):
                continue
            if "wrap=main" in flag:
                continue
            if flag not in seen:
                seen.add(flag)
                fd.write(flag + "\n")
    print("Wrote /usr/hpx-libs.txt and /usr/hpx-cling-flags.txt")
    if "libhpx.so" not in libs and "libhpxd.so" not in libs:
        print("warning: libhpx.so not found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
