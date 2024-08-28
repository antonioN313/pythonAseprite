from os import environ, chdir
from shutil import move, Error
from subprocess import run, CalledProcessError
from zipfile import ZipFile, BadZipFile
from requests import get, RequestException
from pathlib import Path
from re import sub
from pprint import pprint
import platform
import sys



# Constants
ASEPRITE_REPO = "aseprite/aseprite"
SKIA_REPO = "aseprite/skia"
SRC_DIR = Path("~/src").expanduser()
ASE_DIR = SRC_DIR / "ase"
SKIA_DIR = SRC_DIR / "deps/skia"
ASE_BUILD_DIR = ASE_DIR / "build"
OPT_DIR = Path("~/opt").expanduser()

# Debian Dependencies
debian_prerequests = [
    "g++", "clang", "libc++-dev", "libc++abi-dev", "cmake",
    "ninja-build", "libx11-dev", "libxcursor-dev", "libxi-dev", "libgl1-mesa-dev",
    "libfontconfig1-dev"
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

def get_latest_release_url(repo):
    try:
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        latest_release = response.json()
        system = platform.system()
        archtecture = platform.machine()
        print(f"System: {system}")
        print(f"Architecture: {archtecture}")
        if repo == SKIA_REPO:
            filenames = [
                #f"Skia-{system}-Release-{archtecture}-libc++.zip",
                f"Skia-{system}-Release-{archtecture}-libstdc++.zip"
            ]
        else:
            filenames = [f"Aseprite-{latest_release['tag_name']}-Source.zip"]

        for asset in latest_release['assets']:
            if asset['name'] in filenames:
                print(f"Download URL:{asset['browser_download_url']}")
                return asset['browser_download_url']
    except RequestException as e:
        print(f"Failed to fetch latest release from {repo}.")
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

def update_cmake_cache():
    """Update USE_SHARED_ flags in CMakeCache.txt to ON."""
    cmake_cache_path = ASE_BUILD_DIR / "CMakeCache.txt"
    
    try:
        with open(cmake_cache_path, 'r') as file:
            lines = file.readlines()
        
        with open(cmake_cache_path, 'w') as file:
            for line in lines:
                if line.startswith("USE_SHARED_") and line.strip().endswith("=OFF"):
                    line = sub(r'=OFF', '=ON', line)
                file.write(line)
    except Exception as e:
        print(f"Failed to update {cmake_cache_path}.")
        print(e)
        exit(1)

def build_aseprite():
    """Build the Aseprite application using cmake and ninja."""
    try:
        chdir(ASE_BUILD_DIR)

        cmake_command = [
            "cmake",
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DLAF_BACKEND=skia",
            f"-DSKIA_DIR={SKIA_DIR}",
            f"-DSKIA_LIBRARY_DIR={SKIA_DIR / 'out/Release-x64'}",
            f"-DSKIA_LIBRARY={SKIA_DIR / 'out/Release-x64/libskia.a'}",
            "-G", "Ninja", ".."
        ]

        if environ['CXX'] == 'g++':
            cmake_command.extend([
                "-DCMAKE_CXX_FLAGS:STRING=-static-libstdc++",
                "-DCMAKE_EXE_LINKER_FLAGS:STRING=-static-libstdc++"
            ])

        run_command(cmake_command)

        print("Automatically setting USE_SHARED_ flags to ON.")
        update_cmake_cache()

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
    download_and_unpack(get_latest_release_url(ASEPRITE_REPO), ASE_DIR)

    # Download & unpack Skia library
    chdir(SKIA_DIR)
    download_and_unpack(get_latest_release_url(SKIA_REPO), SKIA_DIR)

    set_environment_variables()
    build_aseprite()
    install_aseprite()

if __name__ == "__main__":
    main()
