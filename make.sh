export NCPUS=$(lscpu|grep '^CPU.s.:'|cut -d: -f2)
export BUILD_CPUS=$(($NCPUS/2))
make -j $BUILD_CPUS install 2>&1 | tee make.out
cd /usr/install/cling
find . -type f -a \( -name \*.o -o -name \*.cmake -o -name \*.cpp -o -name \*.h -name \*.c \) | xargs rm -f
