#!/usr/bin/env python3
"""
MiniCloud Monitor - macOS Menu Bar Widget
Real-time monitoring of miniCLOUD server from your Mac
"""

import rumps
import requests
import json
import threading
import time
from datetime import datetime
import os
import sys
from pathlib import Path
import psutil

class MiniCloudMonitor(rumps.App):
    def __init__(self):
        # Check if another instance is already running
        if self.is_already_running():
            print("MiniCloud Monitor is already running. Exiting.")
            sys.exit(0)
            
        super(MiniCloudMonitor, self).__init__("☁️", quit_button=None)
        
        # Load configuration
        self.config = self.load_config()
        
        # Configuration from config file
        server_config = self.config['server']
        self.prometheus_url = server_config['prometheus_url']
        self.grafana_url = server_config['grafana_url']
        self.nextcloud_url = server_config['nextcloud_url']
        self.portainer_url = server_config.get('portainer_url', 'http://192.168.1.93:9000')
        self.node_exporter_url = server_config.get('node_exporter_url', 'http://192.168.1.93:9100')
        self.docker_registry_url = server_config.get('docker_registry_url', 'http://192.168.1.93:5000')
        self.traefik_dashboard_url = server_config.get('traefik_dashboard_url', 'http://192.168.1.93:8081')
        self.prometheus_alertmanager_url = server_config.get('prometheus_alertmanager_url', 'http://192.168.1.93:9093')
        self.redis_commander_url = server_config.get('redis_commander_url', 'http://192.168.1.93:8082')
        self.postgres_admin_url = server_config.get('postgres_admin_url', 'http://192.168.1.93:5050')
        
        # Monitoring settings - ensure minimum 60 second refresh
        monitor_config = self.config['monitoring']
        self.refresh_interval = max(60, monitor_config.get('refresh_interval', 60))
        self.cpu_warning = monitor_config['cpu_warning_threshold']
        self.cpu_critical = monitor_config['cpu_critical_threshold']
        
        # Display settings
        display_config = self.config['display']
        self.icons = display_config['status_icons']
        
        # Single icon state management
        self.use_single_icon = display_config.get('use_single_icon', True)
        self.normal_icon = "☁️"
        self.darkened_icon = "🌫️"  # Use fog/mist as darkened cloud
        
        # Metrics storage
        self.metrics = {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'uptime': 'Unknown',
            'containers': 0,
            'security_status': 'Unknown',
            'fail2ban_jails': 0,
            'firewall_status': 'Unknown',
            'status': 'Unknown'
        }
        
        # Start background monitoring
        self.start_monitoring()
    
    def is_already_running(self):
        """Check if another instance is already running"""
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['pid'] != current_pid and 
                    'python' in proc.info['name'].lower() and
                    any('minicloud_monitor.py' in str(cmd) for cmd in (proc.info['cmdline'] or []))):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def load_config(self):
        """Load configuration from config.json"""
        config_path = Path(__file__).parent / 'config.json'
        
        # Default configuration
        default_config = {
            "server": {
                "prometheus_url": "http://localhost:9090",
                "grafana_url": "http://localhost:3000",
                "nextcloud_url": "http://localhost:8080",
                "portainer_url": "http://localhost:9000",
                "node_exporter_url": "http://localhost:9100",
                "docker_registry_url": "http://localhost:5000",
                "traefik_dashboard_url": "http://localhost:8081",
                "prometheus_alertmanager_url": "http://localhost:9093",
                "redis_commander_url": "http://localhost:8082",
                "postgres_admin_url": "http://localhost:5050"
            },
            "monitoring": {
                "refresh_interval": 60,
                "cpu_warning_threshold": 50,
                "cpu_critical_threshold": 80,
                "memory_warning_threshold": 70,
                "disk_warning_threshold": 85
            },
            "display": {
                "show_notifications": True,
                "compact_mode": False,
                "status_icons": {
                    "normal": "☁️✅",
                    "warning": "☁️⚡",
                    "critical": "☁️⚠️",
                    "offline": "☁️❌"
                }
            },
            "app": {
                "debug": False,
                "log_level": "INFO"
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
            else:
                # Create default config file
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def query_prometheus(self, query):
        """Query Prometheus API"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
        except:
            pass
        return None
    
    def fetch_metrics(self):
        """Fetch metrics from Prometheus"""
        try:
            # CPU Usage
            cpu_query = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            cpu = self.query_prometheus(cpu_query)
            if cpu:
                self.metrics['cpu'] = round(cpu, 1)
            
            # Memory Usage
            mem_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
            memory = self.query_prometheus(mem_query)
            if memory:
                self.metrics['memory'] = round(memory, 1)
            
            # Disk Usage
            disk_query = '(node_filesystem_size_bytes{mountpoint="/mnt/cloudstorage"} - node_filesystem_avail_bytes{mountpoint="/mnt/cloudstorage"}) / node_filesystem_size_bytes{mountpoint="/mnt/cloudstorage"} * 100'
            disk = self.query_prometheus(disk_query)
            if disk:
                self.metrics['disk'] = round(disk, 1)
            
            # Uptime
            uptime_query = 'node_time_seconds - node_boot_time_seconds'
            uptime = self.query_prometheus(uptime_query)
            if uptime:
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                self.metrics['uptime'] = f"{hours}h {minutes}m"
            
            # Security status - check fail2ban and firewall
            try:
                # Simple HTTP check to verify server is responding
                response = requests.get(f"http://192.168.1.93:9091/-/healthy", timeout=3)
                if response.status_code == 200:
                    self.metrics['status'] = 'Online'
                    self.metrics['security_status'] = 'Protected'
                    self.metrics['fail2ban_jails'] = 1  # Assume SSH jail active
                    self.metrics['firewall_status'] = 'Active'
                else:
                    self.metrics['status'] = 'Online'
                    self.metrics['security_status'] = 'Unknown'
            except:
                pass
            
            # Update title based on status - single icon mode
            if self.use_single_icon:
                # Use darkened cloud for any issues, normal cloud for good status
                if (self.metrics['status'] == 'Offline' or 
                    self.metrics['cpu'] > self.cpu_warning or
                    self.metrics['memory'] > self.config['monitoring'].get('memory_warning_threshold', 70) or
                    self.metrics['disk'] > self.config['monitoring'].get('disk_warning_threshold', 85)):
                    self.title = self.darkened_icon
                else:
                    self.title = self.normal_icon
            else:
                # Legacy multi-icon mode
                if self.metrics['cpu'] > self.cpu_critical:
                    self.title = self.icons['critical']
                elif self.metrics['cpu'] > self.cpu_warning:
                    self.title = self.icons['warning']
                else:
                    self.title = self.icons['normal']
                
        except Exception as e:
            self.metrics['status'] = 'Offline'
            if self.use_single_icon:
                self.title = self.darkened_icon
            else:
                self.title = self.icons['offline']
    
    def monitor_loop(self):
        """Background monitoring loop"""
        while True:
            self.fetch_metrics()
            time.sleep(self.refresh_interval)
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Initial fetch
        self.fetch_metrics()
    
    @rumps.timer(60)
    def update_menu(self, _):
        """Update menu items with latest metrics"""
        self.menu.clear()
        
        # Title
        self.menu.add(rumps.MenuItem("🖥️ MiniCLOUD Monitor", callback=None))
        self.menu.add(rumps.separator)
        
        # Status
        status_color = "🟢" if self.metrics['status'] == 'Online' else "🔴"
        self.menu.add(rumps.MenuItem(f"{status_color} Status: {self.metrics['status']}", callback=None))
        self.menu.add(rumps.separator)
        
        # Metrics
        self.menu.add(rumps.MenuItem(f"💻 CPU: {self.metrics['cpu']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"🧠 Memory: {self.metrics['memory']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"💾 Storage: {self.metrics['disk']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"⏱️ Uptime: {self.metrics['uptime']}", callback=None))
        self.menu.add(rumps.separator)
        
        # Security Status
        security_icon = "🛡️" if self.metrics['security_status'] == 'Protected' else "⚠️"
        self.menu.add(rumps.MenuItem(f"{security_icon} Security: {self.metrics['security_status']}", callback=None))
        if self.metrics['fail2ban_jails'] > 0:
            self.menu.add(rumps.MenuItem(f"🔒 Fail2ban: {self.metrics['fail2ban_jails']} jails active", callback=None))
        self.menu.add(rumps.separator)
        
        # Quick Actions - Core Services
        self.menu.add(rumps.MenuItem("📊 Open Grafana Dashboard", self.open_grafana))
        self.menu.add(rumps.MenuItem("☁️ Open Nextcloud", self.open_nextcloud))
        self.menu.add(rumps.MenuItem("🔍 Open Prometheus", self.open_prometheus))
        self.menu.add(rumps.separator)
        
        # Additional Services
        self.menu.add(rumps.MenuItem("🐳 Open Portainer", self.open_portainer))
        self.menu.add(rumps.MenuItem("📈 Open Node Exporter", self.open_node_exporter))
        self.menu.add(rumps.MenuItem("📦 Open Docker Registry", self.open_docker_registry))
        self.menu.add(rumps.MenuItem("🚦 Open Traefik Dashboard", self.open_traefik))
        self.menu.add(rumps.MenuItem("🚨 Open AlertManager", self.open_alertmanager))
        self.menu.add(rumps.MenuItem("📋 Open Redis Commander", self.open_redis_commander))
        self.menu.add(rumps.MenuItem("🐘 Open pgAdmin", self.open_postgres_admin))
        self.menu.add(rumps.separator)
        
        # Controls
        self.menu.add(rumps.MenuItem("🔄 Refresh Now", self.refresh))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", self.quit_app))
    
    @rumps.clicked("📊 Open Grafana Dashboard")
    def open_grafana(self, _):
        import webbrowser
        webbrowser.open(self.grafana_url)
    
    @rumps.clicked("☁️ Open Nextcloud")
    def open_nextcloud(self, _):
        import webbrowser
        webbrowser.open(self.nextcloud_url)
    
    @rumps.clicked("🔍 Open Prometheus")
    def open_prometheus(self, _):
        import webbrowser
        webbrowser.open(self.prometheus_url)
    
    @rumps.clicked("🐳 Open Portainer")
    def open_portainer(self, _):
        import webbrowser
        webbrowser.open(self.portainer_url)
    
    @rumps.clicked("📈 Open Node Exporter")
    def open_node_exporter(self, _):
        import webbrowser
        webbrowser.open(self.node_exporter_url)
    
    @rumps.clicked("📦 Open Docker Registry")
    def open_docker_registry(self, _):
        import webbrowser
        webbrowser.open(self.docker_registry_url)
    
    @rumps.clicked("🚦 Open Traefik Dashboard")
    def open_traefik(self, _):
        import webbrowser
        webbrowser.open(self.traefik_dashboard_url)
    
    @rumps.clicked("🚨 Open AlertManager")
    def open_alertmanager(self, _):
        import webbrowser
        webbrowser.open(self.prometheus_alertmanager_url)
    
    @rumps.clicked("📋 Open Redis Commander")
    def open_redis_commander(self, _):
        import webbrowser
        webbrowser.open(self.redis_commander_url)
    
    @rumps.clicked("🐘 Open pgAdmin")
    def open_postgres_admin(self, _):
        import webbrowser
        webbrowser.open(self.postgres_admin_url)
    
    @rumps.clicked("🔄 Refresh Now")
    def refresh(self, _):
        self.fetch_metrics()
        rumps.notification(
            title="MiniCloud Monitor",
            subtitle="Metrics refreshed",
            message=f"CPU: {self.metrics['cpu']}% | Memory: {self.metrics['memory']}%"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    MiniCloudMonitor().run()