FROM fedora:32
RUN dnf install -y gcc-c++ gcc make git \
    bzip2 hwloc-devel blas blas-devel lapack lapack-devel boost-devel \
    libatomic which compat-openssl10 vim-enhanced wget zlib-devel \
    python3-flake8 gdb sudo python3 python3-pip openmpi-devel sqlite-devel sqlite \
    findutils openssl-devel papi papi-devel lm_sensors-devel tbb-devel cmake \
    xz bzip2 patch flex openssh-server \
    texlive-xetex texlive-bibtex texlive-adjustbox texlive-caption texlive-collectbox \
    texlive-enumitem texlive-environ texlive-eurosym texlive-jknapltx texlive-parskip \
    texlive-pgf texlive-rsfs texlive-tcolorbox texlive-titling texlive-trimspaces \
    texlive-ucs texlive-ulem texlive-upquote texlive-latex pandoc 

ARG CPUS
ARG BUILD_TYPE

WORKDIR /
## ENV GCC_VER 8.4.0
## COPY install-from-spack.sh /usr/local/bin
## RUN bash /usr/local/bin/install-from-spack.sh
## COPY alternatives.sh /usr/local/bin
## RUN bash /usr/local/bin/alternatives.sh

ENV AH_VER 4.6.0
RUN curl -kLO https://www.dyninst.org/sites/default/files/downloads/harmony/ah-${AH_VER}.tar.gz
RUN tar -xzf ah-${AH_VER}.tar.gz
WORKDIR /activeharmony-${AH_VER}
COPY ./activeharmony-4.6.0/code-server/code_generator.cxx code-server/code_generator.cxx
RUN make CFLAGS=-fPIC LDFLAGS=-fPIC && make install prefix=/usr/local/activeharmony

ENV OTF2_VER 2.1.1
WORKDIR /
RUN curl -kLO https://www.vi-hps.org/cms/upload/packages/otf2/otf2-${OTF2_VER}.tar.gz
RUN tar -xzf otf2-${OTF2_VER}.tar.gz
WORKDIR otf2-${OTF2_VER}
RUN ./configure --prefix=/usr/local/otf2 --enable-shared && make && make install

RUN ln -s /usr/lib64/openmpi/lib/libmpi_cxx.so /usr/lib64/openmpi/lib/libmpi_cxx.so.1
RUN ln -s /usr/lib64/openmpi/lib/libmpi.so /usr/lib64/openmpi/lib/libmpi.so.12

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

RUN git clone -b 1.6.0 --depth 1 https://github.com/STEllAR-GROUP/hpx.git
WORKDIR /hpx
RUN mkdir -p /hpx/build
WORKDIR /hpx/build
RUN cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
      -DHPX_WITH_BUILTIN_INTEGER_PACK=Off \
      -DHPX_WITH_ITTNOTIFY=OFF \
      -DHPX_WITH_THREAD_COMPATIBILITY=ON \
      -DHPX_WITH_MALLOC=system \
      -DHPX_WITH_MORE_THAN_64_THREADS=ON \
      -DHPX_WITH_MAX_CPU_COUNT=80 \
      -DHPX_WITH_EXAMPLES=Off \
      .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

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
COPY ./notebooks/*.ipynb ./
RUN git clone --depth 1 https://github.com/shortcourse/USACM16-shortcourse
RUN find . | xargs -d '\n' chmod +r

RUN useradd -m jovyan -s /bin/bash
USER jovyan
WORKDIR /home/jovyan
ENV LD_LIBRARY_PATH /home/jovyan/install/phylanx/lib64:/usr/local/lib64:/home/jovyan/install/phylanx/lib/phylanx:/usr/lib64/openmpi/lib
USER root
RUN dnf install -y nodejs psmisc tbb-devel
RUN pip3 install --upgrade pip
RUN pip3 install jupyter==1.0.0 jupyterhub==1.0.0 matplotlib numpy termcolor

ENV DATE 2020-03-10
RUN mkdir -p /usr/install/cling
WORKDIR /usr/install/cling
RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/llvm.git src
WORKDIR /usr/install/cling/src/tools 
RUN git clone --depth 1 http://root.cern.ch/git/cling.git
RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/clang.git

WORKDIR /usr/install/cling/src/tools/cling

RUN mkdir -p /usr/install/cling/src/build
COPY Pipe.hpp /usr/local/include/
COPY Augment_Kernel.hpp /usr/local/include
COPY Kernel.cpp /usr/install/cling/src/tools/cling/tools/Jupyter

WORKDIR /usr/install/cling/src/build
RUN cmake -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-Wl,-s' \
  -DLLVM_ENABLE_RTTI=ON \
  -DLLVM_ENABLE_EH=ON \
  /usr/install/cling/src
RUN dnf install -y patch
WORKDIR /usr/install/cling/src
# COPY char.patch ./
# RUN patch -p1 < char.patch
WORKDIR /usr/install/cling/src/tools/cling
COPY noexcept.patch ./
RUN patch -p1 < noexcept.patch
WORKDIR /usr/install/cling/src/build
COPY make.sh /usr/install/cling/src/build/
RUN bash ./make.sh
RUN  cd /usr/install/cling/src/tools/cling/tools/Jupyter/kernel && \
  pip3 install -e . && \
  jupyter-kernelspec install cling-cpp14 && \
  jupyter-kernelspec install cling-cpp17 && \
  npm install -g configurable-http-proxy 
WORKDIR /usr
## ENV CLING cling_2020-11-05_ROOT-fedora32
## ENV CLING_TARBALL ${CLING}.tar.bz2
## RUN curl -LO https://root.cern/download/cling/${CLING_TARBALL} && \
##     tar xjf ${CLING_TARBALL} && \
##     rm -f ${CLING_TARBALL}
## WORKDIR /usr/${CLING}/share/cling/Jupyter/kernel
## RUN pip3 install -e . && \
##     jupyter-kernelspec install cling-cpp17 && \
##     npm install -g configurable-http-proxy && \
##     ln -s /usr/${CLING}/bin/cling /usr/bin/cling

## RUN (make -j 8 install 2>&1 | tee make.out)
COPY ./run_hpx.cpp /usr/include/run_hpx.cpp
RUN chmod 644 /usr/include/run_hpx.cpp

RUN pip3 install oauthenticator
RUN dnf install -y procps cppcheck python3-pycurl sqlite python3-libs
COPY ./login.html /usr/local/share/jupyterhub/templates/login.html
COPY ./stellar-logo.png /usr/local/share/jupyterhub/static/images/

ENV PYTHONPATH /usr/local/python
RUN mkdir -p /usr/local/python
COPY ./mkuser.py ${PYTHONPATH}/mkuser.py
COPY ./mkuser.py /usr/local/bin/mkuser
RUN chmod 755 /usr/local/bin/mkuser
RUN pip3 install tornado #==5.1.1 # There's a bug in newer versions
COPY ./clingk.py /usr/${CLING}/share/cling/Jupyter/kernel/clingkernel.py
RUN python3 -c 'import sys; print(sys.path[-1])' > /tmp/path.txt
COPY ./pipes1.py ${PYTHONPATH}/
COPY ./pipes3.py ${PYTHONPATH}/
COPY ./cling.py ${PYTHONPATH}/
COPY ./py11.py ${PYTHONPATH}/
#RUN cp /Python-${PYVER}/pyconfig.h /Python-${PYVER}/Include
#RUN ln -s /Python-${PYVER}/Include /usr/include/python${PYVER}
WORKDIR /

RUN git clone --depth 1 https://github.com/STEllAR-GROUP/BlazeIterative
WORKDIR /BlazeIterative/build
RUN cmake ..
RUN make install

# For some reason, HPX will not link in @py11() unless I do this
RUN ldconfig /usr/local/lib64

WORKDIR /notebooks
COPY ./notebk.sh ./

WORKDIR /root
RUN chmod 755 .
COPY ./startup.sh startup.sh
COPY ./jup-config.py jup-config.py

# For authentication if we aren't using OAuth
RUN git clone --depth 1 https://github.com/stevenrbrandt/cyolauthenticator.git
RUN pip3 install git+https://github.com/stevenrbrandt/cyolauthenticator.git

# Use this CMD for a jupyterhub
# CMD bash startup.sh

COPY clingk.py /usr/install/cling/src/tools/cling/tools/Jupyter/kernel/clingkernel.py
# RUN ln -s /usr/${CLING}/lib/libclingJupyter.so /usr/lib/libclingJupyter.so
# RUN ln -s /usr/${CLING}/lib/clang /usr/lib/clang
# RUN ln -s /usr/${CLING}/include/cling /usr/include/cling
RUN echo "export PYTHONPATH=${PYTHONPATH}" >> /etc/bashrc
RUN dnf install -y ImageMagick file hostname
COPY logo.png /usr/local/share/jupyterhub/static/images/

COPY ./Dockerfile /Dockerfile
USER jovyan
WORKDIR /home/jovyan
COPY nb.py /root/
CMD bash /notebooks/notebk.sh
