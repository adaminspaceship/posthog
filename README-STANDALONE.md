# PostHog Windows Standalone Installer

This project creates a completely standalone, offline Windows installer for PostHog. The installer bundles everything needed to run PostHog on a Windows machine without requiring any external dependencies or internet connection.

## For Users: Running PostHog Offline

### System Requirements
- Windows 10 or 11 (64-bit)
- 4GB RAM minimum (8GB recommended)
- 2GB of free disk space
- Administrator privileges

### Installation
1. Download the `posthog-windows-setup.exe` installer
2. Run the installer and follow the prompts
3. The installer will create a PostHog program group in your Start menu

### Starting PostHog
1. Launch PostHog from the Start menu
2. A command prompt window will open showing the startup progress
3. Your web browser will automatically open to http://localhost:8000
4. Complete the initial setup in your browser

### Important Notes
- The standalone version uses SQLite instead of PostgreSQL/ClickHouse (suitable for personal use but not for high-volume production use)
- All data is stored locally in the installation directory
- No internet connection is required

## For Developers: Building the Installer

### Requirements
- Windows 10 or 11 (64-bit)
- Python 3.8 or higher
- Internet connection (only needed during the build process)

### Building Steps
1. Clone this repository
2. Run the build script:
   ```
   python build_standalone.py
   ```
3. The script will:
   - Download and prepare bundled versions of Python and Node.js
   - Download the PostHog source code
   - Install and configure all dependencies
   - Build the necessary components
   - Create an installer with Inno Setup

4. After successful completion, the installer will be available in the `output` directory

### What's Included in the Build
- Embedded Python 3.11 runtime
- Embedded Node.js 18.19.1 runtime
- PostHog Django application
- PostHog frontend assets
- PostHog plugin server
- SQLite database
- All required dependencies

## Limitations

This standalone version has some limitations compared to the full PostHog deployment:

- Uses SQLite instead of PostgreSQL and ClickHouse (limited scalability)
- No plugin marketplace functionality
- Limited support for event exports/imports
- No multi-server deployment capability
- Maximum practical event volume is lower than the full stack

For production-scale deployments with high volumes of data, consider using the official Docker deployment method instead. 