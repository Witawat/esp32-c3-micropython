# Module Organization & Design Patterns

<cite>
**Referenced Files in This Document**
- [README.md](file://src/lib/README.md)
- [main.py](file://src/main/main.py)
- [boot_production.py](file://src/main/boot_production.py)
- [wifi_portal_example.py](file://src/main/examples/wifi_portal_example.py)
- [sensors_example.py](file://src/main/examples/sensors_example.py)
- [storage_example.py](file://src/main/examples/storage_example.py)
- [wifimanager.py](file://src/lib/wifi/wifimanager.py)
- [config_mgr.py](file://src/lib/storage/config_mgr.py)
- [battery_monitor.py](file://src/lib/sensors/battery_monitor.py)
- [gps_nmea.py](file://src/lib/sensors/gps_nmea.py)
- [security_manager.py](file://src/lib/security/security_manager.py)
- [__init__.py (system)](file://src/lib/system/__init__.py)
- [README.md (system)](file://src/lib/system/README.md)
- [README.md (sensors)](file://src/lib/sensors/README.md)
- [_pms_base.py](file://src/lib/sensors/_pms_base.py)
- [uart_adc_spi_example.py](file://src/main/examples/uart_adc_spi_example.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the module organization and design patterns used across the ESP32-C3 framework. It focuses on how the codebase is structured into functional categories, how design patterns such as factory, observer, strategy, and singleton are applied, and how modularity, dependency injection, lazy initialization, and plugin-style extension support both beginner accessibility and advanced extensibility. The goal is to help users understand the rationale behind architectural choices, trade-offs, and practical usage across modules like WiFi, sensors, storage, system, and security.

## Project Structure
The repository organizes functionality into clearly separated modules under src/lib, grouped by domain (e.g., wifi, sensors, storage, system). Each domain encapsulates related capabilities and exposes a focused public API. The examples under src/main demonstrate typical usage patterns and cross-module integration.

```mermaid
graph TB
subgraph "Main Application"
MAIN["src/main/main.py"]
BOOT["src/main/boot_production.py"]
EX_WIFI["src/main/examples/wifi_portal_example.py"]
EX_SENSORS["src/main/examples/sensors_example.py"]
EX_STORAGE["src/main/examples/storage_example.py"]
end
subgraph "Libraries (/lib)"
subgraph "WiFi"
WIFI_WM["src/lib/wifi/wifimanager.py"]
end
subgraph "Sensors"
SENS_BAT["src/lib/sensors/battery_monitor.py"]
SENS_GPS["src/lib/sensors/gps_nmea.py"]
SENS_PMS["_pms_base.py"]
end
subgraph "Storage"
STORE_CFG["src/lib/storage/config_mgr.py"]
end
subgraph "System"
SYS_INIT["src/lib/system/__init__.py"]
end
subgraph "Security"
SEC_SM["src/lib/security/security_manager.py"]
end
end
MAIN --> WIFI_WM
MAIN --> SYS_INIT
BOOT --> SEC_SM
EX_WIFI --> WIFI_WM
EX_SENSORS --> SENS_BAT
EX_SENSORS --> SENS_GPS
EX_STORAGE --> STORE_CFG
```

**Diagram sources**
- [main.py:1-84](file://src/main/main.py#L1-L84)
- [boot_production.py:1-56](file://src/main/boot_production.py#L1-L56)
- [wifi_portal_example.py:1-350](file://src/main/examples/wifi_portal_example.py#L1-L350)
- [sensors_example.py:1-529](file://src/main/examples/sensors_example.py#L1-L529)
- [storage_example.py:1-63](file://src/main/examples/storage_example.py#L1-L63)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [gps_nmea.py:317-356](file://src/lib/sensors/gps_nmea.py#L317-L356)
- [security_manager.py:39-72](file://src/lib/security/security_manager.py#L39-L72)
- [__init__.py (system):1-5](file://src/lib/system/__init__.py#L1-L5)

**Section sources**
- [README.md:1-72](file://src/lib/README.md#L1-L72)
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [boot_production.py:19-56](file://src/main/boot_production.py#L19-L56)

## Core Components
- WiFi module: Provides WiFiManager for STA connection and integrates with JsonConfigManager for persistent configuration.
- Sensors module: Offers diverse sensor drivers (e.g., battery monitor, GPS NMEA) with asynchronous monitoring and event-driven callbacks.
- Storage module: Provides JsonConfigManager for configuration persistence and FileLogger for diagnostics.
- System module: Exposes system utilities via a consolidated init interface.
- Security module: Implements SecurityManager for lockdown and audit logging.

Key design pattern highlights:
- Factory pattern for dynamic WiFi portal creation (see WiFi Portal examples).
- Observer pattern for sensor monitoring and callback-driven updates.
- Strategy pattern for sensor driver implementations (various protocols and devices).
- Singleton-like configuration management via JsonConfigManager.

**Section sources**
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [gps_nmea.py:317-356](file://src/lib/sensors/gps_nmea.py#L317-L356)
- [__init__.py (system):1-5](file://src/lib/system/__init__.py#L1-L5)

## Architecture Overview
The framework follows a layered, modular design:
- Domain modules encapsulate functionality (WiFi, sensors, storage, system, security).
- Cross-cutting concerns (configuration, logging, security) are centralized and reused.
- Examples orchestrate modules to demonstrate real-world usage.

```mermaid
graph TB
APP["Application Layer<br/>src/main/*"] --> WIFI["WiFi Layer<br/>src/lib/wifi/*"]
APP --> SENS["Sensors Layer<br/>src/lib/sensors/*"]
APP --> STORE["Storage Layer<br/>src/lib/storage/*"]
APP --> SYS["System Layer<br/>src/lib/system/*"]
APP --> SEC["Security Layer<br/>src/lib/security/*"]
CFG["JsonConfigManager<br/>src/lib/storage/config_mgr.py"] --- WIFI
CFG --- SENS
LOG["FileLogger (via examples)<br/>src/lib/storage/logger.py"] --- STORE
AUDIT["AuditLogger<br/>src/lib/security/security_manager.py"] --- SEC
LOCK["REPLLock<br/>src/lib/security/security_manager.py"] --- SEC
```

**Diagram sources**
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [security_manager.py:39-72](file://src/lib/security/security_manager.py#L39-L72)

## Detailed Component Analysis

### WiFi Portal Factory Pattern
The WiFi Portal examples demonstrate a factory-style approach to creating and configuring a WiFi configuration portal dynamically. The examples show:
- Creating a portal instance with default or custom configuration.
- Starting AP mode and HTTP server concurrently with other tasks.
- Transitioning from portal mode to STA mode after configuration is saved.

```mermaid
sequenceDiagram
participant App as "Example Runner"
participant Portal as "WiFiPortal"
participant WiFi as "WiFiManager"
participant Server as "HTTP Server"
App->>Portal : "Create portal instance"
App->>Portal : "start_ap_mode(ssid, password)"
Portal->>Server : "_create_server()"
App->>App : "Run LED/Sensor tasks concurrently"
App->>Server : "Accept clients and handle requests"
App->>WiFi : "load_config()"
WiFi-->>App : "config present?"
App->>WiFi : "connect() if configured"
WiFi-->>App : "IP address or failure"
```

**Diagram sources**
- [wifi_portal_example.py:13-280](file://src/main/examples/wifi_portal_example.py#L13-L280)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)

**Section sources**
- [wifi_portal_example.py:13-280](file://src/main/examples/wifi_portal_example.py#L13-L280)

### Observer Pattern in Sensor Monitoring
Sensor modules implement observer-like behavior through:
- Asynchronous monitoring loops that periodically invoke callbacks.
- Event-driven APIs (e.g., GPS NMEA sentence callbacks) and optional low-threshold alerts.

```mermaid
flowchart TD
Start(["Start Monitoring"]) --> Read["Read sensor value(s)"]
Read --> Callback{"Has callback?"}
Callback --> |Yes| Invoke["Invoke user callback"]
Callback --> |No| Next["Next cycle"]
Invoke --> LowCheck{"Low threshold alert?"}
LowCheck --> |Yes| LowCallback["Invoke low callback"]
LowCheck --> |No| Next
LowCallback --> Next
Next --> Sleep["Sleep interval"]
Sleep --> Start
```

**Diagram sources**
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [gps_nmea.py:317-356](file://src/lib/sensors/gps_nmea.py#L317-L356)

**Section sources**
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [gps_nmea.py:317-356](file://src/lib/sensors/gps_nmea.py#L317-L356)

### Strategy Pattern in Sensor Driver Implementations
Sensor drivers follow a strategy-like interface:
- Uniform constructor parameters (e.g., pins, addresses, gain) enable interchangeable drivers.
- Each driver encapsulates protocol-specific logic (e.g., I2C, UART, analog sampling).
- Shared base utilities (e.g., PMS frame parsing) reduce duplication.

```mermaid
classDiagram
class SensorDriver {
+configure(...)
+read()
+deinit()
}
class DHTSensor {
+read()
+read_fahrenheit()
}
class BMP280 {
+read()
+altitude()
}
class DS18B20 {
+count
+read_all()
+read(index)
}
class PMS7003 {
+read()
+read_multiple()
}
class PMS5003 {
+read()
+warmup()
}
class _PMSBase {
+parse_pms_frame(bytes)
}
SensorDriver <|.. DHTSensor
SensorDriver <|.. BMP280
SensorDriver <|.. DS18B20
SensorDriver <|.. PMS7003
SensorDriver <|.. PMS5003
PMS7003 --> _PMSBase : "uses"
PMS5003 --> _PMSBase : "uses"
```

**Diagram sources**
- [sensors_example.py:10-27](file://src/main/examples/sensors_example.py#L10-L27)
- [_pms_base.py:155-194](file://src/lib/sensors/_pms_base.py#L155-L194)

**Section sources**
- [sensors_example.py:10-27](file://src/main/examples/sensors_example.py#L10-L27)
- [_pms_base.py:155-194](file://src/lib/sensors/_pms_base.py#L155-L194)

### Singleton Pattern for Configuration Management
JsonConfigManager centralizes configuration loading and saving, acting as a singleton-like service:
- One instance per configuration file path.
- Lazy initialization of default values and atomic save semantics.
- Used by WiFiManager and other modules to persist settings.

```mermaid
classDiagram
class JsonConfigManager {
-path : string
-auto_create : bool
+exists() bool
+load(default) dict
+save(data) bool
+get(key, default) any
+set(key, value) void
+update(data) void
+delete(key) void
+reset() void
}
class WiFiManager {
-config_file : string
-_config_mgr : JsonConfigManager
+load_config() dict
+connect() bool
+keep_alive() void
}
WiFiManager --> JsonConfigManager : "uses"
```

**Diagram sources**
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)

**Section sources**
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)

### Dependency Injection and Plugin Architecture
- Modules expose clean constructors and methods, enabling dependency injection of pins, addresses, and callbacks.
- The system module’s init consolidates imports, supporting a plugin-style discovery of system features.
- Examples demonstrate composing modules asynchronously, allowing new modules to be injected without changing core logic.

```mermaid
sequenceDiagram
participant Main as "main.py"
participant Sys as "System (init)"
participant WiFi as "WiFiManager"
participant Sensor as "Sensor Driver"
participant Store as "JsonConfigManager"
Main->>Sys : "Import system.*"
Main->>WiFi : "Instantiate with config path"
WiFi->>Store : "Load config"
Main->>Sensor : "Instantiate with I2C/SPI/pins"
Main->>Main : "Run tasks concurrently"
```

**Diagram sources**
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [__init__.py (system):1-5](file://src/lib/system/__init__.py#L1-L5)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)

**Section sources**
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [__init__.py (system):1-5](file://src/lib/system/__init__.py#L1-L5)

### Lazy Initialization Strategies
- WiFiManager lazily loads configuration from disk only when requested.
- Sensor drivers initialize hardware resources on demand (e.g., ADC, I2C) and expose async monitoring routines.
- Storage managers defer file operations until explicit load/save/update calls.

**Section sources**
- [wifimanager.py:57-120](file://src/lib/wifi/wifimanager.py#L57-L120)
- [config_mgr.py:26-52](file://src/lib/storage/config_mgr.py#L26-L52)

### Modular Design Philosophy and Extensibility
- Functional grouping: Each domain (wifi, sensors, storage, system, security) is self-contained with its own init and README.
- Cross-domain reuse: JsonConfigManager and logging utilities are shared across modules.
- Extensibility: New sensor drivers can follow the same constructor and method patterns; new system features can be added to the system init.

**Section sources**
- [README.md:1-72](file://src/lib/README.md#L1-L72)
- [README.md (sensors):1-200](file://src/lib/sensors/README.md#L1-L200)
- [README.md (system):263-321](file://src/lib/system/README.md#L263-L321)

## Dependency Analysis
The following diagram shows key dependencies among modules and examples:

```mermaid
graph LR
EX_MAIN["src/main/main.py"] --> WIFI_WM["src/lib/wifi/wifimanager.py"]
EX_MAIN --> SYS_INIT["src/lib/system/__init__.py"]
EX_BOOT["src/main/boot_production.py"] --> SEC_SM["src/lib/security/security_manager.py"]
EX_WIFI["src/main/examples/wifi_portal_example.py"] --> WIFI_WM
EX_SENSORS["src/main/examples/sensors_example.py"] --> SENS_BAT["src/lib/sensors/battery_monitor.py"]
EX_SENSORS --> SENS_GPS["src/lib/sensors/gps_nmea.py"]
EX_STORAGE["src/main/examples/storage_example.py"] --> STORE_CFG["src/lib/storage/config_mgr.py"]
```

**Diagram sources**
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [boot_production.py:19-56](file://src/main/boot_production.py#L19-L56)
- [wifi_portal_example.py:10-10](file://src/main/examples/wifi_portal_example.py#L10-L10)
- [sensors_example.py:10-27](file://src/main/examples/sensors_example.py#L10-L27)
- [storage_example.py:11-11](file://src/main/examples/storage_example.py#L11-L11)
- [wifimanager.py:38-120](file://src/lib/wifi/wifimanager.py#L38-L120)
- [config_mgr.py:10-52](file://src/lib/storage/config_mgr.py#L10-L52)
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [gps_nmea.py:317-356](file://src/lib/sensors/gps_nmea.py#L317-L356)
- [security_manager.py:39-72](file://src/lib/security/security_manager.py#L39-L72)

**Section sources**
- [main.py:12-84](file://src/main/main.py#L12-L84)
- [boot_production.py:19-56](file://src/main/boot_production.py#L19-L56)
- [wifi_portal_example.py:10-10](file://src/main/examples/wifi_portal_example.py#L10-L10)
- [sensors_example.py:10-27](file://src/main/examples/sensors_example.py#L10-L27)
- [storage_example.py:11-11](file://src/main/examples/storage_example.py#L11-L11)

## Performance Considerations
- Asynchronous concurrency: The examples use asyncio to run multiple tasks concurrently, improving responsiveness and throughput.
- Minimal blocking: Sensor drivers and WiFi operations are designed to minimize blocking, leveraging async patterns and callbacks.
- Resource pooling: JsonConfigManager avoids frequent disk writes by batching updates and using temporary files during save.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- WiFi connectivity: Use WiFiManager.load_config and connect methods to diagnose missing or invalid credentials.
- Sensor callbacks: Ensure callbacks are safe and handle exceptions to avoid breaking monitoring loops.
- Storage persistence: Verify file paths and permissions; JsonConfigManager logs errors during load/save failures.
- Security lockdown: Confirm SecurityManager lockdown behavior and development mode unlock pin configuration.

**Section sources**
- [wifimanager.py:57-120](file://src/lib/wifi/wifimanager.py#L57-L120)
- [battery_monitor.py:254-290](file://src/lib/sensors/battery_monitor.py#L254-L290)
- [config_mgr.py:26-52](file://src/lib/storage/config_mgr.py#L26-L52)
- [security_manager.py:39-72](file://src/lib/security/security_manager.py#L39-L72)

## Conclusion
The ESP32-C3 framework employs a modular, layered architecture that cleanly separates concerns across domains. Design patterns like factory (WiFi portal), observer (sensor monitoring), strategy (sensor drivers), and singleton-like configuration management enable both simplicity for beginners and flexibility for advanced users. Dependency injection and lazy initialization further improve maintainability and performance, while plugin-style composition allows easy extension with new modules.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices
- Example references:
  - WiFi portal examples: [wifi_portal_example.py:13-280](file://src/main/examples/wifi_portal_example.py#L13-L280)
  - Sensor examples: [sensors_example.py:10-27](file://src/main/examples/sensors_example.py#L10-L27)
  - Storage examples: [storage_example.py:10-59](file://src/main/examples/storage_example.py#L10-L59)
  - Foundation wrappers (UART/ADC/SPI): [uart_adc_spi_example.py:249-263](file://src/main/examples/uart_adc_spi_example.py#L249-L263)