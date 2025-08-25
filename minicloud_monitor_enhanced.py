#!/usr/bin/env python3
"""
Enhanced MiniCloud Monitor - macOS Menu Bar Widget with AI Recovery Integration
Real-time monitoring with automatic issue detection and recovery
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
import subprocess

class EnhancedMiniCloudMonitor(rumps.App):
    def __init__(self):
        # Check if another instance is already running
        if self.is_already_running():
            print("MiniCloud Monitor is already running. Exiting.")
            sys.exit(0)
            
        super(EnhancedMiniCloudMonitor, self).__init__("☁️", quit_button=None)
        
        # Load configuration
        self.config = self.load_config()
        
        # AI Recovery status file
        self.status_file = Path.home() / '.minicloud' / 'status.json'
        
        # Configuration from config file
        server_config = self.config['server']
        self.prometheus_url = server_config['prometheus_url']
        self.grafana_url = server_config['grafana_url']
        self.nextcloud_url = server_config['nextcloud_url']
        self.portainer_url = server_config.get('portainer_url', 'http://192.168.1.93:9000')
        
        # Monitoring settings
        monitor_config = self.config['monitoring']
        self.refresh_interval = max(30, monitor_config.get('refresh_interval', 30))
        self.cpu_warning = monitor_config['cpu_warning_threshold']
        self.cpu_critical = monitor_config['cpu_critical_threshold']
        
        # Display settings
        display_config = self.config['display']
        self.icons = display_config['status_icons']
        
        # AI Recovery integration
        self.ai_recovery_enabled = False
        self.ai_recovery_process = None
        
        # Metrics storage
        self.metrics = {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'uptime': 'Unknown',
            'containers': 0,
            'status': 'Unknown',
            'ai_status': 'Inactive',
            'issues': [],
            'recovery_in_progress': False
        }
        
        # Start background monitoring
        self.start_monitoring()
        
        # Check AI recovery system
        self.check_ai_recovery_system()
    
    def is_already_running(self):
        """Check if another instance is already running"""
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['pid'] != current_pid and 
                    'python' in proc.info['name'].lower() and
                    any('minicloud_monitor' in str(cmd) for cmd in (proc.info['cmdline'] or []))):
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
                "prometheus_url": "http://192.168.1.93:9091",
                "grafana_url": "http://192.168.1.93:3000",
                "nextcloud_url": "http://192.168.1.93:8080",
                "portainer_url": "http://192.168.1.93:9000"
            },
            "monitoring": {
                "refresh_interval": 30,
                "cpu_warning_threshold": 50,
                "cpu_critical_threshold": 80
            },
            "display": {
                "show_notifications": True,
                "status_icons": {
                    "normal": "☁️✅",
                    "warning": "☁️⚠️",
                    "critical": "☁️🔴",
                    "offline": "☁️❌",
                    "recovering": "☁️🔄",
                    "unknown": "☁️❓"
                }
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
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
    
    def check_ai_recovery_system(self):
        """Check if AI recovery system is running"""
        ai_recovery_script = Path(__file__).parent / 'minicloud_ai_recovery.py'
        if ai_recovery_script.exists():
            # Check if process is running
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if any('minicloud_ai_recovery.py' in str(cmd) for cmd in (proc.info['cmdline'] or [])):
                        self.ai_recovery_enabled = True
                        self.ai_recovery_process = proc.info['pid']
                        break
                except:
                    continue
    
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
        """Fetch metrics from Prometheus and AI Recovery status"""
        try:
            # Try to read AI Recovery status first
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    ai_status = json.load(f)
                    
                # Use AI Recovery metrics if available
                self.metrics['status'] = ai_status.get('status', 'Unknown').title()
                self.metrics['cpu'] = round(ai_status['metrics'].get('cpu', 0), 1)
                self.metrics['memory'] = round(ai_status['metrics'].get('memory', 0), 1)
                self.metrics['disk'] = round(ai_status['metrics'].get('disk', 0), 1)
                
                # Uptime formatting
                uptime_seconds = ai_status['metrics'].get('uptime', 0)
                if uptime_seconds:
                    hours = int(uptime_seconds // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    self.metrics['uptime'] = f"{hours}h {minutes}m"
                    
                self.metrics['issues'] = ai_status.get('issues', [])
                self.metrics['recovery_in_progress'] = ai_status.get('recovery_in_progress', False)
                self.metrics['ai_status'] = 'Active'
                
                # Update icon based on actual status
                status_map = {
                    'healthy': 'normal',
                    'degraded': 'warning',
                    'critical': 'critical',
                    'offline': 'offline',
                    'recovering': 'recovering',
                    'unknown': 'unknown'
                }
                icon_key = status_map.get(ai_status.get('status', 'unknown'), 'unknown')
                self.title = self.icons.get(icon_key, '☁️❓')
                
            else:
                # Fall back to direct Prometheus queries
                cpu_query = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
                cpu = self.query_prometheus(cpu_query)
                if cpu is not None:
                    self.metrics['cpu'] = round(cpu, 1)
                
                mem_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
                memory = self.query_prometheus(mem_query)
                if memory is not None:
                    self.metrics['memory'] = round(memory, 1)
                
                disk_query = '(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100'
                disk = self.query_prometheus(disk_query)
                if disk is not None:
                    self.metrics['disk'] = round(disk, 1)
                
                # Check if server is responding
                try:
                    response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=3)
                    if response.status_code == 200:
                        self.metrics['status'] = 'Online'
                        
                        # Update icon based on metrics
                        if self.metrics['cpu'] > self.cpu_critical:
                            self.title = self.icons['critical']
                        elif self.metrics['cpu'] > self.cpu_warning:
                            self.title = self.icons['warning']
                        else:
                            self.title = self.icons['normal']
                    else:
                        self.metrics['status'] = 'Degraded'
                        self.title = self.icons['warning']
                except:
                    self.metrics['status'] = 'Offline'
                    self.title = self.icons['offline']
                    
        except Exception as e:
            # If we can't get any metrics, show offline
            self.metrics['status'] = 'Offline'
            self.title = self.icons['offline']
            self.metrics['ai_status'] = 'Error'
    
    def monitor_loop(self):
        """Background monitoring loop"""
        while True:
            self.fetch_metrics()
            self.check_ai_recovery_system()
            time.sleep(self.refresh_interval)
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Initial fetch
        self.fetch_metrics()
    
    @rumps.timer(30)
    def update_menu(self, _):
        """Update menu items with latest metrics"""
        self.menu.clear()
        
        # Title
        self.menu.add(rumps.MenuItem("🖥️ MiniCLOUD Monitor", callback=None))
        self.menu.add(rumps.separator)
        
        # Status with proper color coding
        status_colors = {
            'Healthy': '🟢',
            'Online': '🟢',
            'Degraded': '🟡',
            'Critical': '🔴',
            'Offline': '🔴',
            'Recovering': '🔄',
            'Unknown': '⚫'
        }
        status_color = status_colors.get(self.metrics['status'], '⚫')
        self.menu.add(rumps.MenuItem(f"{status_color} Status: {self.metrics['status']}", callback=None))
        
        # AI Recovery Status
        ai_icon = '🤖' if self.ai_recovery_enabled else '🔌'
        ai_status = 'Active' if self.ai_recovery_enabled else 'Inactive'
        self.menu.add(rumps.MenuItem(f"{ai_icon} AI Recovery: {ai_status}", callback=None))
        
        if self.metrics['recovery_in_progress']:
            self.menu.add(rumps.MenuItem("🔄 Recovery in Progress...", callback=None))
            
        self.menu.add(rumps.separator)
        
        # Metrics
        self.menu.add(rumps.MenuItem(f"💻 CPU: {self.metrics['cpu']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"🧠 Memory: {self.metrics['memory']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"💾 Storage: {self.metrics['disk']}%", callback=None))
        self.menu.add(rumps.MenuItem(f"⏱️ Uptime: {self.metrics['uptime']}", callback=None))
        
        # Show issues if any
        if self.metrics['issues']:
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("⚠️ Active Issues:", callback=None))
            for issue in self.metrics['issues'][:3]:  # Show top 3 issues
                severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(issue.get('severity', 'low'), '⚫')
                resolved_mark = ' ✓' if issue.get('resolved', False) else ''
                self.menu.add(rumps.MenuItem(f"  {severity_icon} {issue.get('description', 'Unknown issue')}{resolved_mark}", callback=None))
        
        self.menu.add(rumps.separator)
        
        # Quick Actions
        self.menu.add(rumps.MenuItem("📊 Open Grafana Dashboard", self.open_grafana))
        self.menu.add(rumps.MenuItem("☁️ Open Nextcloud", self.open_nextcloud))
        self.menu.add(rumps.MenuItem("🔍 Open Prometheus", self.open_prometheus))
        self.menu.add(rumps.MenuItem("🐳 Open Portainer", self.open_portainer))
        self.menu.add(rumps.separator)
        
        # AI Recovery Controls
        if not self.ai_recovery_enabled:
            self.menu.add(rumps.MenuItem("🚀 Start AI Recovery System", self.start_ai_recovery))
        else:
            self.menu.add(rumps.MenuItem("🛑 Stop AI Recovery System", self.stop_ai_recovery))
            
        self.menu.add(rumps.MenuItem("📋 View Recovery Logs", self.view_recovery_logs))
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
    
    @rumps.clicked("🚀 Start AI Recovery System")
    def start_ai_recovery(self, _):
        """Start the AI recovery system"""
        ai_recovery_script = Path(__file__).parent / 'minicloud_ai_recovery.py'
        if ai_recovery_script.exists():
            try:
                subprocess.Popen(
                    [sys.executable, str(ai_recovery_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(2)  # Wait for startup
                self.check_ai_recovery_system()
                
                if self.ai_recovery_enabled:
                    rumps.notification(
                        title="MiniCloud AI Recovery",
                        subtitle="System Started",
                        message="AI-powered monitoring and recovery is now active"
                    )
                else:
                    rumps.notification(
                        title="MiniCloud AI Recovery",
                        subtitle="Startup Failed",
                        message="Failed to start AI recovery system. Check logs for details."
                    )
            except Exception as e:
                rumps.notification(
                    title="MiniCloud AI Recovery",
                    subtitle="Error",
                    message=f"Failed to start: {str(e)}"
                )
    
    @rumps.clicked("🛑 Stop AI Recovery System")
    def stop_ai_recovery(self, _):
        """Stop the AI recovery system"""
        if self.ai_recovery_process:
            try:
                proc = psutil.Process(self.ai_recovery_process)
                proc.terminate()
                time.sleep(1)
                if proc.is_running():
                    proc.kill()
                    
                self.ai_recovery_enabled = False
                self.ai_recovery_process = None
                
                rumps.notification(
                    title="MiniCloud AI Recovery",
                    subtitle="System Stopped",
                    message="AI recovery system has been stopped"
                )
            except Exception as e:
                rumps.notification(
                    title="MiniCloud AI Recovery",
                    subtitle="Error",
                    message=f"Failed to stop: {str(e)}"
                )
    
    @rumps.clicked("📋 View Recovery Logs")
    def view_recovery_logs(self, _):
        """Open recovery logs"""
        log_file = Path.home() / '.minicloud' / 'recovery.log'
        if log_file.exists():
            subprocess.run(['open', '-a', 'Console', str(log_file)])
        else:
            rumps.notification(
                title="MiniCloud Monitor",
                subtitle="No Logs",
                message="Recovery logs not found. Start AI Recovery System first."
            )
    
    @rumps.clicked("🔄 Refresh Now")
    def refresh(self, _):
        self.fetch_metrics()
        
        # Create detailed status message
        status_msg = f"Status: {self.metrics['status']}"
        metrics_msg = f"CPU: {self.metrics['cpu']}% | Memory: {self.metrics['memory']}% | Disk: {self.metrics['disk']}%"
        
        if self.metrics['issues']:
            issues_msg = f"{len(self.metrics['issues'])} active issues detected"
        else:
            issues_msg = "No issues detected"
            
        rumps.notification(
            title="MiniCloud Monitor",
            subtitle=status_msg,
            message=f"{metrics_msg}\n{issues_msg}"
        )
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    EnhancedMiniCloudMonitor().run()