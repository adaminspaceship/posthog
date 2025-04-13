// Helper script for building PostHog Windows Executable
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const fetch = require('node-fetch');
const AdmZip = require('adm-zip');

// Configuration
const config = {
  posthogDir: 'posthog-master',
  nodeVersion: '18.19.1',
  pythonVersion: '3.11.9',
};

// Helper to run a command
async function runCommand(command, args, cwd = process.cwd()) {
  return new Promise((resolve, reject) => {
    console.log(`Running: ${command} ${args.join(' ')}`);
    
    const proc = spawn(command, args, { 
      cwd, 
      stdio: 'inherit',
      shell: process.platform === 'win32'
    });
    
    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Command failed with code ${code}`));
      } else {
        resolve();
      }
    });
  });
}

// Check if PostHog directory exists
async function checkPostHogDir() {
  if (!fs.existsSync(config.posthogDir)) {
    console.log(`PostHog directory not found: ${config.posthogDir}`);
    console.log('Downloading PostHog source code...');
    
    try {
      const response = await fetch('https://github.com/PostHog/posthog/archive/refs/heads/master.zip');
      const buffer = await response.buffer();
      
      fs.writeFileSync('posthog.zip', buffer);
      
      const zip = new AdmZip('posthog.zip');
      zip.extractAllTo('./', true);
      
      console.log('PostHog source code downloaded and extracted');
    } catch (error) {
      console.error('Failed to download PostHog source code', error);
      process.exit(1);
    }
  }
}

// Install Node.js dependencies
async function installNodeDependencies() {
  console.log('Installing Node.js dependencies...');
  
  try {
    await runCommand('pnpm', ['install', '--frozen-lockfile'], config.posthogDir);
  } catch (error) {
    console.error('Failed to install Node.js dependencies', error);
    process.exit(1);
  }
}

// Prepare the build environment
async function prepareBuild() {
  // Create directories
  ['build', 'dist', 'temp'].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir);
    }
  });
  
  // Create simplified settings file for PostHog
  const settingsPath = path.join(config.posthogDir, 'posthog', 'local_settings.py');
  const settingsContent = `
from posthog.settings import *

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'posthog.db'),
    }
}

# Disable services that won't work in the Windows executable
CLICKHOUSE_ENABLED = False
KAFKA_ENABLED = False
PLUGINS_PREINSTALLED_URLS = []
PLUGINS_INSTALL_VIA_API = False
SITE_URL = 'http://localhost:8000'
CORS_ORIGIN_ALLOW_ALL = True
`;

  fs.writeFileSync(settingsPath, settingsContent);
  console.log('Created local settings file');
}

// Main function
async function main() {
  console.log('PostHog Windows Executable Builder - Node.js Helper');
  
  try {
    await checkPostHogDir();
    await installNodeDependencies();
    await prepareBuild();
    
    console.log('Node.js build preparation completed');
  } catch (error) {
    console.error('Build process failed', error);
    process.exit(1);
  }
}

main(); 