# AgriNex Sensor Client v2.0

🌱 **Modern, modular sensor data collection system for agricultural monitoring**

## ✨ Features

- **🏗️ Clean Architecture**: Modular design with separation of concerns
- **📡 MQTT Communication**: Reliable data transmission to AgriNex backend
- **🔌 Serial Interface**: Support for real and simulated sensors
- **🐳 Docker Ready**: Containerized deployment support
- **📊 Real-time Monitoring**: Live sensor data collection and transmission
- **🛠️ Easy Configuration**: JSON-based configuration management
- **🔍 Built-in Diagnostics**: System health checking and troubleshooting

## 🏛️ Architecture

```
sensor-client/
├── 📁 src/
│   ├── core/           # Core business logic and models
│   ├── adapters/       # External interfaces (MQTT, Serial)
│   ├── services/       # Application orchestration
│   └── utils/          # Utility functions
├── 📁 config/          # Configuration files
├── 📁 scripts/         # Utility scripts
├── 📁 tests/           # Test suite
└── main.py             # Application entry point
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and navigate
cd sensor-client

# Install dependencies
pip install -r requirements.txt
```

### 2. Quick Start (Simulation Mode)

```bash
# Run with default settings
python scripts/quick_start.py
```

### 3. Production Start

```bash
# Run with configuration file
python main.py --config config/sensor_client.json

# Or with environment variables
python main.py --env-config
```

### 4. Docker Deployment

```bash
# Build image
docker build -t agrinex-sensor-client .

# Run container
docker run -d --name sensor-client \
  -e MQTT_HOST=mosquitto \
  agrinex-sensor-client
```

## ⚙️ Configuration

### Configuration File Example

```json
{
  "client_id": "agrinex_sensor_001",
  "mqtt": {
    "host": "localhost",
    "port": 1883,
    "qos": 1
  },
  "serial": {
    "simulation_mode": true,
    "auto_detect": true
  },
  "sensor": {
    "collection_interval": 30.0,
    "include_metadata": true
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_HOST` | MQTT broker host | localhost |
| `MQTT_PORT` | MQTT broker port | 1883 |
| `SENSOR_CLIENT_ID` | Unique client identifier | auto-generated |
| `COLLECTION_INTERVAL` | Data collection interval (seconds) | 30.0 |

## 🔧 Command Line Options

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH           Configuration file path
  --client-id TEXT           Override client ID
  --mqtt-host TEXT           MQTT broker host
  --mqtt-port INTEGER        MQTT broker port
  --simulation               Force simulation mode
  --debug                    Enable debug logging
  --collection-interval FLOAT Collection interval in seconds
  --env-config               Load config from environment
```

## 📊 Data Format

The sensor client sends data in standardized format:

```json
{
  "client_id": "agrinex_sensor_001",
  "timestamp": "2024-07-12T10:30:00Z",
  "data": {
    "temperature": 22.5,
    "humidity": 65.2,
    "light": 1200.0
  }
}
```

## 🔍 Diagnostics

Run system diagnosis to check everything is working:

```bash
python scripts/diagnose.py
```

This checks:
- ✅ Python version compatibility
- ✅ Required dependencies
- ✅ Serial port availability
- ✅ MQTT broker connectivity
- ✅ Configuration validity

## 🛠️ Development

### Project Structure

- **`src/core/`** - Domain models and business logic
- **`src/adapters/`** - External system interfaces
- **`src/services/`** - Application services
- **`src/utils/`** - Helper utilities

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Adding New Sensor Types

1. Extend `SensorReading` model in `src/core/sensor_data.py`
2. Update `SerialAdapter` parsing in `src/adapters/serial_adapter.py`
3. Configure data mapping in sensor configuration

## 📡 MQTT Topics

| Topic | Purpose | QoS |
|-------|---------|-----|
| `sensors/{client_id}/numeric` | Numeric sensor data | 1 |
| `sensors/{client_id}/data` | Detailed sensor data | 1 |
| `sensors/{client_id}/status` | Client status | 1 |
| `sensors/{client_id}/control` | Control commands | 1 |

## 🐳 Docker Integration

### Environment Variables for Docker

```bash
docker run -d \
  -e MQTT_HOST=mosquitto \
  -e MQTT_PORT=1883 \
  -e SENSOR_CLIENT_ID=docker_sensor_001 \
  -e COLLECTION_INTERVAL=30.0 \
  agrinex-sensor-client
```

### Docker Compose Integration

```yaml
version: '3.8'
services:
  sensor-client:
    build: ./sensor-client
    environment:
      - MQTT_HOST=mosquitto
      - MQTT_PORT=1883
    depends_on:
      - mosquitto
```

## 🔧 Troubleshooting

### Common Issues

1. **No Serial Ports Found**
   - Solution: Enable simulation mode with `--simulation`
   - Check: `python scripts/diagnose.py`

2. **MQTT Connection Failed**
   - Check: Broker is running and accessible
   - Verify: Host/port configuration

3. **Permission Denied on Serial Ports**
   - Solution: Add user to dialout group (Linux)
   - Alternative: Use simulation mode

### Debug Mode

Enable detailed logging:

```bash
python main.py --debug
```

## 📈 Monitoring

### Status Monitoring

The client automatically sends status updates every 5 minutes including:
- Connection status
- Data collection statistics
- Error counts
- System uptime

### Health Checks

Docker health checks are built-in:

```bash
docker exec sensor-client python scripts/diagnose.py
```

## 🔄 Migration from v1.x

The v2.0 architecture is a complete rewrite. To migrate:

1. **Backup old configuration**: Configuration format has changed
2. **Update Docker setup**: New Dockerfile and entry point
3. **Review MQTT topics**: Topic structure is standardized
4. **Test thoroughly**: Run diagnosis before deployment

## 📝 Changelog

### v2.0.0 (2024-07-12)

- ✨ Complete architectural rewrite
- 🏗️ Clean separation of concerns
- 📦 Modular adapter pattern
- 🔧 Enhanced configuration management
- 🛠️ Built-in diagnostics
- 🐳 Improved Docker support
- 📊 Standardized data formats
- 🔍 Better error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is part of the AgriNex agricultural monitoring system.

---

**Built with ❤️ for sustainable agriculture** 🌱
