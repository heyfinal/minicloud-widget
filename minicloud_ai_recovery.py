#!/usr/bin/env python3
"""
MiniCloud AI Recovery System
Intelligent monitoring, diagnosis, and auto-recovery for MiniCloud infrastructure
"""

import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import threading
import requests
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import sqlite3
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.minicloud' / 'recovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServerStatus(Enum):
    """Server health states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Recovery action types"""
    RESTART_SERVICE = "restart_service"
    REBOOT_SERVER = "reboot_server"
    CLEAR_CACHE = "clear_cache"
    RESTART_CONTAINER = "restart_container"
    NETWORK_RESET = "network_reset"
    DISK_CLEANUP = "disk_cleanup"
    PROCESS_KILL = "process_kill"
    CONFIG_REPAIR = "config_repair"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class HealthMetrics:
    """System health metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_latency: float = 0.0
    service_statuses: Dict[str, bool] = field(default_factory=dict)
    container_statuses: Dict[str, str] = field(default_factory=dict)
    uptime_seconds: int = 0
    last_check: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    recovery_attempts: int = 0


@dataclass
class Issue:
    """Detected system issue"""
    issue_id: str
    severity: str  # critical, high, medium, low
    component: str
    description: str
    detected_at: datetime
    metrics: Dict[str, Any]
    suggested_actions: List[RecoveryAction]
    resolved: bool = False
    resolution: Optional[str] = None


class DiagnosticEngine:
    """AI-powered diagnostic engine for issue detection and analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get('thresholds', {})
        self.patterns = []
        self.learning_db = self._init_learning_db()
        
    def _init_learning_db(self) -> sqlite3.Connection:
        """Initialize learning database for pattern recognition"""
        db_path = Path.home() / '.minicloud' / 'diagnostic_patterns.db'
        db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        conn.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY,
                issue_type TEXT,
                pattern_hash TEXT UNIQUE,
                metrics TEXT,
                successful_action TEXT,
                success_rate REAL,
                occurrences INTEGER,
                last_seen TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recovery_history (
                id INTEGER PRIMARY KEY,
                issue_id TEXT,
                action TEXT,
                success BOOLEAN,
                duration_seconds REAL,
                timestamp TIMESTAMP
            )
        ''')
        conn.commit()
        return conn
        
    def analyze_metrics(self, metrics: HealthMetrics) -> List[Issue]:
        """Analyze metrics to detect issues"""
        issues = []
        
        # CPU Analysis
        if metrics.cpu_usage > self.thresholds.get('cpu_critical', 90):
            issues.append(Issue(
                issue_id=self._generate_issue_id('cpu_critical'),
                severity='critical',
                component='cpu',
                description=f'Critical CPU usage: {metrics.cpu_usage}%',
                detected_at=datetime.now(),
                metrics={'cpu_usage': metrics.cpu_usage},
                suggested_actions=[
                    RecoveryAction.PROCESS_KILL,
                    RecoveryAction.RESTART_SERVICE,
                    RecoveryAction.REBOOT_SERVER
                ]
            ))
        elif metrics.cpu_usage > self.thresholds.get('cpu_warning', 70):
            issues.append(Issue(
                issue_id=self._generate_issue_id('cpu_high'),
                severity='high',
                component='cpu',
                description=f'High CPU usage: {metrics.cpu_usage}%',
                detected_at=datetime.now(),
                metrics={'cpu_usage': metrics.cpu_usage},
                suggested_actions=[RecoveryAction.PROCESS_KILL, RecoveryAction.RESTART_SERVICE]
            ))
            
        # Memory Analysis
        if metrics.memory_usage > self.thresholds.get('memory_critical', 95):
            issues.append(Issue(
                issue_id=self._generate_issue_id('memory_critical'),
                severity='critical',
                component='memory',
                description=f'Critical memory usage: {metrics.memory_usage}%',
                detected_at=datetime.now(),
                metrics={'memory_usage': metrics.memory_usage},
                suggested_actions=[
                    RecoveryAction.CLEAR_CACHE,
                    RecoveryAction.RESTART_SERVICE,
                    RecoveryAction.REBOOT_SERVER
                ]
            ))
            
        # Disk Analysis
        if metrics.disk_usage > self.thresholds.get('disk_critical', 90):
            issues.append(Issue(
                issue_id=self._generate_issue_id('disk_critical'),
                severity='critical',
                component='disk',
                description=f'Critical disk usage: {metrics.disk_usage}%',
                detected_at=datetime.now(),
                metrics={'disk_usage': metrics.disk_usage},
                suggested_actions=[RecoveryAction.DISK_CLEANUP, RecoveryAction.MANUAL_INTERVENTION]
            ))
            
        # Service Analysis
        for service, status in metrics.service_statuses.items():
            if not status:
                issues.append(Issue(
                    issue_id=self._generate_issue_id(f'service_down_{service}'),
                    severity='high',
                    component=f'service:{service}',
                    description=f'Service {service} is down',
                    detected_at=datetime.now(),
                    metrics={'service': service, 'status': status},
                    suggested_actions=[RecoveryAction.RESTART_SERVICE, RecoveryAction.RESTART_CONTAINER]
                ))
                
        # Container Analysis
        for container, status in metrics.container_statuses.items():
            if status not in ['running', 'healthy']:
                issues.append(Issue(
                    issue_id=self._generate_issue_id(f'container_unhealthy_{container}'),
                    severity='medium' if status == 'unhealthy' else 'high',
                    component=f'container:{container}',
                    description=f'Container {container} is {status}',
                    detected_at=datetime.now(),
                    metrics={'container': container, 'status': status},
                    suggested_actions=[RecoveryAction.RESTART_CONTAINER]
                ))
                
        # Network Analysis
        if metrics.network_latency > self.thresholds.get('network_latency_high', 1000):
            issues.append(Issue(
                issue_id=self._generate_issue_id('network_latency'),
                severity='medium',
                component='network',
                description=f'High network latency: {metrics.network_latency}ms',
                detected_at=datetime.now(),
                metrics={'latency': metrics.network_latency},
                suggested_actions=[RecoveryAction.NETWORK_RESET]
            ))
            
        # Learn from patterns
        self._learn_from_patterns(issues, metrics)
        
        return issues
        
    def _generate_issue_id(self, issue_type: str) -> str:
        """Generate unique issue ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{issue_type}_{timestamp}".encode()).hexdigest()[:12]
        
    def _learn_from_patterns(self, issues: List[Issue], metrics: HealthMetrics):
        """Learn from issue patterns for better prediction"""
        for issue in issues:
            pattern_hash = self._hash_pattern(issue, metrics)
            
            cursor = self.learning_db.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO patterns 
                (issue_type, pattern_hash, metrics, successful_action, success_rate, occurrences, last_seen)
                VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT occurrences FROM patterns WHERE pattern_hash = ?) + 1, 1),
                    ?)
            ''', (
                issue.component,
                pattern_hash,
                json.dumps(issue.metrics),
                None,  # Will be updated after recovery
                0.0,   # Will be calculated from history
                pattern_hash,
                datetime.now()
            ))
            self.learning_db.commit()
            
    def _hash_pattern(self, issue: Issue, metrics: HealthMetrics) -> str:
        """Create hash of issue pattern for learning"""
        pattern_data = {
            'component': issue.component,
            'severity': issue.severity,
            'cpu_range': int(metrics.cpu_usage / 10) * 10,
            'memory_range': int(metrics.memory_usage / 10) * 10,
            'disk_range': int(metrics.disk_usage / 10) * 10
        }
        return hashlib.md5(json.dumps(pattern_data, sort_keys=True).encode()).hexdigest()
        
    def get_best_action(self, issue: Issue) -> Optional[RecoveryAction]:
        """Get best recovery action based on learning history"""
        cursor = self.learning_db.cursor()
        
        # Look for successful past resolutions
        cursor.execute('''
            SELECT action, AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate, COUNT(*) as attempts
            FROM recovery_history
            WHERE issue_id LIKE ?
            GROUP BY action
            ORDER BY success_rate DESC, attempts DESC
            LIMIT 1
        ''', (f"%{issue.component}%",))
        
        result = cursor.fetchone()
        if result and result[1] > 0.7:  # 70% success rate threshold
            try:
                return RecoveryAction(result[0])
            except ValueError:
                pass
                
        # Fall back to suggested actions
        return issue.suggested_actions[0] if issue.suggested_actions else None
        
    def record_recovery_result(self, issue_id: str, action: RecoveryAction, success: bool, duration: float):
        """Record recovery attempt result for learning"""
        cursor = self.learning_db.cursor()
        cursor.execute('''
            INSERT INTO recovery_history (issue_id, action, success, duration_seconds, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (issue_id, action.value, success, duration, datetime.now()))
        self.learning_db.commit()


class RecoveryExecutor:
    """Execute recovery actions on the MiniCloud server"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_ip = config['server']['ip']
        self.ssh_user = config['server'].get('ssh_user', 'admin')
        self.ssh_key = config['server'].get('ssh_key', '~/.ssh/id_rsa')
        self.sudo_password = config['server'].get('sudo_password', '')
        
    async def execute_action(self, action: RecoveryAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a recovery action"""
        logger.info(f"Executing recovery action: {action.value} with context: {context}")
        
        try:
            if action == RecoveryAction.RESTART_SERVICE:
                return await self._restart_service(context.get('service', ''))
            elif action == RecoveryAction.RESTART_CONTAINER:
                return await self._restart_container(context.get('container', ''))
            elif action == RecoveryAction.REBOOT_SERVER:
                return await self._reboot_server()
            elif action == RecoveryAction.CLEAR_CACHE:
                return await self._clear_cache()
            elif action == RecoveryAction.DISK_CLEANUP:
                return await self._disk_cleanup()
            elif action == RecoveryAction.NETWORK_RESET:
                return await self._network_reset()
            elif action == RecoveryAction.PROCESS_KILL:
                return await self._kill_high_cpu_processes()
            elif action == RecoveryAction.CONFIG_REPAIR:
                return await self._repair_config(context)
            else:
                return False, f"Unknown action: {action.value}"
                
        except Exception as e:
            logger.error(f"Recovery action failed: {e}")
            return False, str(e)
            
    async def _execute_ssh_command(self, command: str, use_sudo: bool = False) -> Tuple[bool, str]:
        """Execute command on remote server via SSH"""
        if use_sudo and self.sudo_password:
            command = f"echo '{self.sudo_password}' | sudo -S {command}"
        elif use_sudo:
            command = f"sudo {command}"
            
        ssh_command = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            '-i', os.path.expanduser(self.ssh_key),
            f'{self.ssh_user}@{self.server_ip}',
            command
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *ssh_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode()
            else:
                return False, stderr.decode()
                
        except Exception as e:
            return False, str(e)
            
    async def _restart_service(self, service: str) -> Tuple[bool, str]:
        """Restart a system service"""
        if not service:
            return False, "No service specified"
            
        # Map friendly names to actual service names
        service_map = {
            'prometheus': 'prometheus',
            'grafana': 'grafana-server',
            'nextcloud': 'apache2',
            'docker': 'docker',
            'nginx': 'nginx',
            'mysql': 'mysql',
            'postgresql': 'postgresql'
        }
        
        actual_service = service_map.get(service, service)
        success, output = await self._execute_ssh_command(f"systemctl restart {actual_service}", use_sudo=True)
        
        if success:
            # Verify service is running
            verify_success, verify_output = await self._execute_ssh_command(
                f"systemctl is-active {actual_service}", use_sudo=True
            )
            if verify_success and 'active' in verify_output.lower():
                return True, f"Service {service} restarted successfully"
                
        return False, f"Failed to restart {service}: {output}"
        
    async def _restart_container(self, container: str) -> Tuple[bool, str]:
        """Restart a Docker container"""
        if not container:
            return False, "No container specified"
            
        success, output = await self._execute_ssh_command(f"docker restart {container}", use_sudo=True)
        
        if success:
            # Verify container is running
            verify_success, verify_output = await self._execute_ssh_command(
                f"docker inspect -f '{{{{.State.Running}}}}' {container}", use_sudo=True
            )
            if verify_success and 'true' in verify_output.lower():
                return True, f"Container {container} restarted successfully"
                
        return False, f"Failed to restart container {container}: {output}"
        
    async def _reboot_server(self) -> Tuple[bool, str]:
        """Reboot the server"""
        logger.warning("Initiating server reboot")
        
        # Schedule reboot in 1 minute to allow cleanup
        success, output = await self._execute_ssh_command("shutdown -r +1", use_sudo=True)
        
        if success:
            # Wait for server to come back online (max 5 minutes)
            await asyncio.sleep(90)  # Wait for shutdown to start
            
            for _ in range(30):  # Check every 10 seconds for 5 minutes
                if await self._ping_server():
                    return True, "Server rebooted successfully"
                await asyncio.sleep(10)
                
        return False, "Server reboot failed or timed out"
        
    async def _ping_server(self) -> bool:
        """Check if server is responsive"""
        try:
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '2', self.server_ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.communicate()
            return process.returncode == 0
        except:
            return False
            
    async def _clear_cache(self) -> Tuple[bool, str]:
        """Clear system caches"""
        commands = [
            "sync && echo 3 > /proc/sys/vm/drop_caches",  # Clear page cache
            "systemctl restart memcached 2>/dev/null || true",  # Restart memcached if exists
            "redis-cli FLUSHALL 2>/dev/null || true",  # Clear Redis if exists
        ]
        
        results = []
        for cmd in commands:
            success, output = await self._execute_ssh_command(cmd, use_sudo=True)
            results.append(success)
            
        if any(results):
            return True, "Cache cleared successfully"
        return False, "Failed to clear cache"
        
    async def _disk_cleanup(self) -> Tuple[bool, str]:
        """Clean up disk space"""
        commands = [
            "docker system prune -af --volumes",  # Clean Docker
            "apt-get autoremove -y && apt-get autoclean -y",  # Clean APT
            "find /var/log -type f -name '*.log' -mtime +30 -delete",  # Old logs
            "find /tmp -type f -atime +7 -delete",  # Old temp files
        ]
        
        freed_space = 0
        for cmd in commands:
            # Get disk usage before
            before_success, before_output = await self._execute_ssh_command("df / | tail -1 | awk '{print $4}'")
            before_space = int(before_output.strip()) if before_success else 0
            
            # Execute cleanup
            await self._execute_ssh_command(cmd, use_sudo=True)
            
            # Get disk usage after
            after_success, after_output = await self._execute_ssh_command("df / | tail -1 | awk '{print $4}'")
            after_space = int(after_output.strip()) if after_success else 0
            
            if before_space and after_space:
                freed_space += (after_space - before_space)
                
        if freed_space > 0:
            return True, f"Freed {freed_space / 1024 / 1024:.2f} GB of disk space"
        return False, "No significant disk space freed"
        
    async def _network_reset(self) -> Tuple[bool, str]:
        """Reset network configuration"""
        commands = [
            "systemctl restart networking",
            "ip link set dev eth0 down && ip link set dev eth0 up",
            "systemctl restart docker",  # Docker networking
        ]
        
        for cmd in commands:
            await self._execute_ssh_command(cmd, use_sudo=True)
            
        # Verify network is working
        if await self._ping_server():
            return True, "Network reset successfully"
        return False, "Network reset failed"
        
    async def _kill_high_cpu_processes(self) -> Tuple[bool, str]:
        """Kill processes with high CPU usage"""
        # Get top CPU consuming processes
        success, output = await self._execute_ssh_command(
            "ps aux --sort=-pcpu | head -6 | tail -5 | awk '{if($3 > 50) print $2}'",
            use_sudo=True
        )
        
        if success and output.strip():
            pids = output.strip().split('\n')
            killed = []
            
            for pid in pids:
                if pid.isdigit():
                    # Don't kill critical system processes
                    check_success, proc_info = await self._execute_ssh_command(f"ps -p {pid} -o comm=")
                    if check_success:
                        proc_name = proc_info.strip()
                        if proc_name not in ['systemd', 'kernel', 'init', 'sshd']:
                            kill_success, _ = await self._execute_ssh_command(f"kill -9 {pid}", use_sudo=True)
                            if kill_success:
                                killed.append(f"{pid}:{proc_name}")
                                
            if killed:
                return True, f"Killed high CPU processes: {', '.join(killed)}"
                
        return False, "No high CPU processes found or unable to kill"
        
    async def _repair_config(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Repair configuration files"""
        component = context.get('component', '')
        
        if not component:
            return False, "No component specified for config repair"
            
        # Backup and restore default configs
        config_repairs = {
            'nginx': [
                "cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak",
                "nginx -t || cp /etc/nginx/nginx.conf.default /etc/nginx/nginx.conf",
                "systemctl reload nginx"
            ],
            'docker': [
                "cp /etc/docker/daemon.json /etc/docker/daemon.json.bak 2>/dev/null || true",
                "echo '{}' > /etc/docker/daemon.json",
                "systemctl restart docker"
            ]
        }
        
        if component in config_repairs:
            for cmd in config_repairs[component]:
                await self._execute_ssh_command(cmd, use_sudo=True)
            return True, f"Configuration repaired for {component}"
            
        return False, f"No config repair available for {component}"


class MiniCloudMonitor:
    """Main monitoring and recovery orchestrator"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.diagnostic_engine = DiagnosticEngine(self.config)
        self.recovery_executor = RecoveryExecutor(self.config)
        self.metrics_collector = MetricsCollector(self.config)
        self.notification_manager = NotificationManager(self.config)
        self.widget_updater = WidgetUpdater(self.config)
        
        self.current_status = ServerStatus.UNKNOWN
        self.active_issues: Dict[str, Issue] = {}
        self.recovery_in_progress = False
        self.last_recovery_time = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file"""
        path = Path(config_path)
        if not path.exists():
            # Create default config
            default_config = {
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
                    "disk_critical": 90,
                    "network_latency_high": 1000
                },
                "monitoring": {
                    "check_interval": 30,
                    "recovery_cooldown": 300,
                    "max_recovery_attempts": 3
                },
                "notifications": {
                    "enabled": True,
                    "email": "",
                    "slack_webhook": "",
                    "pushover_token": ""
                },
                "ai": {
                    "openai_api_key": "",
                    "model": "gpt-4",
                    "enable_advanced_diagnostics": False
                }
            }
            
            path.parent.mkdir(exist_ok=True)
            with open(path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config
            
        with open(path, 'r') as f:
            return json.load(f)
            
    async def start(self):
        """Start monitoring loop"""
        logger.info("Starting MiniCloud AI Recovery System")
        
        while True:
            try:
                # Collect metrics
                metrics = await self.metrics_collector.collect()
                
                # Diagnose issues
                issues = self.diagnostic_engine.analyze_metrics(metrics)
                
                # Update status
                self._update_status(metrics, issues)
                
                # Update widget
                await self.widget_updater.update(self.current_status, metrics, issues)
                
                # Handle issues
                if issues and not self.recovery_in_progress:
                    await self._handle_issues(issues)
                    
                # Send notifications for critical issues
                critical_issues = [i for i in issues if i.severity == 'critical']
                if critical_issues:
                    await self.notification_manager.send_alert(critical_issues, self.current_status)
                    
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                logger.error(traceback.format_exc())
                
            # Wait for next check
            await asyncio.sleep(self.config['monitoring']['check_interval'])
            
    def _update_status(self, metrics: HealthMetrics, issues: List[Issue]):
        """Update overall server status"""
        if not issues:
            self.current_status = ServerStatus.HEALTHY
        elif any(i.severity == 'critical' for i in issues):
            self.current_status = ServerStatus.CRITICAL
        elif any(i.severity == 'high' for i in issues):
            self.current_status = ServerStatus.DEGRADED
        else:
            self.current_status = ServerStatus.DEGRADED
            
        if metrics.error_count > 5:
            self.current_status = ServerStatus.OFFLINE
            
    async def _handle_issues(self, issues: List[Issue]):
        """Handle detected issues with recovery actions"""
        # Check cooldown
        if self.last_recovery_time:
            cooldown = self.config['monitoring']['recovery_cooldown']
            if (datetime.now() - self.last_recovery_time).seconds < cooldown:
                logger.info("Recovery in cooldown period")
                return
                
        self.recovery_in_progress = True
        self.current_status = ServerStatus.RECOVERING
        
        # Sort issues by severity
        sorted_issues = sorted(issues, key=lambda x: ['low', 'medium', 'high', 'critical'].index(x.severity), reverse=True)
        
        for issue in sorted_issues[:3]:  # Handle top 3 issues
            logger.info(f"Handling issue: {issue.description}")
            
            # Get best recovery action
            action = self.diagnostic_engine.get_best_action(issue)
            
            if action:
                # Prepare context for action
                context = {'component': issue.component}
                if ':' in issue.component:
                    type_part, name_part = issue.component.split(':', 1)
                    context[type_part] = name_part
                    
                # Execute recovery
                start_time = time.time()
                success, message = await self.recovery_executor.execute_action(action, context)
                duration = time.time() - start_time
                
                # Record result
                self.diagnostic_engine.record_recovery_result(issue.issue_id, action, success, duration)
                
                if success:
                    issue.resolved = True
                    issue.resolution = message
                    logger.info(f"Recovery successful: {message}")
                    await self.notification_manager.send_recovery_notification(issue, action, message)
                else:
                    logger.error(f"Recovery failed: {message}")
                    
        self.recovery_in_progress = False
        self.last_recovery_time = datetime.now()


class MetricsCollector:
    """Collect system metrics from MiniCloud"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prometheus_url = config['server']['prometheus_url']
        
    async def collect(self) -> HealthMetrics:
        """Collect current metrics"""
        metrics = HealthMetrics()
        
        try:
            # Query Prometheus for metrics
            metrics.cpu_usage = await self._query_prometheus(
                '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            )
            metrics.memory_usage = await self._query_prometheus(
                '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
            )
            metrics.disk_usage = await self._query_prometheus(
                '(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100'
            )
            metrics.uptime_seconds = int(await self._query_prometheus(
                'node_time_seconds - node_boot_time_seconds'
            ) or 0)
            
            # Check services
            metrics.service_statuses = await self._check_services()
            
            # Check containers
            metrics.container_statuses = await self._check_containers()
            
            # Check network latency
            metrics.network_latency = await self._check_network_latency()
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            metrics.error_count += 1
            
        metrics.last_check = datetime.now()
        return metrics
        
    async def _query_prometheus(self, query: str) -> float:
        """Query Prometheus for a metric"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': query},
                    timeout=5
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success' and data['data']['result']:
                    return float(data['data']['result'][0]['value'][1])
        except:
            pass
        return 0.0
        
    async def _check_services(self) -> Dict[str, bool]:
        """Check status of key services"""
        services = {}
        endpoints = {
            'prometheus': f"{self.prometheus_url}/-/healthy",
            'grafana': f"{self.config['server']['grafana_url']}/api/health",
            'nextcloud': f"http://{self.config['server']['ip']}:8080/status.php"
        }
        
        for service, url in endpoints.items():
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda u=url: requests.get(u, timeout=3)
                )
                services[service] = response.status_code == 200
            except:
                services[service] = False
                
        return services
        
    async def _check_containers(self) -> Dict[str, str]:
        """Check Docker container statuses"""
        containers = {}
        
        # This would normally SSH to server and check docker ps
        # For now, return empty dict
        return containers
        
    async def _check_network_latency(self) -> float:
        """Check network latency to server"""
        try:
            start = time.time()
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(f"http://{self.config['server']['ip']}", timeout=2)
            )
            return (time.time() - start) * 1000  # Convert to ms
        except:
            return 9999.0  # High value indicates problem


class NotificationManager:
    """Manage notifications for issues and recoveries"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config['notifications']['enabled']
        
    async def send_alert(self, issues: List[Issue], status: ServerStatus):
        """Send alert for critical issues"""
        if not self.enabled:
            return
            
        # Format message
        message = f"MiniCloud Status: {status.value.upper()}\n\n"
        for issue in issues:
            message += f"- [{issue.severity.upper()}] {issue.description}\n"
            
        # Send via configured channels
        await self._send_macos_notification("MiniCloud Alert", message[:200])
        
    async def send_recovery_notification(self, issue: Issue, action: RecoveryAction, message: str):
        """Send notification about successful recovery"""
        if not self.enabled:
            return
            
        notification = f"Recovered: {issue.description}\nAction: {action.value}\n{message}"
        await self._send_macos_notification("MiniCloud Recovery", notification[:200])
        
    async def _send_macos_notification(self, title: str, message: str):
        """Send macOS notification"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ])
        except:
            pass


class WidgetUpdater:
    """Update MiniCloud widget status"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.widget_config_path = Path.home() / 'minicloud-widget' / 'config.json'
        self.status_file = Path.home() / '.minicloud' / 'status.json'
        
    async def update(self, status: ServerStatus, metrics: HealthMetrics, issues: List[Issue]):
        """Update widget with current status"""
        # Create status file for widget to read
        self.status_file.parent.mkdir(exist_ok=True)
        
        status_data = {
            'status': status.value,
            'metrics': {
                'cpu': metrics.cpu_usage,
                'memory': metrics.memory_usage,
                'disk': metrics.disk_usage,
                'uptime': metrics.uptime_seconds,
                'services': metrics.service_statuses,
                'network_latency': metrics.network_latency
            },
            'issues': [
                {
                    'id': issue.issue_id,
                    'severity': issue.severity,
                    'description': issue.description,
                    'resolved': issue.resolved
                }
                for issue in issues
            ],
            'last_update': datetime.now().isoformat(),
            'recovery_in_progress': status == ServerStatus.RECOVERING
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
        # Update widget config with correct icon
        if self.widget_config_path.exists():
            with open(self.widget_config_path, 'r') as f:
                widget_config = json.load(f)
                
            # Update status icons based on actual status
            icon_map = {
                ServerStatus.HEALTHY: widget_config['display']['status_icons']['normal'],
                ServerStatus.DEGRADED: widget_config['display']['status_icons']['warning'],
                ServerStatus.CRITICAL: widget_config['display']['status_icons']['critical'],
                ServerStatus.OFFLINE: widget_config['display']['status_icons']['offline'],
                ServerStatus.RECOVERING: '🔄',
                ServerStatus.UNKNOWN: '❓'
            }
            
            # Write updated status to trigger widget refresh
            widget_config['current_status'] = status.value
            widget_config['current_icon'] = icon_map.get(status, '☁️')
            
            with open(self.widget_config_path, 'w') as f:
                json.dump(widget_config, f, indent=2)


async def main():
    """Main entry point"""
    config_path = Path.home() / '.minicloud' / 'ai_recovery_config.json'
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down MiniCloud AI Recovery System")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    monitor = MiniCloudMonitor(str(config_path))
    await monitor.start()


if __name__ == "__main__":
    asyncio.run(main())