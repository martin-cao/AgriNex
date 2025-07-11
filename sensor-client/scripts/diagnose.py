#!/usr/bin/env python3
"""
System diagnosis script for AgriNex Sensor Client.
"""

import sys
import platform
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from src.core.config import Config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️  Warning: Could not import Config class")
import serial.tools.list_ports
import paho.mqtt.client as mqtt


def check_python_version():
    """Check Python version compatibility."""
    print("=== Python Version Check ===")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False


def check_dependencies():
    """Check required dependencies."""
    print("\n=== Dependencies Check ===")
    required_packages = [
        ('paho-mqtt', mqtt),
        ('pyserial', serial),
    ]
    
    all_available = True
    for name, package in required_packages:
        try:
            version = getattr(package, '__version__', 'unknown')
            print(f"✅ {name}: {version}")
        except Exception as e:
            print(f"❌ {name}: not available ({e})")
            all_available = False
    
    return all_available


def check_serial_ports():
    """Check available serial ports."""
    print("\n=== Serial Ports Check ===")
    try:
        ports = serial.tools.list_ports.comports()
        if ports:
            print(f"Found {len(ports)} serial ports:")
            for port in ports:
                print(f"  - {port.device}: {port.description}")
        else:
            print("No serial ports detected")
            print("💡 This is normal in containerized environments")
        
        # Check platform-specific ports
        system = platform.system()
        print(f"\nPlatform: {system}")
        if system == "Linux":
            print("Expected serial ports: /dev/ttyS*, /dev/ttyUSB*")
        elif system == "Windows":
            print("Expected serial ports: COM*")
        elif system == "Darwin":
            print("Expected serial ports: /dev/tty.*, /dev/cu.*")
        
        return True
    except Exception as e:
        print(f"❌ Error checking serial ports: {e}")
        return False


def check_mqtt_connection(host="localhost", port=1883):
    """Check MQTT broker connectivity."""
    print(f"\n=== MQTT Connection Check ({host}:{port}) ===")
    try:
        client = mqtt.Client(client_id="diagnosis_client")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("✅ Connected to MQTT broker")
                client.disconnect()
            else:
                print(f"❌ Failed to connect to MQTT broker (code: {rc})")
        
        def on_disconnect(client, userdata, rc):
            print("Disconnected from MQTT broker")
        
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        
        print(f"Attempting to connect to {host}:{port}...")
        client.connect(host, port, 60)
        client.loop_start()
        
        import time
        time.sleep(2)  # Wait for connection
        client.loop_stop()
        
        return True
    except Exception as e:
        print(f"❌ MQTT connection failed: {e}")
        return False


def check_configuration():
    """Check configuration files."""
    print("\n=== Configuration Check ===")
    
    config_files = [
        "config/sensor_client.json",
        "config/docker.json"
    ]
    
    configs_ok = True
    for config_file in config_files:
        config_path = Path(__file__).parent.parent / config_file
        try:
            if config_path.exists():
                with open(config_path) as f:
                    config_data = json.load(f)
                print(f"✅ {config_file}: valid JSON")
                
                # Load using Config class
                if CONFIG_AVAILABLE:
                    config = Config.from_file(str(config_path))
                    print(f"   Client ID: {config.client_id}")
                    print(f"   MQTT Host: {config.mqtt.host}:{config.mqtt.port}")
                    print(f"   Simulation Mode: {config.serial.simulation_mode}")
                else:
                    print("   (Config class not available for validation)")
            else:
                print(f"⚠️  {config_file}: not found")
        except Exception as e:
            print(f"❌ {config_file}: error loading ({e})")
            configs_ok = False
    
    return configs_ok


def check_environment():
    """Check environment setup."""
    print("\n=== Environment Check ===")
    
    # Check environment variables
    env_vars = [
        'MQTT_HOST',
        'MQTT_PORT', 
        'SENSOR_CLIENT_ID',
        'PYTHONPATH'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: not set")
    
    # Check file system
    important_dirs = ['src', 'config', 'logs', 'scripts']
    for dir_name in important_dirs:
        dir_path = Path(__file__).parent.parent / dir_name
        if dir_path.exists():
            print(f"✅ Directory {dir_name}: exists")
        else:
            print(f"❌ Directory {dir_name}: missing")
    
    return True


def main():
    """Run complete system diagnosis."""
    print("🔍 AgriNex Sensor Client - System Diagnosis")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Serial Ports", check_serial_ports),
        ("Configuration", check_configuration),
        ("Environment", check_environment),
    ]
    
    # Add MQTT check if config available
    try:
        if CONFIG_AVAILABLE:
            config_path = Path(__file__).parent.parent / "config/sensor_client.json"
            config = Config.from_file(str(config_path))
            checks.append(("MQTT Connection", lambda: check_mqtt_connection(config.mqtt.host, config.mqtt.port)))
        else:
            checks.append(("MQTT Connection", lambda: check_mqtt_connection()))
    except:
        checks.append(("MQTT Connection", lambda: check_mqtt_connection()))
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: Error during check ({e})")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("🎉 System is ready for operation!")
    else:
        print("⚠️  Some issues detected. Please resolve before running.")
        print("\n💡 Tips:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check MQTT broker is running")
        print("- Verify configuration files")
    
    return passed == len(results)


if __name__ == "__main__":
    import os
    success = main()
    sys.exit(0 if success else 1)
