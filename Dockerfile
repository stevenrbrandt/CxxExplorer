FROM fedora:40
RUN dnf install -y gcc-c++ gcc make git \
    bzip2 hwloc-devel blas blas-devel lapack lapack-devel boost-devel \
    libatomic which vim-enhanced wget zlib-devel cmake \
    python3-flake8 gdb sudo python3 python3-pip openmpi-devel sqlite-devel sqlite \
    findutils openssl-devel papi papi-devel lm_sensors-devel tbb-devel \
    xz bzip2 patch flex openssh-server \
    texlive-xetex texlive-bibtex texlive-adjustbox texlive-caption texlive-collectbox \
    texlive-enumitem texlive-environ texlive-eurosym texlive-jknapltx texlive-parskip \
    texlive-pgf texlive-rsfs texlive-tcolorbox texlive-titling texlive-trimspaces \
    texlive-ucs texlive-ulem texlive-upquote texlive-latex pandoc ImageMagick \
    root python3-root root-notebook python3-devel root-graf-gpadv7 

WORKDIR /
## ENV GCC_VER 8.4.0
## COPY install-from-spack.sh /usr/local/bin
## RUN bash /usr/local/bin/install-from-spack.sh
## COPY alternatives.sh /usr/local/bin
## RUN bash /usr/local/bin/alternatives.sh

# ENV AH_VER 4.6.0
# RUN curl -kLO https://www.dyninst.org/sites/default/files/downloads/harmony/ah-${AH_VER}.tar.gz
# RUN tar -xzf ah-${AH_VER}.tar.gz
# WORKDIR /activeharmony-${AH_VER}
# COPY ./activeharmony-4.6.0/code-server/code_generator.cxx code-server/code_generator.cxx
# RUN make CFLAGS=-fPIC LDFLAGS=-fPIC && make install prefix=/usr/local/activeharmony

# ENV OTF2_VER 2.1.1
# WORKDIR /
# RUN curl -kLO https://www.vi-hps.org/cms/upload/packages/otf2/otf2-${OTF2_VER}.tar.gz
# RUN tar -xzf otf2-${OTF2_VER}.tar.gz
# WORKDIR otf2-${OTF2_VER}
# RUN ./configure --prefix=/usr/local/otf2 --enable-shared && make && make install

#RUN ln -s /usr/lib64/openmpi/lib/libmpi_cxx.so /usr/lib64/openmpi/lib/libmpi_cxx.so.1
#RUN ln -s /usr/lib64/openmpi/lib/libmpi.so /usr/lib64/openmpi/lib/libmpi.so.12

#ENV PYVER 3.6.8
#WORKDIR /
#RUN wget https://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz
#RUN tar xf Python-${PYVER}.tgz
#WORKDIR /Python-${PYVER}
#RUN ./configure
#RUN make -j ${CPUS} install

## Make headers available
#RUN cp /Python-${PYVER}/pyconfig.h /Python-${PYVER}/Include
#RUN ln -s /Python-${PYVER}/Include /usr/include/python${PYVER}

#RUN pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org numpy tensorflow keras CNTK pytest
#RUN pip3 install numpy tensorflow keras CNTK pytest
WORKDIR /

RUN dnf install -y python3-devel

WORKDIR /
RUN git clone --depth 1 https://github.com/pybind/pybind11.git && \
    mkdir -p /pybind11/build && \
    cd /pybind11/build && \
    cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} -DPYBIND11_PYTHON_VERSION=${PYVER} .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

RUN git clone --depth 1 https://bitbucket.org/blaze-lib/blaze.git && \
    cd /blaze && \
    mkdir -p /blaze/build && \
    cd /blaze/build && \
    cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

RUN git clone --depth 1 https://github.com/STEllAR-GROUP/blaze_tensor.git && \
    mkdir -p /blaze_tensor/build && \
    cd /blaze_tensor/build && \
    cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

WORKDIR /etc/skel
#COPY ./notebooks/*.ipynb ./
#RUN git clone --depth 1 https://github.com/shortcourse/USACM16-shortcourse
#RUN git clone --depth 1 https://github.com/shortcourse/WCCM-APCOM-22
#RUN find . | xargs -d '\n' chmod +r

RUN useradd -m jovyan -s /bin/bash
USER jovyan
WORKDIR /home/jovyan
#ENV LD_LIBRARY_PATH=/home/jovyan/install/phylanx/lib64:/usr/local/lib64:/home/jovyan/install/phylanx/lib/phylanx:/usr/lib64/openmpi/lib
USER root
#RUN dnf install -y nodejs psmisc tbb-devel
RUN pip3 install --upgrade pip
RUN pip3 install jupyter matplotlib numpy termcolor oauthenticator==15.1.0 jupyterhub==4.1.5 cffi==1.16.0

#ENV DATE 2020-03-10
#RUN mkdir -p /usr/install/cling
#WORKDIR /usr/install/cling
#RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/llvm.git src
#WORKDIR /usr/install/cling/src/tools 
#RUN git clone --depth 1 http://root.cern.ch/git/cling.git
#RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/clang.git

#WORKDIR /usr/install/cling/src/tools/cling

#RUN mkdir -p /usr/install/cling/src/build
COPY Pipe.hpp /usr/local/include/
#COPY Augment_Kernel.hpp /usr/local/include
#COPY Kernel.cpp /usr/install/cling/src/tools/cling/tools/Jupyter

### WORKDIR /usr/install/cling/src/build
### RUN cmake -DCMAKE_INSTALL_PREFIX=/usr \
###   -DCMAKE_BUILD_TYPE=Release \
###   -DCMAKE_CXX_FLAGS='-Wl,-s -std=c++2a' \
###   -DLLVM_ENABLE_RTTI=ON \
###   -DLLVM_ENABLE_EH=ON \
###   /usr/install/cling/src
### # RUN dnf install -y patch
### WORKDIR /usr/install/cling/src
### COPY limits.patch .
### RUN patch -p1 < limits.patch
### WORKDIR /usr/install/cling/src/tools/cling
### COPY noexcept.patch ./
### RUN patch -p1 < noexcept.patch
### WORKDIR /usr/install/cling/src/build
### COPY make.sh /usr/install/cling/src/build/
### RUN bash ./make.sh
### RUN  cd /usr/install/cling/src/tools/cling/tools/Jupyter/kernel && \
###   pip3 install -e . && \
###   jupyter-kernelspec install cling-cpp17 && \
RUN dnf install -y npm
RUN npm install -g configurable-http-proxy 
### WORKDIR /usr
### ## ENV CLING cling_2020-11-05_ROOT-fedora32
### ## ENV CLING_TARBALL ${CLING}.tar.bz2
### ## RUN curl -LO https://root.cern/download/cling/${CLING_TARBALL} && \
### ##     tar xjf ${CLING_TARBALL} && \
### ##     rm -f ${CLING_TARBALL}
### ## WORKDIR /usr/${CLING}/share/cling/Jupyter/kernel
### ## RUN pip3 install -e . && \
### ##     jupyter-kernelspec install cling-cpp17 && \
### ##     npm install -g configurable-http-proxy && \
### ##     ln -s /usr/${CLING}/bin/cling /usr/bin/cling

RUN git clone --branch hpsf_2026 --depth 1 https://github.com/STEllAR-GROUP/hpx.git /hpx
WORKDIR /hpx
RUN mkdir -p /hpx/build
WORKDIR /hpx/build
#RUN env CXX=$(which clang++) cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
RUN cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
      -DHPX_FILESYSTEM_WITH_BOOST_FILESYSTEM_COMPATIBILITY=ON \
      -DHPX_WITH_CXX17_HARDWARE_DESTRUCTIVE_INTERFERENCE_SIZE=OFF \
      -DHPX_WITH_FETCH_ASIO=ON \
      -DHPX_WITH_BUILTIN_INTEGER_PACK=OFF \
      -DHPX_WITH_ITTNOTIFY=OFF \
      -DHPX_WITH_THREAD_COMPATIBILITY=ON \
      -DHPX_WITH_MALLOC=system \
      -DHPX_WITH_MORE_THAN_64_THREADS=ON \
      -DHPX_WITH_MAX_CPU_COUNT=80 \
      -DHPX_WITH_EXAMPLES=Off \
      -DHPX_WITH_CXX_STANDARD=20 \
      -DHPX_WITH_DATAPAR_BACKEND=STD_EXPERIMENTAL_SIMD \
      .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

### ## RUN (make -j 8 install 2>&1 | tee make.out)
### COPY ./run_hpx.cpp /usr/include/run_hpx.cpp
### RUN chmod 644 /usr/include/run_hpx.cpp

### RUN pip3 install oauthenticator
### #RUN dnf install -y procps cppcheck python3-pycurl sqlite python3-libs
COPY ./login.html /usr/local/share/jupyterhub/templates/login.html
COPY ./login2.html /root
COPY ./stellar-logo.png /usr/local/share/jupyterhub/static/images/

ENV PYTHONPATH=/usr/local/python
RUN mkdir -p /usr/local/python
#COPY ./mkuser.py ${PYTHONPATH}/mkuser.py
COPY ./mkuser.py /usr/local/bin/mkuser
RUN chmod 755 /usr/local/bin/mkuser
### RUN pip3 install tornado #==5.1.1 # There's a bug in newer versions
### COPY ./clingk.py /usr/${CLING}/share/cling/Jupyter/kernel/clingkernel.py
### RUN python3 -c 'import sys; print(sys.path[-1])' > /tmp/path.txt
### COPY ./pipes1.py ${PYTHONPATH}/
### COPY ./pipes3.py ${PYTHONPATH}/
### COPY ./cling.py ${PYTHONPATH}/
### COPY ./py11.py ${PYTHONPATH}/
### #RUN cp /Python-${PYVER}/pyconfig.h /Python-${PYVER}/Include
### #RUN ln -s /Python-${PYVER}/Include /usr/include/python${PYVER}
### WORKDIR /

WORKDIR /
RUN git clone --depth 1 https://github.com/STEllAR-GROUP/BlazeIterative.git
WORKDIR /BlazeIterative/build
RUN cmake ..
RUN make install

### # For some reason, HPX will not link in @py11() unless I do this
### RUN ldconfig /usr/local/lib64

WORKDIR /notebooks
COPY ./notebk.sh ./

WORKDIR /root
RUN chmod 755 .
COPY ./startup.sh startup.sh
COPY ./jup-config.py jup-config.py

### # For authentication if we aren't using OAuth
RUN git clone -b v1.2 --depth 1 https://github.com/stevenrbrandt/cyolauthenticator.git
RUN perl -p -i -e 's/from crypt import crypt/from crypt_r import crypt/' cyolauthenticator/cyolauthenticator/cyolauthenticator.py
WORKDIR /root/cyolauthenticator
RUN pip3 install crypt_r
RUN pip3 install .

### # Use this CMD for a jupyterhub
### # CMD bash startup.sh

### COPY clingk.py /usr/install/cling/src/tools/cling/tools/Jupyter/kernel/clingkernel.py
### # RUN ln -s /usr/${CLING}/lib/libclingJupyter.so /usr/lib/libclingJupyter.so
### # RUN ln -s /usr/${CLING}/lib/clang /usr/lib/clang
### # RUN ln -s /usr/${CLING}/include/cling /usr/include/cling
### RUN echo "export PYTHONPATH=${PYTHONPATH}" >> /etc/bashrc
### #RUN dnf install -y ImageMagick file hostname
### COPY is_expr.py /usr/local/python
### COPY logo.png /usr/local/share/jupyterhub/static/images/
### COPY teleplot.hpp /usr/include

### COPY ./Dockerfile /Dockerfile
### USER jovyan

### RUN mkdir -p /home/jovyan/bot
### COPY bot/cxxbot.py /home/jovyan/bot/
### COPY bot/teleplot.py /home/jovyan/bot/
### COPY bot/telecling.py /home/jovyan/bot/
### COPY bot/thumbsup.png /home/jovyan/bot/
### COPY bot/colored.py /home/jovyan/bot/
### RUN pip3 install --user randpass python-telegram-bot

### WORKDIR /home/jovyan
### COPY nb.py /root/
### COPY vector_pack_type.hpp /usr/local/include/hpx/execution/traits/detail/simd/vector_pack_type.hpp
### CMD bash /notebooks/notebk.sh

#USER jovyan
#WORKDIR /home/jovyan
USER root
RUN rm -fr /etc/skel/
RUN mkdir -p /etc/skel/
COPY HPX_Training.ipynb /etc/skel/
COPY mandelbrot.ipynb /etc/skel/
COPY Exercise1.ipynb /etc/skel/
COPY Exercise1-solution.ipynb /etc/skel/
COPY WCCM-APCOM-22/introduction.pdf /etc/skel/
COPY WCCM-APCOM-22/README.md /etc/skel/
COPY WCCM-APCOM-22/LICENSE /etc/skel/
COPY WCCM-APCOM-22/index.md /etc/skel/
RUN perl -p -i -e 's/Boost::/boost_/g' /usr/local/lib64/pkgconfig/*.pc

#WORKDIR /usr/root
#RUN dnf install libuuid-devel
#RUN git clone --branch latest-stable --depth=1 https://github.com/root-project/root.git root_src
#RUN /usr/root/build
#RUN cmake -Dx11=OFF ../root_src/
#RUN make -j10
RUN jupyter nbconvert --clear-output --inplace /etc/skel/*.ipynb

# # Building Standalone cling
# WORKDIR /usr/root
# RUN dnf install -y libuuid-devel
# RUN git clone https://github.com/root-project/llvm-project.git
# WORKDIR /usr/root/llvm-project
# RUN git checkout cling-llvm20 #cling-latest
# WORKDIR /usr/root
# RUN git clone https://github.com/root-project/cling.git
# WORKDIR /usr/root/cling
# RUN git checkout v1.3  # Checkout stable release without the mismatched feature
# WORKDIR /usr/root/cling-build
# RUN cmake -DLLVM_EXTERNAL_PROJECTS=cling \
#       -DLLVM_EXTERNAL_CLING_SOURCE_DIR=../cling/ \
#       -DLLVM_ENABLE_PROJECTS="clang" \
#       -DLLVM_TARGETS_TO_BUILD="host;NVPTX" \
#       -DCMAKE_CXX_FLAGS="-Wno-subobject-linkage"\
#       -DCMAKE_BUILD_TYPE=Release \
#       /usr/root/llvm-project/llvm
# RUN cmake --build . -j$(nproc)  # Use -jN for parallel jobs based on your cores
# RUN cmake --install .
# RUN cmake --build . --target libclingJupyter
# WORKDIR /usr/root/cling/tools/Jupyter/kernel
# RUN pip install -e .
# RUN jupyter-kernelspec install cling-cpp17

# Building ROOT
# RUN dnf install -y git cmake make gcc gcc-c++ libuuid-devel python3-devel python3-pip hpx-devel zlib-devel libxml2-devel openssl-devel fftw-devel gsl-devel xz-devel sqlite-devel readline-devel libAfterImage-devel glew-devel mesa-libGL-devel mesa-libGLU-devel ftgl-devel mysql-devel pcre-devel libX11-devel libXext-devel libXpm-devel libXft-devel

# WORKDIR /root

# # Clone ROOT and checkout latest stable
# RUN git clone --branch latest-stable --depth 1 https://github.com/root-project/root.git root_src

# # Create build directory
# WORKDIR /root/root-build

# # Configure CMake (enable PyROOT for Jupyter integration, HPX, and other useful features)
# RUN cmake -DCMAKE_INSTALL_PREFIX=/usr/local/root \
#           -Dbuiltin_cling=ON \
#           -Dpyroot=ON \
#           -Dhpx=ON \
#           -Dimt=ON \
#           -Droot7=ON \
#           -Djupyter=ON \
#           -DCMAKE_BUILD_TYPE=Release \
#           /root/root_src

# # Build and install (use all cores for speed)
# RUN cmake --build . --target install -j$(nproc)

# # Set up environment (add to shell profiles or run in container entrypoint)
# ENV PATH=/usr/local/root/bin:/usr/local/bin:/usr/bin:/bin
# ENV LD_LIBRARY_PATH=/usr/local/root/lib
# ENV PYTHONPATH=/usr/local/root/lib

# # Install Jupyter kernel (Cling-based for C++)
# WORKDIR /root/root_src/interpreter/cling/tools/Jupyter/kernel
# RUN pip install -e .
# RUN jupyter-kernelspec install cling-cpp17  # Repeat for cling-cpp11, cling-cpp14 if needed

RUN cp /usr/local/share/jupyterhub/static/images/stellar-logo.png /usr/local/share/jupyterhub/static/images/logo.png
COPY  hpsf-logo.png /usr/local/share/jupyterhub/static/images/hpsf-logo.png
COPY WCCM-APCOM-22/slides/* /etc/skel/

USER jovyan
WORKDIR /home/jovyan
RUN cp /etc/skel/* .
