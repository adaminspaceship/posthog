#!/usr/bin/env python
# PostHog Windows Standalone Launcher
# This script launches PostHog with bundled Python and Node.js runtimes

import os
import sys
import subprocess
import webbrowser
import time
import atexit
import signal
import threading
import json
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='posthog_launcher.log'
)
logger = logging.getLogger('posthog_launcher')

# Get the base directory
base_dir = os.path.abspath(os.path.dirname(__file__))
logger.info(f"Base directory: {base_dir}")

# Add bundled Python to path
python_dir = os.path.join(base_dir, "python")
os.environ["PATH"] = f"{python_dir};{os.environ['PATH']}"
os.environ["PYTHONHOME"] = python_dir
os.environ["PYTHONPATH"] = os.path.join(python_dir, "Lib")
sys.path.insert(0, os.path.join(python_dir, "Lib"))
sys.path.insert(0, os.path.join(python_dir, "Lib", "site-packages"))
sys.path.insert(0, base_dir)

# Node.js executable path
node_exe = os.path.join(base_dir, "node", "node.exe")

# Application paths
manage_py = os.path.join(base_dir, "manage.py")
plugin_server_path = os.path.join(base_dir, "plugin-server", "dist", "index.js")
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# Set environment variables
os.environ['DEBUG'] = '0'
os.environ['DATABASE_URL'] = f'sqlite:///{os.path.join(data_dir, "posthog.db")}'
os.environ['REDIS_URL'] = ''  # Will use a fake Redis implementation
os.environ['SECRET_KEY'] = 'windows_standalone_secret_key'
os.environ['DISABLE_SECURE_SSL_REDIRECT'] = '1'
os.environ['SKIP_SERVICE_VERSION_REQUIREMENTS'] = '1'
os.environ['POSTHOG_PLUGIN_SERVER_STARTUP_RETRY_COUNT'] = '0'
os.environ['SITE_URL'] = 'http://localhost:8000'
os.environ['ALLOWED_HOSTS'] = '*'
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['CLICKHOUSE_ENABLED'] = 'false'
os.environ['KAFKA_ENABLED'] = 'false'

# Initialize services
processes = []

def create_default_config():
    """Create default configuration if it doesn't exist"""
    config_path = os.path.join(data_dir, "config.json")
    if not os.path.exists(config_path):
        default_config = {
            "first_run": True,
            "port": 8000,
            "initialized": False
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f)
        return default_config
    
    with open(config_path, 'r') as f:
        return json.load(f)

def initialize_database():
    """Initialize the SQLite database if it doesn't exist"""
    db_path = os.path.join(data_dir, "posthog.db")
    if not os.path.exists(db_path):
        logger.info("Initializing database...")
        try:
            # Create an empty database file
            conn = sqlite3.connect(db_path)
            conn.close()
            logger.info("Database initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    return True

def run_django_command(command):
    """Run a Django management command"""
    logger.info(f"Running Django command: {command}")
    try:
        cmd = [sys.executable, manage_py] + command.split()
        result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        logger.info(f"Command output: {result.stdout.decode()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e.stderr.decode()}")
        return False

def start_django():
    """Start the Django web server"""
    logger.info("Starting Django web server...")
    try:
        run_django_command("migrate --noinput")
        run_django_command("runserver 0.0.0.0:8000")
    except Exception as e:
        logger.error(f"Error starting Django: {e}")

def start_plugin_server():
    """Start the plugin server"""
    logger.info("Starting plugin server...")
    try:
        process = subprocess.Popen(
            [node_exe, plugin_server_path],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(process)
        return process
    except Exception as e:
        logger.error(f"Error starting plugin server: {e}")
        return None

def start_worker():
    """Start a minimal worker"""
    logger.info("Starting worker...")
    try:
        run_django_command("celery worker --loglevel=info")
    except Exception as e:
        logger.error(f"Error starting worker: {e}")

def cleanup():
    """Clean up all processes on exit"""
    logger.info("Cleaning up processes...")
    for process in processes:
        try:
            process.terminate()
            logger.info(f"Terminated process {process.pid}")
        except:
            logger.error(f"Failed to terminate process")

def main():
    """Main entry point"""
    logger.info("Starting PostHog services...")
    print("Starting PostHog... (this may take a minute)")
    print("Check posthog_launcher.log for detailed logs")
    
    # Create default configuration
    config = create_default_config()
    
    # Initialize database
    if not initialize_database():
        print("Failed to initialize database. See log for details.")
        return
    
    # Register cleanup handler
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    
    # Start plugin server in a separate process
    plugin_server = start_plugin_server()
    if not plugin_server:
        print("Failed to start plugin server. See log for details.")
    
    # Start worker in a thread
    worker_thread = threading.Thread(target=start_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait for services to initialize
    time.sleep(5)
    print("Opening browser...")
    
    # Open browser
    webbrowser.open('http://localhost:8000')
    
    # Start Django in the main thread
    start_django()

if __name__ == '__main__':
    main() 