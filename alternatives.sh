source /usr/spack/share/spack/setup-env.sh
spack load gcc
update-alternatives --install /usr/bin/cc cc $(which gcc) 1
rm -f /usr/bin/c++
ln -s /etc/alternatives/c++ /usr/bin/c++
update-alternatives --install /usr/bin/c++ c++ $(which g++) 1
