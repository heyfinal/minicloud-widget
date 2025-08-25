#!/bin/bash

echo "🖥️ MiniCloud Monitor Widget Installer"
echo "====================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

# Install rumps for menu bar app
echo "📦 Installing dependencies..."
pip3 install --user rumps requests

# Make the script executable
chmod +x minicloud_monitor.py

# Create launch agent for auto-start
echo "🚀 Setting up auto-start..."
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.minicloud.monitor.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minicloud.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$PWD/minicloud_monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardErrorPath</key>
    <string>/tmp/minicloud-monitor.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/minicloud-monitor.out</string>
</dict>
</plist>
EOF

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.minicloud.monitor.plist 2>/dev/null

echo ""
echo "✅ Installation complete!"
echo ""
echo "📊 MiniCloud Monitor is now running in your menu bar"
echo ""
echo "Features:"
echo "  • Real-time CPU, Memory, and Disk monitoring"
echo "  • Quick access to Grafana dashboards"
echo "  • Direct links to Nextcloud and Prometheus"
echo "  • Auto-updates every 30 seconds"
echo ""
echo "To manually start the widget:"
echo "  python3 minicloud_monitor.py"
echo ""
echo "To stop the widget:"
echo "  launchctl unload ~/Library/LaunchAgents/com.minicloud.monitor.plist"
echo ""
echo "Enjoy monitoring your miniCLOUD! ☁️"