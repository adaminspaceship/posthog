# PowerShell script to add a Windows Firewall exception for PostHog

# Remove existing rule if it exists
Remove-NetFirewallRule -DisplayName "PostHog" -ErrorAction SilentlyContinue

# Add a new firewall rule for inbound traffic on port 8000
New-NetFirewallRule -DisplayName "PostHog" `
                    -Direction Inbound `
                    -Protocol TCP `
                    -LocalPort 8000 `
                    -Action Allow `
                    -Program "$PSScriptRoot\..\posthog.exe" `
                    -Description "Allow inbound traffic for PostHog on port 8000" 