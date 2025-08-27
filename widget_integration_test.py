#!/usr/bin/env python3
"""
Minicloud Widget Integration Test Suite
Tests widget connectivity, caching, and status reporting functionality
"""

import asyncio
import time
import json
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from minicloud_widget_enhanced import EnhancedMiniacloudWidget, ConnectivityStatus


class WidgetIntegrationTest:
    """Comprehensive widget integration testing"""
    
    def __init__(self):
        self.test_results = []
    
    async def run_all_tests(self) -> bool:
        """Run complete test suite"""
        print("🧪 Starting Widget Integration Tests")
        print("=" * 50)
        
        tests = [
            self.test_basic_connectivity,
            self.test_caching_mechanism,
            self.test_multi_interface_detection,
            self.test_service_discovery,
            self.test_status_reporting,
            self.test_error_handling,
            self.test_performance
        ]
        
        for test in tests:
            try:
                print(f"\n🔍 Running {test.__name__}...")
                success = await test()
                
                self.test_results.append({
                    'test': test.__name__,
                    'status': 'PASS' if success else 'FAIL',
                    'timestamp': time.time()
                })
                
                status_emoji = '✅' if success else '❌'
                print(f"{status_emoji} {test.__name__}: {'PASS' if success else 'FAIL'}")
                
            except Exception as e:
                print(f"💥 {test.__name__} failed with exception: {e}")
                self.test_results.append({
                    'test': test.__name__,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': time.time()
                })
        
        # Print summary
        await self.print_test_summary()
        
        # Return overall success
        return all(result['status'] == 'PASS' for result in self.test_results)
    
    async def test_basic_connectivity(self) -> bool:
        """Test basic connectivity detection"""
        async with EnhancedMiniacloudWidget() as widget:
            status = await widget.get_status(force_refresh=True)
            
            # Check that we got a valid status
            if not isinstance(status.status, ConnectivityStatus):
                print("  ❌ Invalid status type returned")
                return False
            
            if not status.server_ip:
                print("  ❌ No server IP detected")
                return False
            
            if not status.connection_tests:
                print("  ❌ No connection tests performed")
                return False
            
            print(f"  ✅ Status: {status.status.value}, IP: {status.server_ip}")
            print(f"  ✅ Connection tests: {len(status.connection_tests)}")
            
            return True
    
    async def test_caching_mechanism(self) -> bool:
        """Test status caching functionality"""
        async with EnhancedMiniacloudWidget() as widget:
            # First call - should not be cached
            start_time = time.time()
            status1 = await widget.get_status(force_refresh=True)
            first_call_time = time.time() - start_time
            
            if status1.cache_hit:
                print("  ❌ First call should not be cached")
                return False
            
            # Second call - should be cached
            start_time = time.time()
            status2 = await widget.get_status()
            second_call_time = time.time() - start_time
            
            if not status2.cache_hit:
                print("  ❌ Second call should be cached")
                return False
            
            # Cached call should be much faster
            if second_call_time > first_call_time * 0.1:  # Should be at least 10x faster
                print(f"  ⚠️  Cached call not significantly faster: {second_call_time:.3f}s vs {first_call_time:.3f}s")
            
            print(f"  ✅ Cache working: {first_call_time:.3f}s -> {second_call_time:.3f}s")
            
            return True
    
    async def test_multi_interface_detection(self) -> bool:
        """Test multi-interface network detection"""
        async with EnhancedMiniacloudWidget() as widget:
            status = await widget.get_status(force_refresh=True)
            
            if not status.interfaces:
                print("  ❌ No interfaces detected")
                return False
            
            # Check for expected interface types
            expected_interfaces = ['ethernet', 'wireless', 'local_config']
            found_interfaces = list(status.interfaces.keys())
            
            print(f"  ✅ Found interfaces: {found_interfaces}")
            
            # At least one interface should be detected
            if len(found_interfaces) == 0:
                print("  ❌ No network interfaces found")
                return False
            
            return True
    
    async def test_service_discovery(self) -> bool:
        """Test service availability detection"""
        async with EnhancedMiniacloudWidget() as widget:
            status = await widget.get_status(force_refresh=True)
            
            if not status.services:
                print("  ❌ No services detected")
                return False
            
            # Check expected services
            service_names = [s.name for s in status.services]
            expected_services = ['SSH', 'HTTP', 'Nextcloud']
            
            found_expected = [s for s in expected_services if s in service_names]
            print(f"  ✅ Found services: {service_names}")
            print(f"  ✅ Expected services found: {found_expected}")
            
            # At least SSH should be accessible if server is online
            if status.status == ConnectivityStatus.ONLINE:
                ssh_accessible = any(s.accessible for s in status.services if s.name == 'SSH')
                if not ssh_accessible:
                    print("  ⚠️  SSH not accessible despite online status")
            
            return True
    
    async def test_status_reporting(self) -> bool:
        """Test status reporting formats"""
        async with EnhancedMiniacloudWidget() as widget:
            status = await widget.get_status(force_refresh=True)
            
            # Test simple status
            simple = widget.get_simple_status(status)
            if not simple or not any(emoji in simple for emoji in ['🟢', '🟡', '🔴', '❓']):
                print(f"  ❌ Invalid simple status: {simple}")
                return False
            
            # Test detailed status
            detailed = widget.get_detailed_status(status)
            if not detailed or len(detailed) < 10:
                print(f"  ❌ Invalid detailed status: {detailed}")
                return False
            
            # Test JSON export
            json_status = widget.export_json_status(status)
            try:
                parsed = json.loads(json_status)
                if 'status' not in parsed or 'timestamp' not in parsed:
                    print("  ❌ Invalid JSON structure")
                    return False
            except json.JSONDecodeError:
                print("  ❌ Invalid JSON format")
                return False
            
            print(f"  ✅ Simple: {simple}")
            print(f"  ✅ Detailed: {detailed[:60]}...")
            print(f"  ✅ JSON: Valid structure")
            
            return True
    
    async def test_error_handling(self) -> bool:
        """Test error handling and resilience"""
        async with EnhancedMiniacloudWidget() as widget:
            # Override config with invalid IPs to test error handling
            original_ips = widget.config['server_ips']
            widget.config['server_ips'] = ['192.168.99.99', '10.0.0.99']  # Non-existent IPs
            
            try:
                status = await widget.get_status(force_refresh=True)
                
                # Should still return a status (likely offline)
                if not status:
                    print("  ❌ No status returned on error")
                    return False
                
                if status.status not in [ConnectivityStatus.OFFLINE, ConnectivityStatus.UNKNOWN]:
                    print(f"  ❌ Expected offline/unknown status, got: {status.status}")
                    return False
                
                print(f"  ✅ Error handled gracefully: {status.status.value}")
                
            finally:
                # Restore original config
                widget.config['server_ips'] = original_ips
            
            return True
    
    async def test_performance(self) -> bool:
        """Test performance characteristics"""
        async with EnhancedMiniacloudWidget() as widget:
            # Test response time
            start_time = time.time()
            status = await widget.get_status(force_refresh=True)
            response_time = time.time() - start_time
            
            # Should complete within reasonable time (10 seconds)
            if response_time > 10.0:
                print(f"  ❌ Slow response time: {response_time:.2f}s")
                return False
            
            # Test cached response time
            start_time = time.time()
            cached_status = await widget.get_status()
            cached_time = time.time() - start_time
            
            # Cached response should be very fast
            if cached_time > 0.1:
                print(f"  ⚠️  Slow cached response: {cached_time:.3f}s")
            
            print(f"  ✅ Performance: {response_time:.2f}s (fresh), {cached_time:.3f}s (cached)")
            
            return True
    
    async def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 50)
        print("🧪 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.test_results if r['status'] == 'ERROR')
        total = len(self.test_results)
        
        for result in self.test_results:
            status_emoji = {'PASS': '✅', 'FAIL': '❌', 'ERROR': '💥'}[result['status']]
            print(f"{status_emoji} {result['test']}: {result['status']}")
            
            if 'error' in result:
                print(f"    Error: {result['error']}")
        
        print("-" * 50)
        print(f"📊 TOTALS: {passed} passed, {failed} failed, {errors} errors ({total} total)")
        
        if failed == 0 and errors == 0:
            print("🎉 All tests passed! Widget is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the issues above.")
        
        print("=" * 50)


async def main():
    """Main test runner"""
    tester = WidgetIntegrationTest()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())