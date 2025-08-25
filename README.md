# MiniCloud Monitor

A native macOS menu bar widget for monitoring your server infrastructure with Prometheus metrics. Get real-time system statistics, quick access to dashboards, and visual status indicators right from your menu bar.

![MiniCloud Monitor](https://img.shields.io/badge/platform-macOS-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## Features

- 📊 **Real-time Monitoring**: CPU, Memory, Disk usage from Prometheus
- 🖥️ **Native macOS Integration**: Clean menu bar interface using system notifications
- ⚡ **Quick Actions**: Direct links to Grafana, Nextcloud, Prometheus
- 🔄 **Auto-refresh**: Updates every 30 seconds with configurable intervals  
- 🎨 **Visual Status**: Cloud emoji indicators (✅ Normal, ⚡ Moderate, ⚠️ High load)
- ⚙️ **Configurable**: Easy setup for custom servers and ports
- 🚀 **Lightweight**: Minimal resource usage, auto-starts on boot

## Screenshots

```
☁️✅ MiniCloud Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Status: Online
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 CPU: 23.4%
🧠 Memory: 45.2%
💾 Storage: 12.8%
⏱️ Uptime: 9h 48m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Open Grafana Dashboard
☁️ Open Nextcloud  
🔍 Open Prometheus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Refresh Now
```

## Quick Start

### Prerequisites

- macOS 10.14+ 
- Python 3.7+
- A server running Prometheus/Grafana (see [Server Setup](#server-setup))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/heyfinal/minicloud-widget.git
   cd minicloud-widget
   ```

2. **Run the installer:**
   ```bash
   ./install_widget.sh
   ```

3. **Look for the ☁️ icon in your menu bar!**

The widget will automatically start and connect to your server. If you need to configure custom settings, edit `config.json` (created on first run).

### Manual Installation

```bash
# Install dependencies
pip3 install --user rumps requests

# Make executable
chmod +x minicloud_monitor.py

# Run manually
python3 minicloud_monitor.py
```

## Configuration

Edit `config.json` to customize your setup:

```json
{
  "server": {
    "prometheus_url": "http://192.168.1.93:9091",
    "grafana_url": "http://192.168.1.93:3000", 
    "nextcloud_url": "http://192.168.1.93:8080"
  },
  "monitoring": {
    "refresh_interval": 30,
    "cpu_warning_threshold": 50,
    "cpu_critical_threshold": 80,
    "memory_warning_threshold": 70,
    "disk_warning_threshold": 85
  },
  "display": {
    "show_notifications": true,
    "compact_mode": false
  }
}
```

## Server Setup

### Option 1: Complete MiniCloud Stack

Deploy a full monitoring stack with our Docker Compose:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ['9091:9090']
    volumes: ['./prometheus:/etc/prometheus']
    
  grafana:
    image: grafana/grafana:latest
    ports: ['3000:3000']
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      
  node-exporter:
    image: prom/node-exporter:latest
    ports: ['9100:9100']
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
```

### Option 2: Existing Prometheus

If you already have Prometheus running, ensure these endpoints are available:

- **Prometheus API**: `http://your-server:9090/api/v1/query`
- **Basic metrics**: `node_cpu_seconds_total`, `node_memory_*`, `node_filesystem_*`

### Option 3: Cloud Providers

The widget works with cloud-hosted Prometheus instances:

- **Grafana Cloud**: Use your Grafana Cloud Prometheus endpoint
- **AWS**: Amazon Managed Service for Prometheus
- **GCP**: Google Cloud Monitoring with Prometheus
- **Azure**: Azure Monitor with Prometheus metrics

## Usage

### Menu Bar Controls

- **Click the ☁️ icon** to view current metrics
- **📊 Open Grafana Dashboard** - Launch web dashboard
- **☁️ Open Nextcloud** - Access your cloud storage
- **🔍 Open Prometheus** - View raw metrics
- **🔄 Refresh Now** - Force immediate update

### Status Indicators

- **☁️✅** - Normal operation (CPU < 50%)  
- **☁️⚡** - Moderate load (CPU 50-80%)
- **☁️⚠️** - High load (CPU > 80%)
- **☁️❌** - Server offline/unreachable

### Auto-start Setup

The installer automatically creates a Launch Agent for system startup:

```bash
# Manual control
launchctl load ~/Library/LaunchAgents/com.minicloud.monitor.plist
launchctl unload ~/Library/LaunchAgents/com.minicloud.monitor.plist
```

## Troubleshooting

### Common Issues

**Widget not appearing in menu bar:**
```bash
python3 minicloud_monitor.py
# Check console for errors
```

**Connection failed:**
```bash
# Test Prometheus connection
curl http://your-server:9091/api/v1/query?query=up
```

**Python/pip issues:**
```bash
# Install with Homebrew Python
brew install python
/opt/homebrew/bin/python3 -m pip install rumps requests
```

### Debug Mode

Run with debug logging:
```bash
python3 minicloud_monitor.py --debug
```

### Logs

Check application logs:
```bash
# Launch Agent logs
tail -f /tmp/minicloud-monitor.out
tail -f /tmp/minicloud-monitor.err
```

## Development

### Building from Source

```bash
git clone https://github.com/heyfinal/minicloud-widget.git
cd minicloud-widget

# Development dependencies
pip3 install --user rumps requests pytest

# Run tests
python3 -m pytest tests/

# Run development version
python3 minicloud_monitor.py --dev
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

### Architecture

```
minicloud_monitor.py     # Main application
├── PrometheusClient     # API client for metrics
├── MiniCloudMonitor     # Core app logic & menu bar
└── Configuration        # Settings management
```

## Roadmap

- [ ] **Multi-server support** - Monitor multiple servers
- [ ] **Custom metrics** - Add your own Prometheus queries  
- [ ] **Alerting** - Desktop notifications for critical issues
- [ ] **Themes** - Dark mode, custom icons
- [ ] **Docker widget** - Container-specific monitoring
- [ ] **iOS companion** - View metrics on iPhone/iPad

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/heyfinal/minicloud-widget/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/heyfinal/minicloud-widget/discussions)
- 📧 **Contact**: [support@minicloud-widget.com](mailto:support@minicloud-widget.com)

## Acknowledgments

- [rumps](https://github.com/jaredks/rumps) - Ridiculously Uncomplicated macOS Python Statusbar apps
- [Prometheus](https://prometheus.io/) - Systems monitoring and alerting toolkit
- [Grafana](https://grafana.com/) - Observability platform

---

<div align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
</div>