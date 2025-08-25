#!/usr/bin/env python3
"""
Test script for MiniCloud AI Recovery System
Validates components and connectivity
"""

import sys
import json
import subprocess
import requests
from pathlib import Path
import time

def test_ssh_connection(config):
    """Test SSH connectivity to server"""
    print("Testing SSH connection...", end=" ")
    cmd = [
        'ssh', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=no',
        '-i', config['server']['ssh_key'].replace('~', str(Path.home())),
        f"{config['server']['ssh_user']}@{config['server']['ip']}",
        'echo "OK"'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "OK" in result.stdout:
            print("✅ SUCCESS")
            return True
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_prometheus(config):
    """Test Prometheus connectivity"""
    print("Testing Prometheus...", end=" ")
    try:
        response = requests.get(f"{config['server']['prometheus_url']}/-/healthy", timeout=5)
        if response.status_code == 200:
            print("✅ SUCCESS")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_metrics_collection(config):
    """Test metric collection"""
    print("Testing metric collection...", end=" ")
    try:
        query = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        response = requests.get(
            f"{config['server']['prometheus_url']}/api/v1/query",
            params={'query': query},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print("✅ SUCCESS")
                return True
        print("❌ FAILED: No data")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_widget_config():
    """Test widget configuration"""
    print("Testing widget config...", end=" ")
    config_path = Path.home() / 'minicloud-widget' / 'config.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            if 'server' in config and 'monitoring' in config:
                print("✅ SUCCESS")
                return True
        except:
            pass
    print("❌ FAILED: Invalid or missing config")
    return False

def test_ai_recovery_config():
    """Test AI recovery configuration"""
    print("Testing AI recovery config...", end=" ")
    config_path = Path.home() / '.minicloud' / 'ai_recovery_config.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            if 'server' in config and 'thresholds' in config:
                print("✅ SUCCESS")
                return config
        except:
            pass
    print("❌ FAILED: Invalid or missing config")
    return None

def test_python_modules():
    """Test required Python modules"""
    print("Testing Python modules...")
    modules = ['rumps', 'requests', 'psutil', 'asyncio', 'paramiko']
    all_good = True
    
    for module in modules:
        print(f"  • {module}...", end=" ")
        try:
            __import__(module)
            print("✅")
        except ImportError:
            print("❌ NOT INSTALLED")
            all_good = False
    
    return all_good

def test_claude_ns():
    """Test claude-ns fix"""
    print("Testing claude-ns...", end=" ")
    try:
        result = subprocess.run(
            ['claude-ns', '--neuralsync-status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ SUCCESS")
            return True
        else:
            print(f"❌ FAILED: {result.stderr[:100]}")
            return False
    except FileNotFoundError:
        print("❌ NOT FOUND")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    print("=" * 60)
    print("MiniCloud AI Recovery System - Component Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test Python modules
    results.append(("Python Modules", test_python_modules()))
    
    # Test configurations
    results.append(("Widget Config", test_widget_config()))
    config = test_ai_recovery_config()
    results.append(("AI Recovery Config", config is not None))
    
    if config:
        # Test connectivity
        results.append(("SSH Connection", test_ssh_connection(config)))
        results.append(("Prometheus", test_prometheus(config)))
        results.append(("Metrics Collection", test_metrics_collection(config)))
    
    # Test claude-ns
    results.append(("Claude-NS", test_claude_ns()))
    
    print()
    print("=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<30} {status}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())