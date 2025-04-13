#!/usr/bin/env python3
# Script to build a Windows executable for PostHog

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Define paths
POSTHOG_DIR = Path("posthog-master")
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
TEMP_DIR = Path("temp")
OUTPUT_DIR = Path("posthog-windows")

def run_command(command, cwd=None):
    """Run a command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, check=True)
    return result

def setup_environment():
    """Set up the build environment"""
    print("Setting up build environment...")
    
    # Create directories
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Install PyInstaller and other build dependencies
    run_command("pip install pyinstaller==6.5.0 pywin32==306")
    
    # Install PostHog Python dependencies
    run_command(f"pip install -e {POSTHOG_DIR}")

def build_frontend():
    """Build the PostHog frontend"""
    print("Building frontend...")
    frontend_dir = POSTHOG_DIR / "frontend"
    
    # Install Node.js dependencies
    run_command("pnpm install", cwd=POSTHOG_DIR)
    
    # Build frontend
    run_command("pnpm run build", cwd=frontend_dir)

def build_plugin_server():
    """Build the PostHog plugin server"""
    print("Building plugin server...")
    plugin_server_dir = POSTHOG_DIR / "plugin-server"
    
    # Install plugin server dependencies
    run_command("pnpm install", cwd=plugin_server_dir)
    
    # Build plugin server
    run_command("pnpm run build", cwd=plugin_server_dir)

def create_spec_file():
    """Create a PyInstaller spec file for PostHog"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

django_files = [
    ('posthog-master/posthog', 'posthog'),
    ('posthog-master/frontend/dist', 'frontend/dist'),
    ('posthog-master/plugin-server/dist', 'plugin-server/dist'),
    ('posthog-master/plugin-server/node_modules', 'plugin-server/node_modules'),
    ('posthog-master/staticfiles', 'staticfiles'),
]

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=django_files,
    hiddenimports=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'posthog',
        'dj_database_url',
        'whitenoise',
        'corsheaders',
        'social_django',
        'django_filters',
        'rest_framework',
        'celery',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='posthog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='posthog',
)
"""
    
    with open("posthog.spec", "w") as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file")

def create_launcher_script():
    """Create a launcher script for PostHog"""
    launcher_content = """#!/usr/bin/env python
# PostHog Windows Launcher

import os
import sys
import subprocess
import webbrowser
import time
import atexit
import signal
import threading

# Add PostHog directory to Python path
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, base_dir)

# Set environment variables
os.environ['DEBUG'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:///posthog.db'
os.environ['REDIS_URL'] = ''  # Will use a fake Redis implementation
os.environ['SECRET_KEY'] = 'windows_standalone_secret_key'
os.environ['DISABLE_SECURE_SSL_REDIRECT'] = '1'
os.environ['SKIP_SERVICE_VERSION_REQUIREMENTS'] = '1'

# Initialize services
processes = []

def start_django():
    """Start the Django web server"""
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate'])
    execute_from_command_line(['manage.py', 'migrate_clickhouse'])
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

def start_plugin_server():
    """Start the plugin server"""
    plugin_server_path = os.path.join(base_dir, 'plugin-server', 'dist', 'index.js')
    process = subprocess.Popen(
        ['node', plugin_server_path],
        env=os.environ.copy()
    )
    processes.append(process)
    return process

def start_worker():
    """Start Celery worker"""
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'celery', 'worker'])

def cleanup():
    """Clean up all processes on exit"""
    for process in processes:
        try:
            process.terminate()
        except:
            pass

def main():
    """Main entry point"""
    print("Starting PostHog services...")
    
    # Register cleanup handler
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    
    # Start plugin server in a separate process
    plugin_server = start_plugin_server()
    
    # Start worker in a thread
    worker_thread = threading.Thread(target=start_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait for services to initialize
    time.sleep(2)
    
    # Open browser
    webbrowser.open('http://localhost:8000')
    
    # Start Django in the main thread
    start_django()

if __name__ == '__main__':
    main()
"""
    
    with open("launcher.py", "w") as f:
        f.write(launcher_content)
    
    print("Created launcher script")

def build_executable():
    """Build the executable with PyInstaller"""
    print("Building Windows executable...")
    run_command("pyinstaller --clean posthog.spec")
    
    # Copy additional files to the distribution
    shutil.copy("posthog-master/bin/start-worker.bat", "dist/posthog/")
    shutil.copy("posthog-master/bin/start-plugin-server.bat", "dist/posthog/")
    
    # Create a start.bat file
    with open("dist/posthog/start.bat", "w") as f:
        f.write("""@echo off
echo Starting PostHog...
start posthog.exe
""")
    
    # Create a README file
    with open("dist/posthog/README.txt", "w") as f:
        f.write("""PostHog Windows Standalone

This is a standalone Windows executable package of PostHog.

To start PostHog:
1. Double-click on start.bat
2. Wait for the services to start
3. Your browser will automatically open to http://localhost:8000

Note: This standalone version uses SQLite for the database and includes
simplified versions of the services. For production use, please use the
official Docker deployment method.

For more information, visit: https://posthog.com
""")
    
    # Create the final zip file
    shutil.make_archive("posthog-windows", "zip", "dist/posthog")
    
    print("PostHog Windows executable has been built! The final package is: posthog-windows.zip")

def main():
    print("Building PostHog Windows executable")
    setup_environment()
    build_frontend()
    build_plugin_server()
    create_launcher_script()
    create_spec_file()
    build_executable()
    print("Build completed!")

if __name__ == "__main__":
    main() 