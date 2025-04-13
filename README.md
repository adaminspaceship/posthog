# PostHog Windows Executable Builder

This project creates a standalone Windows executable for PostHog, allowing you to run PostHog without Docker or complex setup.

## Requirements

- Windows 10/11 64-bit
- Python 3.11
- Node.js 18.x
- PNPM package manager

## Setup

1. Install the required software:
   - Python 3.11: https://www.python.org/downloads/
   - Node.js 18.x: https://nodejs.org/
   - PNPM: Run `npm install -g pnpm` after installing Node.js

2. Clone the PostHog repository:
   ```
   git clone https://github.com/PostHog/posthog.git posthog-master
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Building the Executable

Run the build script:
```
python build_windows_exe.py
```

The build process will:
1. Install required dependencies
2. Build the PostHog frontend
3. Build the plugin server
4. Package everything into a Windows executable

When completed, you'll find a `posthog-windows.zip` file in the current directory.

## Using the PostHog Windows Executable

1. Extract the `posthog-windows.zip` archive
2. Run `start.bat` to start PostHog
3. Your browser will automatically open to http://localhost:8000
4. Complete the setup process in the browser

## Notes

- This standalone version uses SQLite for the database, which is suitable for testing but not recommended for production use
- For production environments, consider using the official Docker deployment method
- The executable includes a simplified version of PostHog with core functionality

## Limitations

- No ClickHouse integration (using SQLite instead)
- Limited plugin functionality
- No event exports/imports
- Reduced performance compared to the full deployment

## Troubleshooting

- If you encounter any issues, check the console window for error messages
- Make sure you have sufficient permissions to run executables and access the internet
- For database issues, try deleting the `posthog.db` file and restarting the application 