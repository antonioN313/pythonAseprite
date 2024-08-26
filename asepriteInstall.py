import os, shutil,platform,sys,subprocess,zipfile
from pathlib import Path

debian_prerequests = ["zip","unzip","g++","clang","libc++-dev","libc++abi-dev","cmake", "ninja-build",
"libx11-dev", "libxcursor-dev","libxi-dev","libgl1-mesa-dev", "libfontconfig1-dev","curl","nano"]
debian_prerequests_libstdc = ["libharfbuzz-dev","libgif-dev", "libjpeg-dev", "libcurl4-openssl-dev",
"libtinyxml2-dev","libpixman-1-dev","libcmark-dev"]

subprocess.run(["sudo","apt","install","-y"]+debian_prerequests+debian_prerequests_libstdc, capture_output=True)


os.makedirs(os.path.expanduser("~/src/ase/build"), exist_ok=True)
os.makedirs(os.path.expanduser("~/src/deps/skia"), exist_ok=True)

os.chdir(os.path.expanduser("~/src/ase"))
subprocess.run(["curl", "-LO", "https://github.com/aseprite/aseprite/releases/download/v1.3.8.1/Aseprite-v1.3.8.1-Source.zip"])
subprocess.run(["unzip", "Aseprite-v1.3.8.1-Source.zip"])
os.chdir(os.path.expanduser("~/src/deps/skia"))
subprocess.run(["curl", "-LO", "https://github.com/aseprite/skia/releases/download/m102-861e4743af/Skia-Linux-Release-x64-libstdc++.zip"])
subprocess.run(["unzip", "Skia-Linux-Release-x64-libstdc++.zip"])

