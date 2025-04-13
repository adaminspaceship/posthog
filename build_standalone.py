#!/usr/bin/env python3
# Script to build a complete standalone offline Windows executable for PostHog

import os
import sys
import subprocess
import shutil
import zipfile
import urllib.request
import tempfile
from pathlib import Path

# Define paths
POSTHOG_DIR = Path("posthog-master")
BUILD_DIR = Path("build")
DIST_DIR = Path("dist/posthog")
OUTPUT_DIR = Path("output")
EMBEDDED_DIR = Path("embedded")
SCRIPTS_DIR = Path("scripts")

# Define URLs for downloading bundled runtimes
NODE_URL = "https://nodejs.org/dist/v18.19.1/node-v18.19.1-win-x64.zip"
PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
INNO_SETUP_URL = "https://files.jrsoftware.org/is/6/innosetup-6.2.2.exe"
POSTHOG_URL = "https://github.com/PostHog/posthog/archive/refs/heads/master.zip"

def run_command(command, cwd=None):
    """Run a command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, check=True)
    return result

def download_file(url, dest):
    """Download a file from a URL to a destination"""
    print(f"Downloading {url} to {dest}")
    
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    # Download the file
    urllib.request.urlretrieve(url, dest)
    
    print(f"Downloaded {url}")

def extract_zip(zip_path, extract_to):
    """Extract a zip file to a destination"""
    print(f"Extracting {zip_path} to {extract_to}")
    
    # Create the destination directory if it doesn't exist
    os.makedirs(extract_to, exist_ok=True)
    
    # Extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    print(f"Extracted {zip_path}")

def setup_environment():
    """Set up the build environment"""
    print("Setting up build environment...")
    
    # Create directories
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(EMBEDDED_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    # Download PostHog source code if it doesn't exist
    if not POSTHOG_DIR.exists():
        posthog_zip = BUILD_DIR / "posthog.zip"
        download_file(POSTHOG_URL, posthog_zip)
        extract_zip(posthog_zip, ".")
    
    # Download Node.js
    node_zip = BUILD_DIR / "node.zip"
    download_file(NODE_URL, node_zip)
    node_dir = EMBEDDED_DIR / "node"
    if node_dir.exists():
        shutil.rmtree(node_dir)
    extract_zip(node_zip, EMBEDDED_DIR)
    # Move the contents from the nested directory to node_dir
    node_extracted = list(EMBEDDED_DIR.glob("node-v*-win-x64"))[0]
    shutil.move(str(node_extracted), str(node_dir))
    
    # Download Python
    python_zip = BUILD_DIR / "python.zip"
    download_file(PYTHON_URL, python_zip)
    python_dir = EMBEDDED_DIR / "python"
    if python_dir.exists():
        shutil.rmtree(python_dir)
    os.makedirs(python_dir, exist_ok=True)
    extract_zip(python_zip, python_dir)
    
    # Download Inno Setup
    inno_setup_exe = BUILD_DIR / "innosetup.exe"
    download_file(INNO_SETUP_URL, inno_setup_exe)
    
    # Install Inno Setup (silently)
    run_command(f'"{inno_setup_exe}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART')
    
    print("Environment setup complete")

def copy_posthog_files():
    """Copy necessary PostHog files to the distribution directory"""
    print("Copying PostHog files...")
    
    # Copy the main PostHog files
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # Copy launcher scripts
    shutil.copy("standalone_launcher.py", DIST_DIR)
    shutil.copy("posthog.bat", DIST_DIR)
    
    # Copy PostHog Python files
    posthog_dir = DIST_DIR / "posthog"
    os.makedirs(posthog_dir, exist_ok=True)
    shutil.copytree(POSTHOG_DIR / "posthog", posthog_dir, dirs_exist_ok=True)
    
    # Copy Django management scripts
    shutil.copy(POSTHOG_DIR / "manage.py", DIST_DIR)
    
    # Copy frontend assets
    frontend_dist = DIST_DIR / "frontend" / "dist"
    os.makedirs(frontend_dist, exist_ok=True)
    shutil.copytree(POSTHOG_DIR / "frontend" / "dist", frontend_dist, dirs_exist_ok=True)
    
    # Copy plugin server
    plugin_server = DIST_DIR / "plugin-server"
    os.makedirs(plugin_server, exist_ok=True)
    shutil.copytree(POSTHOG_DIR / "plugin-server" / "dist", plugin_server / "dist", dirs_exist_ok=True)
    shutil.copytree(POSTHOG_DIR / "plugin-server" / "node_modules", plugin_server / "node_modules", dirs_exist_ok=True)
    
    # Create data directory
    data_dir = DIST_DIR / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print("PostHog files copied")

def install_python_dependencies():
    """Install Python dependencies to the embedded Python"""
    print("Installing Python dependencies...")
    
    # Create a requirements file with the necessary dependencies
    requirements = [
        "Django~=4.2.17",
        "dj-database-url==0.5.0",
        "whitenoise==6.5.0",
        "django-cors-headers==3.5.0",
        "djangorestframework==3.15.1",
        "celery==5.3.4",
        "fakeredis[lua]==2.23.3",
        "psycopg2-binary==2.9.7",
        "python-dateutil>=2.8.2",
        "sentry-sdk~=1.44.1",
        "requests~=2.32.3",
        "pillow==10.2.0",
    ]
    
    with open(BUILD_DIR / "requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    # Install pip to the embedded Python
    python_dir = EMBEDDED_DIR / "python"
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = BUILD_DIR / "get-pip.py"
    download_file(get_pip_url, get_pip_path)
    
    # Run get-pip.py with the embedded Python
    python_exe = python_dir / "python.exe"
    run_command(f'"{python_exe}" "{get_pip_path}"')
    
    # Install the requirements
    run_command(f'"{python_dir / "Scripts" / "pip.exe"}" install -r "{BUILD_DIR / "requirements.txt"}" --no-warn-script-location')
    
    print("Python dependencies installed")

def create_license_file():
    """Create a license file for the installer"""
    license_content = """PostHog Windows Standalone Edition

Copyright (c) 2020-present PostHog Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open("LICENSE.txt", "w") as f:
        f.write(license_content)
    
    print("License file created")

def build_installer():
    """Build the Windows installer with Inno Setup"""
    print("Building Windows installer...")
    
    # Find Inno Setup compiler
    inno_compiler = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(inno_compiler):
        print("Inno Setup compiler not found at the expected location.")
        print("Please install Inno Setup 6 and make sure it's installed in the default location.")
        return False
    
    # Run the compiler
    run_command(f'"{inno_compiler}" posthog_installer.iss')
    
    print("Installer built successfully!")
    return True

def main():
    print("Building PostHog Windows Standalone Executable")
    
    try:
        setup_environment()
        copy_posthog_files()
        install_python_dependencies()
        create_license_file()
        
        if build_installer():
            print("\nBuild completed successfully!")
            print(f"The installer is available at: {OUTPUT_DIR / 'posthog-windows-setup.exe'}")
        else:
            print("\nBuild failed to create the installer. See errors above.")
    except Exception as e:
        print(f"Error during build: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 