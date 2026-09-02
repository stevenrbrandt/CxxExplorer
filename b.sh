#!/bin/bash
# Use lscpu, not nproc. OMP_NUM_THREADS=1 makes nproc report 1 CPU.
set -euo pipefail
CPUS=$(lscpu | awk '/^CPU\(s\):/{print $2}')
if [ -z "${CPUS}" ]; then
  echo "could not read CPU count from lscpu" >&2
  exit 1
fi
# Leave a little headroom for the host.
if [ "${CPUS}" -gt 8 ]; then
  CPUS=$((CPUS - 4))
fi
echo "Building with CPUS=${CPUS} (from lscpu)"
docker compose -f docker-compose.build.yml build --build-arg CPUS="${CPUS}" --build-arg BUILD_TYPE=Release "$@"
bash ./r.sh
