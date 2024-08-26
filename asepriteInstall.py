import os, shutil,platform,sys,subprocess,zipfile
from pathlib import Path
from time import sleep

# Debian Dependencies
debian_prerequests = ["zip","unzip","g++","clang","libc++-dev","libc++abi-dev","cmake", "ninja-build",
"libx11-dev", "libxcursor-dev","libxi-dev","libgl1-mesa-dev", "libfontconfig1-dev","curl","nano"]
debian_prerequests_libstdc = ["libharfbuzz-dev","libgif-dev", "libjpeg-dev", "libcurl4-openssl-dev",
"libtinyxml2-dev","libpixman-1-dev","libcmark-dev"]

#update & upgrade
subprocess.run(["sudo","apt","install","-y"])
subprocess.run(["sudo","apt","install","-y"]+debian_prerequests+debian_prerequests_libstdc, capture_output=True)

#create folders
os.makedirs(os.path.expanduser("~/src/ase/build"), exist_ok=True)
os.makedirs(os.path.expanduser("~/src/deps/skia"), exist_ok=True)

#Download & unpack Aseprite source
os.chdir(os.path.expanduser("~/src/ase"))
subprocess.run(["curl", "-LO", "https://github.com/aseprite/aseprite/releases/download/v1.3.8.1/Aseprite-v1.3.8.1-Source.zip"])
subprocess.run(["unzip", "Aseprite-v1.3.8.1-Source.zip"])

#Download & unpack Skia library
os.chdir(os.path.expanduser("~/src/deps/skia"))
subprocess.run(["curl", "-LO", "https://github.com/aseprite/skia/releases/download/m102-861e4743af/Skia-Linux-Release-x64-libstdc++.zip"])
subprocess.run(["unzip", "Skia-Linux-Release-x64-libstdc++.zip"])

#build aseprite

os.chdir(os.path.expanduser("~/src/ase/build"))

#Clang
os.environ['CC'] = 'clang'
os.environ['CXX'] = 'clang++'

cmake_command = f"""
cmake \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_FLAGS:STRING=-static-libstdc++ \
  -DCMAKE_EXE_LINKER_FLAGS:STRING=-static-libstdc++ \
  -DLAF_BACKEND=skia \
  -DSKIA_DIR={os.path.expanduser("~/src/deps/skia")} \
  -DSKIA_LIBRARY_DIR={os.path.expanduser("~/src/deps/skia/out/Release-x64")} \
  -DSKIA_LIBRARY={os.path.expanduser("~/src/deps/skia/out/Release-x64/libskia.a")} \
  -G Ninja ..
"""

subprocess.run(cmake_command, shell=True, check=True)

print("Enable the `USE_SHARED_` flags; set their value to `ON`.")
sleep(5)
subprocess.run(["sudo","nano","-w","CmakeCache.txt"])

subprocess.run(["ninja","aseprite"])

#install program
os.makedirs(os.path.expanduser("~/opt"), exist_ok=True)
subprocess.run(["mv","-T", "bin",os.path.expanduser("~/opt/aseprite")])
subprocess.run([os.path.expanduser("~/opt/aseprite/aseprite")])
