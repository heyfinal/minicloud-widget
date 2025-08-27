#!/usr/bin/env python3
"""
Enhanced Minicloud Widget with Dual-Interface Connectivity
Production-ready widget with intelligent caching, multi-path testing, and resilient connectivity detection
"""

import asyncio
import aiohttp
import json
import time
import socket
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.minicloud_widget.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """Connectivity status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ConnectionTest:
    """Individual connection test result"""
    method: str
    success: bool
    response_time: float
    error: Optional[str] = None
    details: Dict[str, Any] = None


@dataclass
class ServiceStatus:
    """Service availability status"""
    name: str
    port: int
    accessible: bool
    response_time: float
    error: Optional[str] = None


@dataclass
class WidgetStatus:
    """Complete widget status"""
    timestamp: float
    status: ConnectivityStatus
    server_ip: str
    interfaces: Dict[str, Dict[str, Any]]
    services: List[ServiceStatus]
    connection_tests: List[ConnectionTest]
    uptime_percentage: float
    last_seen_online: float
    cache_hit: bool = False


class EnhancedMiniacloudWidget:
    """Production-ready minicloud widget with enhanced connectivity detection"""
    
    def __init__(self):
        self.config = {
            'server_ips': ['192.168.2.2', '192.168.1.229'],  # Primary and fallback IPs
            'test_ports': [22, 80, 443, 8080],
            'timeout': 5.0,
            'cache_duration': 30,  # seconds
            'max_retries': 2,
            'failure_threshold': 3,
            'interfaces': {
                'ethernet': {'subnet': '192.168.2.0/24', 'gateway': '192.168.2.1'},
                'wireless': {'subnet': '192.168.1.0/24', 'gateway': '192.168.1.254'}
            }
        }
        
        # Cache and status tracking
        self.status_cache: Optional[WidgetStatus] = None
        self.cache_timestamp: float = 0
        self.failure_count: int = 0
        self.last_online_time: float = time.time()
        self.uptime_tracking: List[Tuple[float, bool]] = []
        
        # Network session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_status(self, force_refresh: bool = False) -> WidgetStatus:
        """Get current minicloud status with intelligent caching"""
        current_time = time.time()
        
        # Return cached result if valid
        if (not force_refresh and 
            self.status_cache and 
            current_time - self.cache_timestamp < self.config['cache_duration']):
            
            self.status_cache.cache_hit = True
            return self.status_cache
        
        # Perform fresh status check
        try:
            status = await self._perform_comprehensive_check()
            
            # Update cache
            self.status_cache = status
            self.cache_timestamp = current_time
            
            # Update failure tracking
            if status.status == ConnectivityStatus.ONLINE:
                self.failure_count = 0
                self.last_online_time = current_time
            else:
                self.failure_count += 1
            
            # Update uptime tracking
            self.uptime_tracking.append((current_time, status.status == ConnectivityStatus.ONLINE))
            
            # Keep only last 1000 data points
            if len(self.uptime_tracking) > 1000:
                self.uptime_tracking = self.uptime_tracking[-1000:]
            
            return status
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            
            # Return cached status if available, otherwise unknown
            if self.status_cache:
                return self.status_cache
            
            return WidgetStatus(
                timestamp=current_time,
                status=ConnectivityStatus.UNKNOWN,
                server_ip="unknown",
                interfaces={},
                services=[],
                connection_tests=[],
                uptime_percentage=0.0,
                last_seen_online=self.last_online_time
            )
    
    async def _perform_comprehensive_check(self) -> WidgetStatus:
        """Perform comprehensive connectivity check across all methods"""
        start_time = time.time()
        
        # Discover active server IP
        server_ip = await self._discover_server_ip()
        
        # Test multiple connectivity methods
        connection_tests = await self._test_connectivity_methods(server_ip)
        
        # Test service availability
        services = await self._test_services(server_ip)
        
        # Analyze network interfaces
        interfaces = await self._analyze_interfaces()
        
        # Determine overall status
        status = self._determine_status(connection_tests, services)
        
        # Calculate uptime percentage
        uptime_percentage = self._calculate_uptime_percentage()
        
        return WidgetStatus(
            timestamp=time.time(),
            status=status,
            server_ip=server_ip,
            interfaces=interfaces,
            services=services,
            connection_tests=connection_tests,
            uptime_percentage=uptime_percentage,
            last_seen_online=self.last_online_time,
            cache_hit=False
        )
    
    async def _discover_server_ip(self) -> str:
        """Discover the active server IP address"""
        for ip in self.config['server_ips']:
            try:
                # Quick ping test
                result = await self._run_command(['ping', '-c', '1', '-W', '2', ip])
                if result[0] == 0:  # Success
                    return ip
            except:
                continue
        
        return self.config['server_ips'][0]  # Fallback to primary
    
    async def _test_connectivity_methods(self, server_ip: str) -> List[ConnectionTest]:
        """Test multiple connectivity methods"""
        tests = []
        
        # Test 1: ICMP Ping
        test_result = await self._test_ping(server_ip)
        tests.append(test_result)
        
        # Test 2: TCP Port Connectivity
        for port in [22, 80, 8080]:  # Essential ports
            test_result = await self._test_tcp_port(server_ip, port)
            tests.append(test_result)
        
        # Test 3: HTTP Endpoint
        test_result = await self._test_http_endpoint(server_ip)
        tests.append(test_result)
        
        return tests
    
    async def _test_ping(self, ip: str) -> ConnectionTest:
        """Test ICMP ping connectivity"""
        start_time = time.time()
        
        try:
            returncode, stdout, stderr = await self._run_command(
                ['ping', '-c', '1', '-W', '3', ip]
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if returncode == 0:
                # Extract actual ping time from output
                import re
                match = re.search(r'time=(\d+\.?\d*)', stdout)
                if match:
                    actual_ping_time = float(match.group(1))
                    response_time = actual_ping_time
                
                return ConnectionTest(
                    method="ping",
                    success=True,
                    response_time=response_time,
                    details={'stdout': stdout.strip()}
                )
            else:
                return ConnectionTest(
                    method="ping",
                    success=False,
                    response_time=response_time,
                    error=stderr.strip()
                )
                
        except Exception as e:
            return ConnectionTest(
                method="ping",
                success=False,
                response_time=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _test_tcp_port(self, ip: str, port: int) -> ConnectionTest:
        """Test TCP port connectivity"""
        start_time = time.time()
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.config['timeout']
            )
            
            writer.close()
            await writer.wait_closed()
            
            response_time = (time.time() - start_time) * 1000
            
            return ConnectionTest(
                method=f"tcp_port_{port}",
                success=True,
                response_time=response_time,
                details={'port': port}
            )
            
        except Exception as e:
            return ConnectionTest(
                method=f"tcp_port_{port}",
                success=False,
                response_time=(time.time() - start_time) * 1000,
                error=str(e),
                details={'port': port}
            )
    
    async def _test_http_endpoint(self, ip: str) -> ConnectionTest:
        """Test HTTP endpoint connectivity"""
        start_time = time.time()
        
        endpoints = [
            f"http://{ip}:8080/status",
            f"http://{ip}:80/",
            f"http://{ip}:8080/"
        ]
        
        for endpoint in endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    return ConnectionTest(
                        method="http",
                        success=response.status < 400,
                        response_time=response_time,
                        details={
                            'endpoint': endpoint,
                            'status_code': response.status,
                            'headers': dict(response.headers)
                        }
                    )
                    
            except Exception as e:
                continue
        
        # All endpoints failed
        return ConnectionTest(
            method="http",
            success=False,
            response_time=(time.time() - start_time) * 1000,
            error="All HTTP endpoints failed"
        )
    
    async def _test_services(self, server_ip: str) -> List[ServiceStatus]:
        """Test individual service availability"""
        services = []
        
        service_configs = [
            {"name": "SSH", "port": 22},
            {"name": "HTTP", "port": 80},
            {"name": "HTTPS", "port": 443},
            {"name": "Nextcloud", "port": 8080}
        ]
        
        for config in service_configs:
            start_time = time.time()
            
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(server_ip, config["port"]),
                    timeout=3.0
                )
                
                writer.close()
                await writer.wait_closed()
                
                services.append(ServiceStatus(
                    name=config["name"],
                    port=config["port"],
                    accessible=True,
                    response_time=(time.time() - start_time) * 1000
                ))
                
            except Exception as e:
                services.append(ServiceStatus(
                    name=config["name"],
                    port=config["port"],
                    accessible=False,
                    response_time=(time.time() - start_time) * 1000,
                    error=str(e)
                ))
        
        return services
    
    async def _analyze_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Analyze local network interfaces"""
        interfaces = {}
        
        try:
            # Get local network configuration
            returncode, stdout, stderr = await self._run_command(['ifconfig'])
            if returncode == 0:
                interfaces['local_config'] = {'raw_output': stdout[:1000]}  # Truncate
            
            # Test gateway connectivity
            for name, config in self.config['interfaces'].items():
                gateway = config['gateway']
                
                start_time = time.time()
                returncode, _, _ = await self._run_command(
                    ['ping', '-c', '1', '-W', '2', gateway]
                )
                
                interfaces[name] = {
                    'gateway': gateway,
                    'reachable': returncode == 0,
                    'response_time': (time.time() - start_time) * 1000,
                    'subnet': config['subnet']
                }
        
        except Exception as e:
            logger.warning(f"Interface analysis failed: {e}")
        
        return interfaces
    
    def _determine_status(self, connection_tests: List[ConnectionTest], 
                         services: List[ServiceStatus]) -> ConnectivityStatus:
        """Determine overall connectivity status"""
        
        # Count successful tests
        successful_connections = sum(1 for test in connection_tests if test.success)
        accessible_services = sum(1 for service in services if service.accessible)
        
        # Determine status based on test results
        if successful_connections >= 2 and accessible_services >= 1:
            return ConnectivityStatus.ONLINE
        elif successful_connections >= 1 or accessible_services >= 1:
            return ConnectivityStatus.DEGRADED
        else:
            return ConnectivityStatus.OFFLINE
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage from recent tracking data"""
        if not self.uptime_tracking:
            return 100.0
        
        # Consider only last hour of data
        one_hour_ago = time.time() - 3600
        recent_data = [(t, online) for t, online in self.uptime_tracking if t > one_hour_ago]
        
        if not recent_data:
            return 100.0
        
        online_count = sum(1 for _, online in recent_data if online)
        total_count = len(recent_data)
        
        return (online_count / total_count) * 100.0
    
    async def _run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run system command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return (
                process.returncode,
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore')
            )
            
        except Exception as e:
            return 1, "", str(e)
    
    def get_simple_status(self, status: WidgetStatus) -> str:
        """Get simple status string for basic widgets"""
        if status.status == ConnectivityStatus.ONLINE:
            return "🟢 Online"
        elif status.status == ConnectivityStatus.DEGRADED:
            return "🟡 Degraded"
        elif status.status == ConnectivityStatus.OFFLINE:
            return "🔴 Offline"
        else:
            return "❓ Unknown"
    
    def get_detailed_status(self, status: WidgetStatus) -> str:
        """Get detailed status string with metrics"""
        simple = self.get_simple_status(status)
        
        if status.status != ConnectivityStatus.OFFLINE:
            accessible_services = sum(1 for s in status.services if s.accessible)
            total_services = len(status.services)
            
            return (
                f"{simple} | {status.server_ip} | "
                f"{accessible_services}/{total_services} services | "
                f"{status.uptime_percentage:.1f}% uptime"
            )
        else:
            offline_duration = time.time() - status.last_seen_online
            return f"{simple} | Last seen: {offline_duration/60:.0f}m ago"
    
    def export_json_status(self, status: WidgetStatus) -> str:
        """Export status as JSON for advanced widgets"""
        return json.dumps(asdict(status), indent=2)


# Command-line interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Minicloud Widget')
    parser.add_argument('--simple', action='store_true', 
                       help='Simple status output')
    parser.add_argument('--detailed', action='store_true',
                       help='Detailed status output')
    parser.add_argument('--json', action='store_true',
                       help='JSON status output')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force cache refresh')
    parser.add_argument('--monitor', type=int, metavar='SECONDS',
                       help='Monitor mode with update interval')
    
    args = parser.parse_args()
    
    async with EnhancedMiniacloudWidget() as widget:
        if args.monitor:
            # Monitor mode
            print("🔄 Starting minicloud monitoring...")
            try:
                while True:
                    status = await widget.get_status(force_refresh=True)
                    
                    if args.json:
                        print(widget.export_json_status(status))
                    elif args.detailed:
                        print(f"[{time.strftime('%H:%M:%S')}] {widget.get_detailed_status(status)}")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] {widget.get_simple_status(status)}")
                    
                    await asyncio.sleep(args.monitor)
            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped")
        else:
            # Single check mode
            status = await widget.get_status(force_refresh=args.force_refresh)
            
            if args.json:
                print(widget.export_json_status(status))
            elif args.detailed:
                print(widget.get_detailed_status(status))
            else:
                print(widget.get_simple_status(status))


if __name__ == '__main__':
    asyncio.run(main())