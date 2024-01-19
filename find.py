import os
libs_to_load = dict()
for root, dirs, files in os.walk("/usr"):
    for name in files:
        if name.endswith(".so"):
            if name not in ["libhpx.so", "libhpxd.so"]:
                continue
            if "hpx" not in dirs:
                continue
            if "hpx-corot" in root:
                continue
            hpx_path = os.path.join(root, name)
            libs_to_load["hpx"] = hpx_path
    for name in files:
        if name.endswith(".so"):
            if name not in ["libboost_system.so",
                            "libboost_filesystem.so",
                            "libboost_program_options.so",
                            "libboost_thread.so"]:
                continue
            libs_to_load[name] = os.path.join(root, name)
for lib in libs_to_load.values():
    print(lib)
