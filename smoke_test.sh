#!/bin/bash
# Basic checks that Cling and HPX are usable inside the image.
set -euo pipefail

echo "== cling =="
command -v cling
cling --help >/dev/null
printf '%s\n' '#include <iostream>' 'std::cout << "hello cling " << __cplusplus << std::endl;' | cling -std=c++20 --nologo | tee /tmp/cling.out
grep -q "hello cling" /tmp/cling.out

echo "== libclingJupyter =="
python3 - <<'PY'
from cling_env import find_libcling_jupyter, cling_install_dir, preload_hpx
print("install", cling_install_dir())
print("lib", find_libcling_jupyter())
print("hpx flags", [x.decode() if isinstance(x, bytes) else x for x in preload_hpx()])
PY

echo "== HPX compile =="
cat > /tmp/hpx_hi.cpp <<'EOF'
#include <hpx/hpx_init.hpp>
#include <hpx/algorithm.hpp>
#include <hpx/execution.hpp>
#include <iostream>
#include <vector>
int hpx_main() {
    std::vector<int> v(8, 1);
    hpx::for_each(hpx::execution::par, v.begin(), v.end(), [](int& x) { x += 1; });
    std::cout << "hpx ok " << v[0] << std::endl;
    return hpx::finalize();
}
int main(int argc, char** argv) { return hpx::init(argc, argv); }
EOF
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig:${PKG_CONFIG_PATH:-}"
if pkg-config --exists hpx_application; then
  PC=hpx_application
elif pkg-config --exists hpx_application_release; then
  PC=hpx_application_release
else
  echo "no hpx pkg-config module" >&2
  exit 1
fi
c++ -std=c++20 /tmp/hpx_hi.cpp $(pkg-config --cflags --libs "$PC") -o /tmp/hpx_hi
/tmp/hpx_hi --hpx:threads=2 | tee /tmp/hpx.out
grep -q "hpx ok 2" /tmp/hpx.out

echo "== python helpers =="
python3 -c 'import cling_env, cin, py11; print("ok")'

echo "ALL OK"
