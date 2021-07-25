make -j 20 install 2>&1 | tee make.out
rm -fr bin $(find . -name \*.o) $(find . -name \*.cmake)
