cd /usr
git clone https://github.com/spack/spack.git
source /usr/spack/share/spack/setup-env.sh
spack install gcc@${GCC_VER}
spack load gcc@${GCC_VER}
spack compiler find
spack gc -y
