#!/usr/bin/bash

base_sha1=$1
build_path="../app-helloworld/build/app-helloworld_qemu-x86_64"

# Install requirements
sudo apt-get update -y > /dev/null 2>&1
sudo apt-get install -y qemu-system-x86-64 python3 > /dev/null 2>&1

# Run lib-libc-test on the current pr
git clone https://github.com/unikraft/app-helloworld ../app-helloworld --depth=1 > /dev/null 2>&1
git clone https://github.com/unikraft/lib-libc-test ../libs/lib-libc-test --depth=1 > /dev/null 2>&1
git clone https://github.com/unikraft/lib-musl ../libs/lib-musl --depth=1 > /dev/null 2>&1
git clone https://github.com/unikraft/lib-lwip ../libs/lib-lwip --depth=1 > /dev/null 2>&1
cp config/app-config ../app-helloworld/.config
cp config/app-Makefile ../app-helloworld/Makefile
pushd ../app-helloworld > /dev/null && make -j$(nproc) > build_log.txt 2>&1 && popd > /dev/null
[ -e "$build_path" ] || { echo "Build staging branch failed, see logs below:"; cat build_log.txt; exit 1; }
qemu-system-x86_64 -kernel $build_path -nographic -cpu max > test_result_new.txt

# Run lib-libc-test on unikraft:staging
rm -rf ../app-helloworld/build && rm -rf ../unikraft
git clone https://github.com/i-Pear/unikraft ../unikraft --depth=1 > /dev/null 2>&1
pushd ../unikraft > /dev/null && git reset --hard $base_sha1 > /dev/null && popd > /dev/null
pushd ../app-helloworld > /dev/null && make -j$(nproc) > build_log.txt 2>&1 && popd > /dev/null
[ -e "$build_path" ] || { echo "Build your PR failed, see logs below:"; cat build_log.txt; exit 1; }
qemu-system-x86_64 -kernel $build_path -nographic -cpu max > test_result_staging.txt

# Diff and report test results
python3 ./report.py test_result_staging.txt test_result_new.txt
exit $?
