#!/bin/bash
#
# MiniCloud AI Recovery System - Installer
# Installs and configures the complete monitoring and recovery solution
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/minicloud-widget"
CONFIG_DIR="$HOME/.minicloud"
NEURALSYNC_DIR="$HOME/NeuralSync2"
VENV_DIR="$INSTALL_DIR/.venv"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     MiniCloud AI Recovery System - Installation Wizard      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Function to print status
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python 3.9+
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

# Check for pip
if ! python3 -m pip --version &> /dev/null; then
    print_warning "pip not found, installing..."
    python3 -m ensurepip --upgrade
fi
print_success "pip is available"

# Create directories
print_status "Creating directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$INSTALL_DIR"
print_success "Directories created"

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip wheel setuptools &> /dev/null

# Create requirements file
cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
rumps>=0.4.0
requests>=2.28.0
psutil>=5.9.0
pyyaml>=6.0
aiohttp>=3.8.0
asyncio>=3.4.3
paramiko>=3.0.0
cryptography>=40.0.0
EOF

pip install -r "$INSTALL_DIR/requirements.txt" &> /dev/null
print_success "Dependencies installed"

# Make scripts executable
print_status "Setting up executables..."
chmod +x "$INSTALL_DIR/minicloud_monitor_enhanced.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/minicloud_ai_recovery.py" 2>/dev/null || true
chmod +x "$NEURALSYNC_DIR/bin/claude-ns-fixed" 2>/dev/null || true
print_success "Executables configured"

# Fix claude-ns if it exists
if [ -f "$HOME/.local/bin/claude-ns" ]; then
    print_status "Fixing claude-ns launcher..."
    
    # Backup original
    if [ ! -f "$HOME/.local/bin/claude-ns.backup" ]; then
        cp "$HOME/.local/bin/claude-ns" "$HOME/.local/bin/claude-ns.backup"
    fi
    
    # Replace with fixed version
    if [ -f "$NEURALSYNC_DIR/bin/claude-ns-fixed" ]; then
        cp "$NEURALSYNC_DIR/bin/claude-ns-fixed" "$HOME/.local/bin/claude-ns"
        chmod +x "$HOME/.local/bin/claude-ns"
        print_success "claude-ns fixed"
    else
        print_warning "Fixed claude-ns script not found"
    fi
else
    print_warning "claude-ns not installed yet"
fi

# Configure AI Recovery
print_status "Configuring AI Recovery System..."

# Get server details
echo
echo -e "${YELLOW}Server Configuration:${NC}"
read -p "Enter MiniCloud server IP [192.168.1.93]: " SERVER_IP
SERVER_IP=${SERVER_IP:-192.168.1.93}

read -p "Enter SSH username [admin]: " SSH_USER
SSH_USER=${SSH_USER:-admin}

read -p "Enter SSH key path [~/.ssh/id_rsa]: " SSH_KEY
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

# Expand tilde in path
SSH_KEY="${SSH_KEY/#\~/$HOME}"

# Test SSH connection
print_status "Testing SSH connection..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "echo 'Connection successful'" &> /dev/null; then
    print_success "SSH connection successful"
else
    print_warning "SSH connection failed - please configure manually"
fi

# Create AI recovery config
cat > "$CONFIG_DIR/ai_recovery_config.json" << EOF
{
  "server": {
    "ip": "$SERVER_IP",
    "ssh_user": "$SSH_USER",
    "ssh_key": "$SSH_KEY",
    "prometheus_url": "http://$SERVER_IP:9091",
    "grafana_url": "http://$SERVER_IP:3000"
  },
  "thresholds": {
    "cpu_warning": 70,
    "cpu_critical": 90,
    "memory_warning": 80,
    "memory_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90,
    "network_latency_high": 1000
  },
  "monitoring": {
    "check_interval": 30,
    "recovery_cooldown": 300,
    "max_recovery_attempts": 3
  },
  "notifications": {
    "enabled": true
  }
}
EOF
print_success "AI recovery configured"

# Create launcher scripts
print_status "Creating launcher scripts..."

# Widget launcher
cat > "$INSTALL_DIR/start_widget.sh" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
python3 "$INSTALL_DIR/minicloud_monitor_enhanced.py"
EOF
chmod +x "$INSTALL_DIR/start_widget.sh"

# AI Recovery launcher
cat > "$INSTALL_DIR/start_ai_recovery.sh" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
python3 "$INSTALL_DIR/minicloud_ai_recovery.py"
EOF
chmod +x "$INSTALL_DIR/start_ai_recovery.sh"

print_success "Launcher scripts created"

# Create macOS LaunchAgent for auto-start
print_status "Setting up auto-start..."

LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENT_DIR"

# Widget LaunchAgent
cat > "$LAUNCH_AGENT_DIR/com.minicloud.monitor.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minicloud.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/start_widget.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardErrorPath</key>
    <string>$CONFIG_DIR/widget_error.log</string>
    <key>StandardOutPath</key>
    <string>$CONFIG_DIR/widget_output.log</string>
</dict>
</plist>
EOF

# AI Recovery LaunchAgent
cat > "$LAUNCH_AGENT_DIR/com.minicloud.airecovery.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.minicloud.airecovery</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/start_ai_recovery.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardErrorPath</key>
    <string>$CONFIG_DIR/ai_recovery_error.log</string>
    <key>StandardOutPath</key>
    <string>$CONFIG_DIR/ai_recovery_output.log</string>
</dict>
</plist>
EOF

print_success "Auto-start configured"

# Load LaunchAgents
print_status "Starting services..."

# Unload if already loaded
launchctl unload "$LAUNCH_AGENT_DIR/com.minicloud.monitor.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENT_DIR/com.minicloud.airecovery.plist" 2>/dev/null || true

# Load services
launchctl load "$LAUNCH_AGENT_DIR/com.minicloud.monitor.plist"
launchctl load "$LAUNCH_AGENT_DIR/com.minicloud.airecovery.plist"

print_success "Services started"

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

echo "Uninstalling MiniCloud AI Recovery System..."

# Stop services
launchctl unload ~/Library/LaunchAgents/com.minicloud.monitor.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.minicloud.airecovery.plist 2>/dev/null

# Remove LaunchAgents
rm -f ~/Library/LaunchAgents/com.minicloud.monitor.plist
rm -f ~/Library/LaunchAgents/com.minicloud.airecovery.plist

# Kill any running processes
pkill -f minicloud_monitor
pkill -f minicloud_ai_recovery

# Remove configuration
rm -rf ~/.minicloud

# Restore original claude-ns if backed up
if [ -f ~/.local/bin/claude-ns.backup ]; then
    mv ~/.local/bin/claude-ns.backup ~/.local/bin/claude-ns
fi

echo "Uninstall complete. Installation directory kept at ~/minicloud-widget"
echo "To completely remove, run: rm -rf ~/minicloud-widget"
EOF
chmod +x "$INSTALL_DIR/uninstall.sh"

# Final summary
echo
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║               Installation Complete!                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${BLUE}Services Status:${NC}"
echo -e "  • Widget: ${GREEN}Running${NC} (Check menu bar for ☁️ icon)"
echo -e "  • AI Recovery: ${GREEN}Running${NC} (Background service)"
echo
echo -e "${BLUE}Configuration:${NC}"
echo -e "  • Config directory: $CONFIG_DIR"
echo -e "  • Logs directory: $CONFIG_DIR"
echo -e "  • Server IP: $SERVER_IP"
echo
echo -e "${BLUE}Commands:${NC}"
echo -e "  • Start widget: $INSTALL_DIR/start_widget.sh"
echo -e "  • Start AI recovery: $INSTALL_DIR/start_ai_recovery.sh"
echo -e "  • View logs: tail -f $CONFIG_DIR/recovery.log"
echo -e "  • Uninstall: $INSTALL_DIR/uninstall.sh"
echo
echo -e "${BLUE}Claude-NS:${NC}"
if command -v claude-ns &> /dev/null; then
    echo -e "  • Status: ${GREEN}Fixed and ready${NC}"
    echo -e "  • Test with: claude-ns --neuralsync-status"
else
    echo -e "  • Status: ${YELLOW}Not installed${NC}"
    echo -e "  • Install from: https://claude.ai/code"
fi
echo
echo -e "${GREEN}The MiniCloud widget should now appear in your menu bar!${NC}"
echo -e "${GREEN}AI Recovery is monitoring your server in the background.${NC}"
echo