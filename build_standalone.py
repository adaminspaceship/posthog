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
    
    # Rename extracted root folder if necessary (e.g., posthog-master-HASH to posthog-master)
    extracted_dirs = [d for d in Path(extract_to).iterdir() if d.is_dir() and 'posthog-' in d.name]
    if len(extracted_dirs) == 1 and extracted_dirs[0].name != POSTHOG_DIR.name:
        print(f"Renaming {extracted_dirs[0]} to {POSTHOG_DIR}")
        extracted_dirs[0].rename(POSTHOG_DIR)
    
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
        # Extract to a temporary place to handle potential root folder naming
        temp_extract_dir = BUILD_DIR / "posthog_extract"
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        extract_zip(posthog_zip, temp_extract_dir)
        # Find the actual source folder (e.g., posthog-master)
        extracted_src = next(temp_extract_dir.iterdir()) # Assume only one folder inside
        if POSTHOG_DIR.exists():
             shutil.rmtree(POSTHOG_DIR)
        shutil.move(str(extracted_src), str(POSTHOG_DIR))
        shutil.rmtree(temp_extract_dir)
    
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

def build_posthog_components():
    """Build PostHog frontend and plugin server"""
    print("Building PostHog components...")
    
    # Install Node.js dependencies (removed --frozen-lockfile)
    run_command("pnpm install", cwd=POSTHOG_DIR)
    
    # Build frontend
    print("Building frontend...")
    run_command("pnpm --filter=@posthog/frontend build", cwd=POSTHOG_DIR)
    
    # Build plugin server
    print("Building plugin server...")
    run_command("pnpm --filter=@posthog/plugin-server build", cwd=POSTHOG_DIR)
    
    print("PostHog components built successfully")

def copy_posthog_files():
    """Copy necessary PostHog files to the distribution directory"""
    print("Copying PostHog files...")
    
    # Ensure dist dir exists
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # Copy launcher scripts
    shutil.copy("standalone_launcher.py", DIST_DIR)
    shutil.copy("posthog.bat", DIST_DIR)
    
    # Copy PostHog Python files
    posthog_py_dir = DIST_DIR / "posthog"
    if posthog_py_dir.exists(): shutil.rmtree(posthog_py_dir)
    shutil.copytree(POSTHOG_DIR / "posthog", posthog_py_dir, dirs_exist_ok=True)
    
    # Copy common Python files
    common_dir = DIST_DIR / "common"
    if common_dir.exists(): shutil.rmtree(common_dir)
    shutil.copytree(POSTHOG_DIR / "common", common_dir, dirs_exist_ok=True)

    # Copy products Python files
    products_dir = DIST_DIR / "products"
    if products_dir.exists(): shutil.rmtree(products_dir)
    shutil.copytree(POSTHOG_DIR / "products", products_dir, dirs_exist_ok=True)

    # Copy Django management scripts
    shutil.copy(POSTHOG_DIR / "manage.py", DIST_DIR)
    
    # Copy frontend assets
    frontend_dist_src = POSTHOG_DIR / "frontend" / "dist"
    frontend_dist_dest = DIST_DIR / "frontend" / "dist"
    if not frontend_dist_src.exists():
        raise FileNotFoundError(f"Frontend dist directory not found: {frontend_dist_src}")
    if frontend_dist_dest.exists(): shutil.rmtree(frontend_dist_dest.parent)
    os.makedirs(frontend_dist_dest.parent, exist_ok=True)
    shutil.copytree(frontend_dist_src, frontend_dist_dest, dirs_exist_ok=True)
    
    # Copy plugin server
    plugin_server_src = POSTHOG_DIR / "plugin-server"
    plugin_server_dest = DIST_DIR / "plugin-server"
    if plugin_server_dest.exists(): shutil.rmtree(plugin_server_dest)
    os.makedirs(plugin_server_dest, exist_ok=True)
    # Copy dist
    plugin_dist_src = plugin_server_src / "dist"
    plugin_dist_dest = plugin_server_dest / "dist"
    if not plugin_dist_src.exists():
        raise FileNotFoundError(f"Plugin server dist directory not found: {plugin_dist_src}")
    shutil.copytree(plugin_dist_src, plugin_dist_dest, dirs_exist_ok=True)
    # Copy node_modules (only production dependencies)
    print("Installing production Node.js dependencies for plugin server...")
    # Also remove --frozen-lockfile here for consistency
    run_command("pnpm install --prod", cwd=plugin_server_src) 
    plugin_node_modules_src = plugin_server_src / "node_modules"
    plugin_node_modules_dest = plugin_server_dest / "node_modules"
    shutil.copytree(plugin_node_modules_src, plugin_node_modules_dest, dirs_exist_ok=True)
    # Copy package.json
    shutil.copy(plugin_server_src / "package.json", plugin_server_dest)

    # Copy other necessary root files
    for item in ["pyproject.toml", "pnpm-lock.yaml", "pnpm-workspace.yaml", "uv.lock"]:
        if (POSTHOG_DIR / item).exists():
             shutil.copy(POSTHOG_DIR / item, DIST_DIR)

    # Create data directory
    data_dir = DIST_DIR / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    print("PostHog files copied")

def install_python_dependencies():
    """Install Python dependencies to the embedded Python"""
    print("Installing Python dependencies...")
    
    # Use uv if available, otherwise pip
    python_dir = EMBEDDED_DIR / "python"
    python_exe = python_dir / "python.exe"
    pip_exe = python_dir / "Scripts" / "pip.exe"
    uv_exe = python_dir / "Scripts" / "uv.exe"

    # Ensure pip is installed
    if not pip_exe.exists():
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = BUILD_DIR / "get-pip.py"
        download_file(get_pip_url, get_pip_path)
        run_command(f'"{python_exe}" "{get_pip_path}"')
        # Install uv
        run_command(f'"{pip_exe}" install uv')

    # Install the requirements from PostHog's requirements.txt
    # Assuming PostHog maintains a requirements.txt for broader compatibility
    requirements_path = POSTHOG_DIR / "requirements.txt"
    if not requirements_path.exists():
        print(f"Warning: {requirements_path} not found. Attempting install via pyproject.toml/uv.lock")
        # This might fail if the lock file isn't present or compatible in the zip download
        run_command(f'"{uv_exe}" sync --frozen --no-dev --system --python "{python_exe}"', cwd=DIST_DIR)
    else:
        print("Installing Python dependencies using uv from requirements.txt...")
        run_command(f'"{uv_exe}" pip install -r "{requirements_path}" --system --python "{python_exe}"', cwd=DIST_DIR)
    
    print("Python dependencies installed")

def create_license_file():
    """Create a license file for the installer"""
    print("Creating license file...")
    license_src = POSTHOG_DIR / "LICENSE"
    if license_src.exists():
        shutil.copy(license_src, "LICENSE.txt")
        print("Copied PostHog LICENSE file")
    else:
        # Fallback license content
        license_content = """PostHog Windows Standalone Edition

Copyright (c) 2020-present PostHog Inc.

This software is based on the PostHog open-source project, available under the MIT license.
See the original license at: https://github.com/PostHog/posthog/blob/master/LICENSE

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
        print("Created fallback license file")

def build_installer():
    """Build the Windows installer with Inno Setup"""
    print("Building Windows installer...")
    
    # Find Inno Setup compiler
    inno_compiler_path = Path("C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    if not inno_compiler_path.exists():
        print(f"Inno Setup compiler not found at: {inno_compiler_path}")
        print("Please install Inno Setup 6 or ensure it's in the default location.")
        return False
    
    # Run the compiler
    run_command(f'"{inno_compiler_path}" posthog_installer.iss')
    
    print("Installer built successfully!")
    return True

def main():
    print("Building PostHog Windows Standalone Executable")
    
    try:
        setup_environment()
        build_posthog_components()
        copy_posthog_files()
        install_python_dependencies()
        create_license_file()
        
        if build_installer():
            print("\nBuild completed successfully!")
            print(f"The installer is available at: {OUTPUT_DIR / 'posthog-windows-setup.exe'}")
        else:
            print("\nBuild failed to create the installer. See errors above.")
    except Exception as e:
        print(f"\nError during build: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 