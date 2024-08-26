from os import environ, chdir
from shutil import move, Error
from subprocess import run, CalledProcessError
from zipfile import ZipFile, BadZipFile
from requests import get, RequestException
from pathlib import Path
from time import sleep

# Constants
ASEPRITE_SRC_URL = "https://github.com/aseprite/aseprite/releases/download/v1.3.8.1/Aseprite-v1.3.8.1-Source.zip"
SKIA_LIB_URL = "https://github.com/aseprite/skia/releases/download/m102-861e4743af/Skia-Linux-Release-x64-libstdc++.zip"
SRC_DIR = Path("~/src").expanduser()
ASE_DIR = SRC_DIR / "ase"
SKIA_DIR = SRC_DIR / "deps/skia"
ASE_BUILD_DIR = ASE_DIR / "build"
OPT_DIR = Path("~/opt").expanduser()

# Debian Dependencies
debian_prerequests = [
    "zip", "unzip", "g++", "clang", "libc++-dev", "libc++abi-dev", "cmake",
    "ninja-build", "libx11-dev", "libxcursor-dev", "libxi-dev", "libgl1-mesa-dev",
    "libfontconfig1-dev", "curl", "nano"
]
debian_prerequests_libstdc= [
    "libharfbuzz-dev", "libgif-dev", "libjpeg-dev", "libcurl4-openssl-dev",
    "libtinyxml2-dev", "libpixman-1-dev", "libcmark-dev"
]

def run_command(command, capture_output=False):
    """Runs a shell command and returns the result."""
    try:
        result = run(command, capture_output=capture_output, text=True, check=True)
        if capture_output:
            return result.stdout
    except CalledProcessError as e:
        print(f"An error occurred while running command: {command}")
        print(e)
        exit(1)

def install_dependencies():
    """Install required dependencies using apt."""
    try:
        run_command(["sudo", "apt", "update"])
        run_command(["sudo", "apt", "install", "-y"] + debian_prerequests+ debian_prerequests_libstdc)
    except Exception as e:
        print("Failed to install dependencies.")
        print(e)
        exit(1)

def create_directories():
    """Create necessary directories."""
    try:
        ASE_BUILD_DIR.mkdir(parents=True, exist_ok=True)
        SKIA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print("Failed to create directories.")
        print(e)
        exit(1)

def download_and_unpack(url, dest):
    """Download and unpack a zip file from a URL."""
    try:
        response = get(url)
        response.raise_for_status()
        zip_path = dest / url.split("/")[-1]  # Extract file name from URL
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest)
    except RequestException as e:
        print(f"Failed to download file from {url}.")
        print(e)
        exit(1)
    except BadZipFile as e:
        print(f"Failed to unzip file: {zip_path}.")
        print(e)
        exit(1)

def set_environment_variables():
    """Set environment variables for building."""
    try:
        environ['CC'] = 'clang'
        environ['CXX'] = 'clang++'
    except Exception as e:
        print("Failed to set environment variables.")
        print(e)
        exit(1)

def build_aseprite():
    """Build the Aseprite application using cmake and ninja."""
    try:
        chdir(ASE_BUILD_DIR)

        cmake_command = [
            "cmake",
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DCMAKE_CXX_FLAGS:STRING=-static-libstdc++",
            "-DCMAKE_EXE_LINKER_FLAGS:STRING=-static-libstdc++",
            "-DLAF_BACKEND=skia",
            f"-DSKIA_DIR={SKIA_DIR}",
            f"-DSKIA_LIBRARY_DIR={SKIA_DIR / 'out/Release-x64'}",
            f"-DSKIA_LIBRARY={SKIA_DIR / 'out/Release-x64/libskia.a'}",
            "-G", "Ninja", ".."
        ]

        run_command(cmake_command)

        print("Enable the USE_SHARED_ flags; set their value to ON.")
        sleep(5)
        run_command(["nano", "-w", "CMakeCache.txt"])

        run_command(["ninja", "aseprite"])
    except Exception as e:
        print("Failed to build Aseprite.")
        print(e)
        exit(1)

def install_aseprite():
    """Install Aseprite by moving it to the desired location."""
    try:
        OPT_DIR.mkdir(parents=True, exist_ok=True)
        move(str(ASE_BUILD_DIR / "bin"), str(OPT_DIR / "aseprite"))
        run_command([str(OPT_DIR / "aseprite/aseprite")])
    except (OSError, Error) as e:
        print("Failed to install Aseprite.")
        print(e)
        exit(1)

def main():
    install_dependencies()
    create_directories()

    # Download & unpack Aseprite source
    chdir(ASE_DIR)
    download_and_unpack(ASEPRITE_SRC_URL, ASE_DIR)

    # Download & unpack Skia library
    chdir(SKIA_DIR)
    download_and_unpack(SKIA_LIB_URL, SKIA_DIR)

    set_environment_variables()
    build_aseprite()
    install_aseprite()

if __name__ == "__main__":
    main()
