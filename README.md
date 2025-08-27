# MiniCLOUD Monitor Widget

A professional macOS menu bar widget for monitoring your MiniCLOUD server with real-time system metrics, security status, and one-click access to your services. Now includes complete touchless deployment automation for Mac Mini hardware.

![MiniCloud Monitor](https://img.shields.io/badge/platform-macOS-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

### Enhanced Connectivity Detection (v2.0)
- 🌐 **Multi-Path Testing**: Dual ethernet + wireless connectivity validation
- ⚡ **Intelligent Caching**: 30-second cache for instant widget updates  
- 🎯 **Smart Status Logic**: Distinguishes online/degraded/offline with high accuracy
- 📊 **Service Discovery**: Tests SSH, HTTP, HTTPS, and Nextcloud accessibility
- 🔄 **Auto-Recovery**: Handles network fluctuations and temporary outages gracefully

### System Monitoring
- 📊 **Real-time Metrics**: CPU, Memory, Disk usage, and uptime from Prometheus
- 🖥️ **Native macOS Integration**: Clean menu bar interface with system notifications
- ⚡ **Smart Refresh**: Auto-updates every 60 seconds minimum with duplicate prevention
- 🎨 **Visual Status Indicators**: Color-coded cloud icons based on system health
- 📈 **Uptime Tracking**: Real-time uptime percentage calculation and history

### Advanced Widget Modes
- 🟢 **Simple Mode**: Clean emoji-based status (`🟢 Online`, `🔴 Offline`)
- 📋 **Detailed Mode**: Comprehensive status with IP, services, and uptime metrics  
- 📄 **JSON Mode**: Structured data export for advanced widget integrations
- 👁️ **Monitor Mode**: Continuous monitoring with configurable update intervals

### Security Monitoring
- 🛡️ **Security Status**: Real-time security health monitoring
- 🔒 **Fail2ban Integration**: Monitor active SSH protection jails
- 🔥 **Firewall Status**: Track UFW firewall status and rules
- ⚠️ **Security Alerts**: Visual indicators for security system status

### Network Troubleshooting (NEW)
- 🔧 **Connectivity Diagnosis**: Multi-method network testing (ping, TCP, HTTP)
- 🌐 **Interface Analysis**: Ethernet and wireless network path validation
- 📊 **Performance Metrics**: Response time tracking and network quality assessment
- 🚨 **Error Resilience**: Graceful handling of network failures and timeouts

### Quick Access
- 📊 **One-Click Dashboards**: Direct links to Grafana, Prometheus, and Nextcloud
- ☁️ **Service Health**: Real-time availability checking with timeout handling
- ⚙️ **Configurable URLs**: Easy customization for your server setup
- 🔄 **Manual Refresh**: Force immediate metric updates

### Deployment & Automation
- 🚀 **Touchless Installation**: Complete automated Ubuntu Server deployment
- 💻 **Mac Mini Optimized**: Hardware-specific configurations for Mac Mini 7.1
- 🏗️ **Production Ready**: Full monitoring stack, security hardening included
- 📦 **One-Click Deploy**: Custom ISO creation with all services pre-configured

## 🚀 Quick Start

### Enhanced Widget (v2.0)

```bash
# Clone repository
git clone https://github.com/heyfinal/minicloud-widget.git
cd minicloud-widget

# Install dependencies
pip3 install aiohttp requests

# Test enhanced widget
python3 minicloud_widget_enhanced.py --simple
python3 minicloud_widget_enhanced.py --detailed  
python3 minicloud_widget_enhanced.py --json

# Run integration tests
python3 widget_integration_test.py

# Monitor mode (updates every 60 seconds)
python3 minicloud_widget_enhanced.py --monitor 60 --detailed
```

### Legacy Widget

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run installer
./install_widget.sh
```

Look for the ☁️ icon in your menu bar!

### Configure for Your Server

Edit `config.json` (created on first run):

```json
{
  "server": {
    "prometheus_url": "http://YOUR-SERVER-IP:9091",
    "grafana_url": "http://YOUR-SERVER-IP:3000",
    "nextcloud_url": "http://YOUR-SERVER-IP:8080"
  },
  "monitoring": {
    "refresh_interval": 60,
    "cpu_warning_threshold": 50,
    "cpu_critical_threshold": 80,
    "memory_warning_threshold": 70,
    "disk_warning_threshold": 85
  },
  "display": {
    "show_notifications": true,
    "compact_mode": false,
    "status_icons": {
      "normal": "☁️",
      "warning": "⚠️", 
      "critical": "🚨",
      "offline": "💀"
    }
  }
}
```

## 🏗️ Touchless MiniCLOUD Deployment

### Create Auto-Install ISO

Create a bootable Ubuntu Server ISO with complete MiniCLOUD setup:

```bash
# Install required tools (macOS)
brew install xorriso p7zip wget

# Create custom deployment ISO
./create_minicloud_iso.sh
```

### What Gets Installed Automatically

The deployment ISO creates a complete server environment:

- **🐧 Ubuntu Server 24.04 LTS** with Mac Mini 7.1 optimizations
- **🐳 Docker & Docker Compose** for containerized services  
- **📊 Prometheus & Node Exporter** for comprehensive system monitoring
- **📈 Grafana** with pre-configured dashboards and admin access
- **☁️ Nextcloud** for cloud storage and file sharing via Snap
- **🔒 Fail2ban** for SSH brute force protection and IP banning
- **🔥 UFW Firewall** with secure default rules and service access
- **📡 Broadcom WiFi drivers** for Mac Mini internal WiFi connectivity
- **🔗 Network Bonding** Ethernet + WiFi failover configuration

### Hardware Compatibility

Specifically optimized for **Mac Mini 7.1 (Late 2014)**:
- Intel Core i5/i7 4th generation processors
- 8-16GB RAM support with automatic detection
- Gigabit Ethernet + 802.11ac WiFi with bonding
- USB 3.0 and Thunderbolt 2 port support
- Automatic Broadcom WiFi driver installation
- LVM storage with encryption options

### Installation Process

1. **Flash ISO to USB Drive**:
   ```bash
   sudo dd if=minicloud-server-autoinstall.iso of=/dev/diskX bs=1m
   ```

2. **Boot Mac Mini**:
   - Hold Alt/Option key during startup
   - Select "EFI Boot" option from boot menu
   - Installation proceeds completely automatically (15-20 minutes)
   - No user interaction required during installation

3. **Access Your MiniCLOUD Server**:
   - **SSH**: `ssh daniel@[server-ip]` (key-based auth)
   - **Grafana**: `http://[server-ip]:3000` (admin/minicloud123)
   - **Prometheus**: `http://[server-ip]:9091` (metrics and targets)
   - **Nextcloud**: `http://[server-ip]:8080` (cloud storage)

## 📊 Complete Monitoring Stack

### Pre-configured Services

| Service | Port | Purpose | Default Access |
|---------|------|---------|----------------|
| **Prometheus** | 9091 | Metrics collection & storage | http://server:9091 |
| **Grafana** | 3000 | Visualization dashboards | admin/minicloud123 |
| **Node Exporter** | 9100 | System metrics export | Internal only |
| **Nextcloud** | 8080 | Cloud storage & sync | Via Snap package |
| **SSH** | 22 | Secure remote access | Key-based auth |

### Security Features

- **🔒 Fail2ban Protection**: Automatic IP banning for failed SSH attempts
- **🔥 UFW Firewall**: Restrictive rules allowing only necessary service ports  
- **🛡️ Encrypted Storage**: LVM with optional LUKS full-disk encryption
- **🔑 SSH Key Authentication**: Secure passwordless login with public key
- **🚫 Disabled Root**: Root login disabled, sudo-only administration
- **⏰ Automatic Updates**: Weekly security updates via cron scheduling

### Widget Screenshots

```
☁️ MiniCLOUD Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 Status: Online
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💻 CPU: 23.4%
🧠 Memory: 45.2%
💾 Storage: 12.8%
⏱️ Uptime: 9h 48m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ Security: Protected
🔒 Fail2ban: 1 jails active
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Open Grafana Dashboard
☁️ Open Nextcloud
🔍 Open Prometheus  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Refresh Now
```

## 🔧 Advanced Configuration

### Network Configuration

The auto-install supports flexible network setup:

```yaml
# Ethernet + WiFi bonding with failover
bonds:
  bond0:
    interfaces: [eno0, wlp3s0]  # Ethernet primary, WiFi secondary
    addresses: [192.168.1.100/24]
    gateway4: 192.168.1.1
    parameters:
      mode: active-backup
      primary: eno0  # Prefer Ethernet
      fail-over-mac: none
```

### Custom Service Configuration

Modify the ISO script to add your own services:

```bash
# Add custom services to /opt/minicloud-startup.sh
- echo "Starting custom service..." >> /var/log/minicloud.log
- systemctl enable my-custom-service
- systemctl start my-custom-service
```

### Widget Customization

Advanced widget configuration options:

```json
{
  "monitoring": {
    "refresh_interval": 60,
    "timeout_seconds": 10,
    "retry_attempts": 3,
    "enable_security_monitoring": true
  },
  "display": {
    "show_security_status": true,
    "compact_mode": false,
    "notification_threshold": 90
  }
}
```

## 🛠️ Development & Testing

### Requirements

```txt
rumps>=0.4.0
requests>=2.25.0
psutil>=5.8.0
```

### Building from Source

```bash
git clone https://github.com/heyfinal/minicloud-widget.git
cd minicloud-widget

# Development dependencies
pip3 install --user -r requirements.txt

# Run development version
python3 minicloud_monitor.py
```

### Testing the ISO

```bash
# Test ISO creation process
./create_minicloud_iso.sh

# Verify ISO with QEMU (requires: brew install qemu)
qemu-system-x86_64 \
  -m 4096 \
  -cdrom minicloud-server-autoinstall.iso \
  -drive file=test-disk.img,format=qcow2,if=virtio
```

## 📋 Troubleshooting

### Common Widget Issues

**Multiple widgets in menu bar**:
```bash
# Kill all instances
pkill -f minicloud_monitor.py
# Widget now prevents duplicates automatically
python3 minicloud_monitor.py
```

**Connection timeouts**:
```bash
# Test server connectivity
ping YOUR-SERVER-IP
curl -m 10 http://YOUR-SERVER-IP:9091/-/healthy
```

**Widget not auto-starting**:
```bash
# Check launch agent status
launchctl list | grep minicloud
launchctl load ~/Library/LaunchAgents/com.minicloud.monitor.plist
```

### Server Deployment Issues

**ISO won't boot on Mac Mini**:
- Disable Secure Boot in Mac firmware settings
- Try different USB creation tool (Balena Etcher recommended)
- Verify Mac Mini 7.1 compatibility

**WiFi drivers not working**:
```bash
# Manual driver installation on server
sudo apt install firmware-linux-nonfree broadcom-sta-dkms
sudo modprobe -r b43 ssb wl brcmfmac brcmsmac bcma
sudo modprobe wl
```

**Services not starting**:
```bash
# Check service status
systemctl status prometheus grafana-server fail2ban
# View startup logs
journalctl -u prometheus --since "1 hour ago"
```

### Log Locations

- **Widget logs**: Console.app → search "minicloud"
- **Server installation**: `/var/log/minicloud-ready.log`
- **Service logs**: `journalctl -u SERVICE_NAME`
- **Security logs**: `/var/log/fail2ban.log`

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request** with detailed description

### Development Guidelines

- Follow PEP 8 Python style guidelines
- Add tests for new functionality
- Update documentation for user-facing changes
- Test on actual Mac Mini hardware when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[rumps](https://github.com/jaredks/rumps)** - Ridiculously Uncomplicated macOS Python Statusbar apps
- **[Prometheus](https://prometheus.io/)** - Systems monitoring and alerting toolkit  
- **[Grafana](https://grafana.com/)** - The open observability platform
- **[Nextcloud](https://nextcloud.com/)** - The self-hosted productivity platform
- **[Ubuntu](https://ubuntu.com/)** - The leading operating system for containers and cloud
- **[Fail2ban](https://github.com/fail2ban/fail2ban)** - Daemon to ban hosts that cause multiple authentication errors

## 🌟 Support This Project

If you find MiniCLOUD Monitor Widget helpful:

- ⭐ **Star this repository**
- 🐛 **Report bugs** via GitHub Issues  
- 💡 **Suggest features** in Discussions
- 🤝 **Contribute code** via Pull Requests
- 📢 **Share with others** who need server monitoring

---

**Built for professional Mac Mini server deployments with enterprise-grade monitoring, security, and automation.**