# MiniCloud AI Recovery System

## Overview

The MiniCloud AI Recovery System is an intelligent monitoring and auto-recovery solution for your MiniCloud server. It combines real-time monitoring, AI-powered diagnostics, and automated recovery actions to keep your server healthy.

## Features

### 🤖 AI-Powered Diagnostics
- Pattern recognition for issue detection
- Learning from past recovery attempts
- Predictive failure analysis
- Intelligent action selection

### 🔄 Automated Recovery
- Service restarts
- Container management
- Disk cleanup
- Memory optimization
- Network reset
- Process management
- Configuration repair

### 📊 Enhanced Widget
- Real-time status display
- Correct icon states (no more green when offline!)
- Issue tracking
- Recovery progress indication
- One-click access to services

### 🔔 Smart Notifications
- macOS native notifications
- Critical issue alerts
- Recovery success/failure updates
- Customizable thresholds

## Installation

### Quick Install

```bash
chmod +x install.sh
./install.sh
```

### Manual Install

1. Install Python dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure server access:
```bash
cp config.example.json config.json
# Edit config.json with your server details
```

3. Start services:
```bash
./start_widget.sh        # Start menu bar widget
./start_ai_recovery.sh   # Start AI recovery daemon
```

## Configuration

### Server Configuration (`~/.minicloud/ai_recovery_config.json`)

```json
{
  "server": {
    "ip": "192.168.1.93",
    "ssh_user": "admin",
    "ssh_key": "~/.ssh/id_rsa",
    "prometheus_url": "http://192.168.1.93:9091",
    "grafana_url": "http://192.168.1.93:3000"
  },
  "thresholds": {
    "cpu_warning": 70,
    "cpu_critical": 90,
    "memory_warning": 80,
    "memory_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90
  }
}
```

### Widget Configuration (`config.json`)

```json
{
  "display": {
    "status_icons": {
      "normal": "☁️✅",
      "warning": "☁️⚠️",
      "critical": "☁️🔴",
      "offline": "☁️❌"
    }
  }
}
```

## Usage

### Menu Bar Widget

The widget appears in your macOS menu bar with a cloud icon that changes based on server status:

- ☁️✅ **Healthy** - Everything is running smoothly
- ☁️⚠️ **Warning** - Minor issues detected
- ☁️🔴 **Critical** - Major issues requiring attention
- ☁️❌ **Offline** - Server is unreachable
- ☁️🔄 **Recovering** - AI is fixing issues
- ☁️❓ **Unknown** - Cannot determine status

Click the icon to see:
- Current server metrics
- Active issues
- AI Recovery status
- Quick access to services
- Recovery controls

### AI Recovery Actions

The system automatically performs these recovery actions:

1. **Service Issues**
   - Restart failed services
   - Clear service caches
   - Repair configurations

2. **High Resource Usage**
   - Kill high-CPU processes
   - Clear memory caches
   - Clean up disk space

3. **Container Problems**
   - Restart unhealthy containers
   - Clean Docker system
   - Reset container networks

4. **Network Issues**
   - Reset network interfaces
   - Restart networking services
   - Clear DNS cache

### Manual Controls

From the widget menu:
- **Start/Stop AI Recovery** - Control the recovery daemon
- **View Recovery Logs** - See detailed recovery actions
- **Refresh Now** - Force immediate metric update

### Command Line

```bash
# Check AI Recovery status
tail -f ~/.minicloud/recovery.log

# View current server status
cat ~/.minicloud/status.json | jq

# Manually trigger recovery
python3 minicloud_ai_recovery.py

# Test SSH connection
ssh -i ~/.ssh/id_rsa admin@192.168.1.93 "echo OK"
```

## Claude-NS Fix

The installer also fixes the claude-ns stdin/raw mode issue:

### Test the Fix
```bash
# Check NeuralSync status
claude-ns --neuralsync-status

# Use claude-ns normally
claude-ns "Help me with Python code"
```

### What Was Fixed
- Removed dependency on raw mode stdin
- Added PTY wrapper for interactive sessions
- Fixed service startup timeouts
- Improved error handling

## Troubleshooting

### Widget Not Appearing

1. Check if process is running:
```bash
ps aux | grep minicloud_monitor
```

2. Restart the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.minicloud.monitor.plist
launchctl load ~/Library/LaunchAgents/com.minicloud.monitor.plist
```

3. Check logs:
```bash
tail -f ~/.minicloud/widget_error.log
```

### AI Recovery Not Working

1. Verify SSH access:
```bash
ssh -i ~/.ssh/id_rsa admin@192.168.1.93 "sudo echo OK"
```

2. Check recovery logs:
```bash
tail -f ~/.minicloud/recovery.log
```

3. Test Prometheus access:
```bash
curl http://192.168.1.93:9091/-/healthy
```

### Claude-NS Still Failing

1. Use the fixed version directly:
```bash
~/NeuralSync2/bin/claude-ns-fixed
```

2. Check Python version:
```bash
python3 --version  # Should be 3.9+
```

3. Reinstall NeuralSync:
```bash
cd ~/NeuralSync2
./install_neuralsync.py
```

## Architecture

### Components

1. **DiagnosticEngine** - Analyzes metrics and detects issues
2. **RecoveryExecutor** - Performs recovery actions via SSH
3. **MetricsCollector** - Gathers data from Prometheus
4. **NotificationManager** - Handles alerts and notifications
5. **WidgetUpdater** - Updates menu bar display

### Learning System

The AI Recovery system learns from past actions:

1. **Pattern Recognition** - Identifies recurring issues
2. **Success Tracking** - Records which actions work
3. **Action Optimization** - Chooses best recovery method
4. **Predictive Analysis** - Anticipates future problems

### Data Flow

```
Prometheus → MetricsCollector → DiagnosticEngine
                                       ↓
                                  Issue Detection
                                       ↓
                                RecoveryExecutor
                                       ↓
                              SSH → MiniCloud Server
                                       ↓
                                 Action Result
                                       ↓
                                Learning Database
```

## Uninstallation

To completely remove the system:

```bash
./uninstall.sh
```

This will:
- Stop all services
- Remove LaunchAgents
- Delete configuration files
- Restore original claude-ns (if backed up)

## Support

For issues or questions:
1. Check logs in `~/.minicloud/`
2. Review configuration files
3. Ensure SSH key has proper permissions (`chmod 600 ~/.ssh/id_rsa`)
4. Verify server services are accessible

## License

MIT License - See LICENSE file for details