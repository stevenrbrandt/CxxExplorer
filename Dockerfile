FROM fedora:27
RUN dnf install -y gcc-c++ gcc make cmake git \
    bzip2 hwloc-devel blas blas-devel lapack lapack-devel boost-devel \
    libatomic which compat-openssl10 vim-enhanced wget zlib-devel \
    python3-flake8 gdb sudo python36 openmpi-devel sqlite-devel sqlite \
    findutils openssl-devel papi papi-devel lm_sensors-devel

ARG CPUS
ARG BUILD_TYPE

ENV AH_VER 4.6.0
RUN curl -kLO https://www.dyninst.org/sites/default/files/downloads/harmony/ah-${AH_VER}.tar.gz
RUN tar -xzf ah-${AH_VER}.tar.gz
WORKDIR /activeharmony-${AH_VER}
COPY activeharmony-4.6.0/code-server/code_generator.cxx code-server/code_generator.cxx
RUN make CFLAGS=-fPIC LDFLAGS=-fPIC && make install prefix=/usr/local/activeharmony

ENV OTF2_VER 2.1.1
WORKDIR /
RUN curl -kLO https://www.vi-hps.org/cms/upload/packages/otf2/otf2-${OTF2_VER}.tar.gz
RUN tar -xzf otf2-${OTF2_VER}.tar.gz
WORKDIR otf2-${OTF2_VER}
RUN ./configure --prefix=/usr/local/otf2 --enable-shared && make && make install

RUN ln -s /usr/lib64/openmpi/lib/libmpi_cxx.so /usr/lib64/openmpi/lib/libmpi_cxx.so.1
RUN ln -s /usr/lib64/openmpi/lib/libmpi.so /usr/lib64/openmpi/lib/libmpi.so.12

ENV PYVER 3.6.8
WORKDIR /
RUN wget https://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz
RUN tar xf Python-${PYVER}.tgz
WORKDIR /Python-${PYVER}
RUN ./configure
RUN make -j ${CPUS} install

# Make headers available
RUN cp /Python-${PYVER}/pyconfig.h /Python-${PYVER}/Include
RUN ln -s /Python-${PYVER}/Include /usr/include/python${PYVER}

RUN pip3 install --trusted-host pypi.org --trusted-host files.pythonhosted.org numpy tensorflow keras CNTK pytest
RUN pip3 install numpy tensorflow keras CNTK pytest
WORKDIR /

RUN git clone --depth 1 https://github.com/STEllAR-GROUP/hpx.git && \
    mkdir -p /hpx/build && \
    cd /hpx/build && \
    cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
      -DHPX_WITH_MALLOC=system \
      -DHPX_WITH_MORE_THAN_64_THREADS=ON \
      -DHPX_WITH_MAX_CPU_COUNT=80 \
      -DHPX_WITH_EXAMPLES=Off \
      -DHPX_WITH_APEX=TRUE \
      -DAPEX_WITH_ACTIVEHARMONY=TRUE \
      -DACTIVEHARMONY_ROOT=/usr/local/activeharmony \
      -DAPEX_WITH_OTF2=TRUE \
      -DOTF2_ROOT=/usr/local/otf2 \
      -DAPEX_WITH_PAPI=TRUE \
      -DHPX_WITH_APEX_NO_UPDATE=TRUE \
      -DHPX_WITH_APEX_TAG=develop \
      -DAPEX_WITH_BFD=FALSE \
      .. && \
    make -j ${CPUS} install && \
    rm -f $(find . -name \*.o)

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

RUN echo "ALL            ALL = (ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN useradd -m jovyan
USER jovyan
WORKDIR /home/jovyan
ENV LD_LIBRARY_PATH /home/jovyan/install/phylanx/lib64:/usr/local/lib64:/home/jovyan/install/phylanx/lib/phylanx:/usr/lib64/openmpi/lib
#===
USER root
RUN dnf install -y nodejs psmisc tbb-devel
#RUN apt-get install -y gcc g++ make python-pip python \
#  python3-pip python3 wget git \
#  make nodejs libpython3.5-dev vim hwloc libhwloc-dev
RUN pip3 install --upgrade pip
RUN pip3 install jupyter==1.0.0 jupyterhub==1.0.0 matplotlib numpy

#ENV PROCS 12

ENV DATE 2019-08-23
RUN mkdir -p /usr/install/cling
WORKDIR /usr/install/cling
RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/llvm.git src
#RUN git clone http://root.cern.ch/git/llvm.git src
#WORKDIR /usr/install/cling/src
#RUN git checkout `git rev-list -n 1 --before="${DATE} 00:00" cling-patches`
#WORKDIR /usr/install/cling/src
##RUN git checkout cling-patches
WORKDIR /usr/install/cling/src/tools 
RUN git clone --depth 1 http://root.cern.ch/git/cling.git
RUN git clone --depth 1 --branch cling-patches http://root.cern.ch/git/clang.git
#RUN git clone http://root.cern.ch/git/cling.git
#RUN git clone http://root.cern.ch/git/clang.git

#WORKDIR /usr/install/cling/src/tools/cling
#RUN git checkout `git rev-list -n 1 --before="${DATE} 00:00" master`

#WORKDIR /usr/install/cling/src/tools/clang
#RUN git checkout `git rev-list -n 1 --before="${DATE} 00:00" cling-patches`

WORKDIR /usr/install/cling/src/tools/cling
#COPY CMakeLists.txt CMakeLists.txt
#COPY tools/Jupyter/CMakeLists.txt tools/Jupyter/CMakeLists.txt
#COPY tools/Jupyter/Kernel.cpp tools/Jupyter/Kernel.cpp
#COPY tools/Jupyter/kernel/clingkernel.py tools/Jupyter/kernel/clingkernel.py
#COPY include/init3.cpp include/init3.cpp

RUN mkdir -p /usr/install/cling/src/build
WORKDIR /usr/install/cling/src
WORKDIR /usr/install/cling/src/build
RUN cmake -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS='-Wl,-s' \
  -DLLVM_ENABLE_RTTI=ON \
  -DLLVM_ENABLE_EH=ON \
  /usr/install/cling/src && \
  (make -j 4 install | tee make.out) && \
  cd /usr/install/cling/src/tools/cling/tools/Jupyter/kernel && \
  pip3 install -e . && \
  jupyter-kernelspec install cling-cpp14 && \
  jupyter-kernelspec install cling-cpp17 && \
  npm install -g configurable-http-proxy 

COPY run_hpx.cpp /usr/include/run_hpx.cpp
RUN chmod 644 /usr/include/run_hpx.cpp

#RUN apt-get update
#RUN apt-get install -y libblas-dev liblapack-dev
#WORKDIR /
#RUN git clone --depth 1 https://bitbucket.org/blaze-lib/blaze.git && \
#    mkdir -p /blaze/build && \
#    cd /blaze/build && \
#    cmake -DCXX=clang -DCMAKE_BUILD_TYPE=Debug -DBLAZE_SMP_THREADS=C++11 .. && \
#    make install

#WORKDIR /usr/install/root
#RUN useradd -m jup
#WORKDIR /usr/install/jup
#COPY ck.py /usr/install/cling/src/tools/cling/tools/Jupyter/kernel/clingkernel.py
#COPY ck.py /usr/share/cling/Jupyter/kernel/clingkernel.py
#RUN find . | xargs chown jup 
#RUN find . | xargs chgrp jup 
#WORKDIR /root
##RUN echo jup:jup1fun | chpasswd
#RUN mkdir -p /tutorial
#RUN chmod 755 /tutorial
#COPY *.ipynb /tutorial/
#COPY mkusers.sh mkusers.sh
#RUN bash mkusers.sh
#RUN rm mkusers.sh


##COPY login.html /usr/local/share/jupyter/hub/templates/login.html

## Python 2 in the notebook
##RUN python2 -m pip install ipykernel
##RUN python2 -m ipykernel install

##RUN apt-get install -y procps

### Useful stuff
###RUN apt-get install -y python-tables python3-tables
###RUN python2 -m pip install h5py numpy scipy matplotlib
###RUN python3 -m pip install h5py numpy scipy matplotlib
###RUN curl -kLO https://raw.githubusercontent.com/nds-org/jupyter-et/master/et-pkg-installer.py
###RUN python et-pkg-installer.py 
###RUN sh install-for-cactus.sh
###RUN apt-get install -y time mercurial
###RUN apt-get install -y gdb
###RUN apt-get install -y unzip
RUN pip3 install oauthenticator
RUN dnf install -y procps cppcheck python3-pycurl sqlite python3-libs
COPY login.html /usr/local/share/jupyterhub/templates/login.html
COPY stellar-logo.png /usr/local/share/jupyterhub/static/images/stellar-logo.png

#COPY spawner.py /usr/local/lib/python3.5/dist-packages/jupyterhub/spawner.py
#COPY github.py /usr/local/lib/python3.5/dist-packages/oauthenticator/github.py
COPY mkuser.py /usr/local/lib/python3.6/site-packages/mkuser.py
COPY mkuser.py /usr/local/bin/mkuser
RUN chmod 755 /usr/local/bin/mkuser
RUN pip3 install tornado==5.1.1 # There's a bug in newer versions
#COPY spawner.py-3.6 /usr/local/lib/python3.6/site-packages/jupyterhub/spawner.py
COPY clingk.py /usr/install/cling/src/tools/cling/tools/Jupyter/kernel/clingkernel.py
COPY pipes1.py /usr/local/lib/python3.6/site-packages/
COPY pipes3.py /usr/local/lib/python3.6/site-packages/
COPY cling.py /usr/local/lib/python3.6/site-packages/
COPY py11.py /usr/local/lib/python3.6/site-packages/
RUN cp /Python-${PYVER}/pyconfig.h /Python-${PYVER}/Include
RUN ln -s /Python-${PYVER}/Include /usr/include/python${PYVER}
WORKDIR /

RUN git clone https://github.com/STEllAR-GROUP/BlazeIterative
WORKDIR /BlazeIterative/build
RUN cmake ..
RUN make install

# For some reason, HPX will not link in @py11() unless I do this
RUN ldconfig /usr/local/lib64

WORKDIR /notebooks
COPY notebk.sh ./


WORKDIR /root
RUN chmod 755 .
COPY startup.sh startup.sh
COPY jup-config.py jup-config.py

COPY Dockerfile /Dockerfile
CMD bash startup.sh
