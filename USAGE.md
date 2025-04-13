# PostHog Windows Executable - Usage Guide

This guide explains how to use the PostHog Windows executable after building it.

## System Requirements

- Windows 10 or Windows 11 (64-bit)
- Minimum 4GB RAM (8GB recommended)
- 2GB free disk space
- Administrator privileges

## Installation

1. Extract the `posthog-windows.zip` file to a location of your choice
2. The extracted folder contains all the necessary files to run PostHog

## Starting PostHog

1. Navigate to the extracted folder
2. Double-click on `start.bat` to start the PostHog application
3. A command prompt window will open showing startup progress
4. Your web browser will automatically open to http://localhost:8000
5. If the browser doesn't open automatically, open it manually and navigate to http://localhost:8000

## First-Time Setup

When you first access PostHog, you'll need to create an admin account:

1. Fill out the registration form with your details
2. Create a strong password
3. Complete the initial configuration

## Basic Usage

### Tracking Events

To start tracking events from your website:

1. Go to "Project Settings" > "Setup" in the PostHog interface
2. Copy the JavaScript snippet
3. Add the snippet to your website's HTML

### Viewing Data

- Dashboard: Overview of your analytics data
- Insights: Create custom charts and visualizations
- Session Recordings: Watch user sessions
- Feature Flags: Control feature rollouts

## Stopping PostHog

To stop the PostHog application:

1. Go to the command prompt window that opened when you started PostHog
2. Press `Ctrl+C` to stop the application
3. Confirm with `Y` if prompted

## Troubleshooting

### Application Won't Start

- Make sure you have administrator privileges
- Check that no other application is using port 8000
- Try running `posthog.exe` directly from the command line for more detailed error messages

### Database Issues

If you encounter database errors:

1. Close the PostHog application
2. Delete the `posthog.db` file from the installation directory
3. Restart the application (this will create a fresh database)

### Browser Can't Connect

If your browser can't connect to http://localhost:8000:

1. Make sure PostHog is running (check the command prompt window)
2. Try accessing it via http://127.0.0.1:8000 instead
3. Check if your firewall is blocking the connection

## Limitations

This standalone Windows executable has some limitations compared to the full PostHog deployment:

- Uses SQLite instead of PostgreSQL and ClickHouse (limited performance for high event volumes)
- No plugin marketplace functionality
- Limited support for event exports/imports
- No support for multi-server deployment

For production use with high volumes of data, consider using the official Docker deployment method. 