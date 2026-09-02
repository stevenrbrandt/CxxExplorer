# C++Explorer — Ubuntu 24.04, Cling 1.3 (LLVM 20), HPX 1.11
#
# Build (use lscpu, not nproc — OMP_NUM_THREADS=1 makes nproc report 1):
#   CPUS=$(lscpu | awk '/^CPU\(s\):/{print $2}')
#   docker compose -f docker-compose.build.yml build --build-arg CPUS=$CPUS
#
# Pins:
#   Cling v1.3 + llvm-project tag cling-llvm20-20260119-01 (same pair Homebrew uses)
#   HPX v1.11.0

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/usr/local/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64 \
    PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig \
    PYTHONPATH=/usr/local/python

ARG CPUS=8
ARG BUILD_TYPE=Release

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git patch \
        build-essential g++ gcc cmake ninja-build pkg-config \
        python3 python3-dev python3-pip python3-venv python3-setuptools \
        libpython3-dev \
        libhwloc-dev libjemalloc-dev libasio-dev \
        libboost-all-dev \
        libblas-dev liblapack-dev libtbb-dev \
        libxml2-dev libedit-dev zlib1g-dev libzstd-dev libssl-dev \
        libncurses-dev \
        libsqlite3-dev sqlite3 \
        nodejs npm \
        vim gdb \
        imagemagick file hostname psmisc \
        pybind11-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Cling 1.3 on the cling-patched LLVM 20 tree
# ---------------------------------------------------------------------------
WORKDIR /opt
RUN git clone --depth 1 --branch cling-llvm20-20260119-01 \
        https://github.com/root-project/llvm-project.git llvm-project \
    && git clone --depth 1 --branch v1.3 \
        https://github.com/root-project/cling.git cling-src

COPY Pipe.hpp Augment_Kernel.hpp /usr/local/include/
COPY Kernel.cpp /opt/cling-src/tools/Jupyter/Kernel.cpp

WORKDIR /opt/cling-build
RUN cmake -G Ninja \
        -S /opt/llvm-project/llvm \
        -B /opt/cling-build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_CXX_FLAGS="-I/usr/local/include" \
        -DCLING_CXX_PATH=/usr/bin/c++ \
        -DLLVM_ENABLE_PROJECTS=clang \
        -DLLVM_EXTERNAL_PROJECTS=cling \
        -DLLVM_EXTERNAL_CLING_SOURCE_DIR=/opt/cling-src \
        -DLLVM_TARGETS_TO_BUILD=host \
        -DLLVM_BUILD_TOOLS=OFF \
        -DLLVM_INCLUDE_BENCHMARKS=OFF \
        -DLLVM_INCLUDE_TESTS=OFF \
        -DCLING_INCLUDE_TESTS=ON \
        -DLLVM_ENABLE_RTTI=ON \
        -DLLVM_ENABLE_EH=ON \
        -DLLVM_ENABLE_ASSERTIONS=OFF \
        -DLLVM_PARALLEL_LINK_JOBS=8 \
    && ninja -j ${CPUS} \
    && ninja -j ${CPUS} install \
    && mkdir -p /usr/local/share/cling /usr/local/lib \
    && cp -a /opt/cling-src/tools/Jupyter /usr/local/share/cling/ \
    && so=$(find /opt/cling-build /usr/local -name 'libclingJupyter.so' | head -1) \
    && test -n "$so" \
    && cp -a "$so" /usr/local/lib/ \
    && rm -rf /opt/cling-build /opt/llvm-project /opt/cling-src

# Cling bakes the build-tree resource dir into the binary. Point it at the install.
RUN mkdir -p /opt/cling-build/lib \
    && ln -sfn /usr/local/lib/clang /opt/cling-build/lib/clang

# ---------------------------------------------------------------------------
# HPX 1.11
# ---------------------------------------------------------------------------
WORKDIR /opt
RUN git clone --depth 1 --branch v1.11.0 https://github.com/STEllAR-GROUP/hpx.git hpx-src \
    && cmake -G Ninja \
        -S /opt/hpx-src \
        -B /opt/hpx-build \
        -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DHPX_WITH_CXX_STANDARD=20 \
        -DHPX_WITH_MALLOC=jemalloc \
        -DHPX_WITH_EXAMPLES=OFF \
        -DHPX_WITH_TESTS=OFF \
        -DHPX_WITH_TOOLS=OFF \
        -DHPX_WITH_DOCUMENTATION=OFF \
        -DHPX_WITH_MORE_THAN_64_THREADS=ON \
        -DHPX_WITH_MAX_CPU_COUNT=128 \
    && ninja -C /opt/hpx-build -j ${CPUS} install \
    && rm -rf /opt/hpx-build /opt/hpx-src \
    && ldconfig /usr/local/lib /usr/local/lib64

# ---------------------------------------------------------------------------
# Blaze (header-only math). blaze_tensor / BlazeIterative are best-effort.
# ---------------------------------------------------------------------------
WORKDIR /opt
RUN (git clone --depth 1 https://bitbucket.org/blaze-lib/blaze.git blaze \
        || git clone --depth 1 https://github.com/CodeAtelier/Blaze.git blaze) \
    && cmake -S /opt/blaze -B /opt/blaze/build -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
    && cmake --build /opt/blaze/build -j ${CPUS} --target install \
    && rm -rf /opt/blaze \
    && (git clone --depth 1 https://github.com/STEllAR-GROUP/blaze_tensor.git blaze_tensor \
        && cmake -S /opt/blaze_tensor -B /opt/blaze_tensor/build -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
        && cmake --build /opt/blaze_tensor/build -j ${CPUS} --target install \
        && rm -rf /opt/blaze_tensor || echo "blaze_tensor skipped") \
    && (git clone --depth 1 https://github.com/STEllAR-GROUP/BlazeIterative.git BlazeIterative \
        && cmake -S /opt/BlazeIterative -B /opt/BlazeIterative/build \
        && cmake --build /opt/BlazeIterative/build -j ${CPUS} --target install \
        && rm -rf /opt/BlazeIterative || echo "BlazeIterative skipped")

COPY ./run_hpx.cpp /usr/include/run_hpx.cpp
COPY ./teleplot.hpp /usr/include/teleplot.hpp
RUN chmod 644 /usr/include/run_hpx.cpp /usr/include/teleplot.hpp

COPY gen_hpx_cling_config.py /usr/local/python/gen_hpx_cling_config.py
RUN python3 /usr/local/python/gen_hpx_cling_config.py && ldconfig
# jemalloc must be loaded before Python or ctypes.CDLL(libhpx) hits a TLS error.
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# ---------------------------------------------------------------------------
# Jupyter / JupyterHub
# ---------------------------------------------------------------------------
RUN python3 -m pip install --no-cache-dir --ignore-installed \
        "jupyterhub==4.1.6" \
        "notebook==7.2.2" \
        "jupyterlab==4.2.5" \
        ipykernel jupyter \
        matplotlib numpy termcolor \
        "oauthenticator>=16,<17" \
        piraha==1.1.7 \
    && python3 -m pip install --no-cache-dir \
        git+https://github.com/stevenrbrandt/cyolauthenticator.git@v1.2 \
    && python3 -m pip install --no-cache-dir --no-deps "python-telegram-bot==13.15" \
        || python3 -m pip install --no-cache-dir "python-telegram-bot" \
        || true \
    && npm install -g configurable-http-proxy \
    && (python3 -m pip install --no-cache-dir randpass || true)

WORKDIR /usr/local/share/cling/Jupyter/kernel
COPY clingk.py /usr/local/share/cling/Jupyter/kernel/clingkernel.py
RUN python3 -m pip install --no-cache-dir -e /usr/local/share/cling/Jupyter/kernel \
    && jupyter kernelspec install /usr/local/share/cling/Jupyter/kernel/cling-cpp17 \
    && jupyter kernelspec install /usr/local/share/cling/Jupyter/kernel/cling-cpp20 \
    && (jupyter kernelspec install /usr/local/share/cling/Jupyter/kernel/cling-cpp23 || true) \
    && (jupyter kernelspec install /usr/local/share/cling/Jupyter/kernel/cling-cpp2b || true)

RUN mkdir -p /usr/local/python
COPY cling_env.py cin.py cling.py py11.py pipes1.py pipes3.py \
     is_expr.py find.py mkuser.py gen_hpx_cling_config.py \
     /usr/local/python/
COPY mkuser.py /usr/local/bin/mkuser
COPY hpxcxx /usr/local/bin/hpxcxx
RUN chmod 755 /usr/local/bin/mkuser /usr/local/bin/hpxcxx \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && echo "export PYTHONPATH=${PYTHONPATH}" >> /etc/bash.bashrc \
    && echo "export PATH=/usr/local/bin:\$PATH" >> /etc/bash.bashrc \
    && echo "export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64" >> /etc/bash.bashrc \
    && echo "export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig" >> /etc/bash.bashrc

# JupyterHub branding / auth templates
COPY ./login.html /usr/local/share/jupyterhub/templates/login.html
COPY ./login2.html /root/login2.html
COPY ./error.html /root/error.html
COPY ./stellar-logo.png /usr/local/share/jupyterhub/static/images/
COPY ./logo.png /usr/local/share/jupyterhub/static/images/

WORKDIR /root
COPY ./startup.sh /root/startup.sh
COPY ./jup-config.py /root/jup-config.py
COPY ./nb.py /root/nb.py
RUN git clone -b v1.2 --depth 1 https://github.com/stevenrbrandt/cyolauthenticator.git \
    && chmod 755 /root /root/startup.sh

WORKDIR /notebooks
COPY ./notebk.sh /notebooks/notebk.sh
COPY ./smoke_test.sh /usr/local/share/cxxex-smoke.sh
RUN chmod 755 /notebooks/notebk.sh /usr/local/share/cxxex-smoke.sh

WORKDIR /etc/skel
COPY ./notebooks/*.ipynb ./
COPY ./notebooks/*.hpp ./
RUN git clone --depth 1 https://github.com/shortcourse/WCCM-APCOM-22 \
    && find . -type f -exec chmod +r {} +

RUN useradd -m -s /bin/bash jovyan || true
USER jovyan
WORKDIR /home/jovyan
RUN mkdir -p /home/jovyan/bot
COPY --chown=jovyan:jovyan bot/cxxbot.py bot/teleplot.py bot/telecling.py \
     bot/thumbsup.png bot/colored.py /home/jovyan/bot/

USER root
# Rebuild libclingJupyter from Kernel.cpp against the installed libcling.so so
# kernel edits do not invalidate the LLVM/Cling build cache.
COPY Pipe.hpp Augment_Kernel.hpp /usr/local/include/
COPY Kernel.cpp /tmp/cxxex-kernel/
RUN g++ -shared -fPIC -fexceptions -frtti -std=c++17 \
        -I/usr/local/include \
        -o /usr/local/lib/libclingJupyter.so.20.1 \
        /tmp/cxxex-kernel/Kernel.cpp \
        -L/usr/local/lib -lcling -latomic \
        -Wl,-soname,libclingJupyter.so.20.1 \
        -Wl,--export-dynamic \
    && rm -rf /tmp/cxxex-kernel \
    && ldconfig /usr/local/lib /usr/local/lib64
COPY ./jupyter_lab_config.py /usr/local/etc/jupyter/jupyter_lab_config.py
RUN python3 -m pip install --no-cache-dir "httpx>=0.27.2,<0.28"
COPY ./Dockerfile /Dockerfile
RUN ldconfig /usr/local/lib /usr/local/lib64

USER jovyan
WORKDIR /home/jovyan
CMD ["bash", "/notebooks/notebk.sh"]
