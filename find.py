#!/usr/bin/env python3
"""Backward-compatible wrapper: print shared libraries Cling should preload."""
import gen_hpx_cling_config

libs = gen_hpx_cling_config.find_libs()
for key in gen_hpx_cling_config.WANTED:
    if key in libs:
        print(libs[key])
