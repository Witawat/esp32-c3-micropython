# Security Manager

<cite>
**Referenced Files in This Document**
- [security_manager.py](file://src/lib/security/security_manager.py)
- [repl_lock.py](file://src/lib/security/repl_lock.py)
- [auth_provider.py](file://src/lib/security/auth_provider.py)
- [secret_store.py](file://src/lib/security/secret_store.py)
- [audit_logger.py](file://src/lib/security/audit_logger.py)
- [__init__.py](file://src/lib/security/__init__.py)
- [README.md](file://src/lib/security/README.md)
- [secure_production_example.py](file://src/main/examples/secure_production_example.py)
- [boot_production.py](file://src/main/boot_production.py)
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
This document provides comprehensive documentation for the SecurityManager class, the central security orchestrator for the ESP32-C3 framework. It explains the lockdown procedure for production deployment, development mode unlocking, token management, secure command dispatching for protected REPL access, and status monitoring. It also details the integrated security architecture coordinating REPLLock, AuthProvider, AuditLogger, and SecretStore subsystems, and demonstrates practical examples from secure_production_example.py for production workflows, security configuration patterns, and emergency wipe procedures.

## Project Structure
The security module is organized around a central orchestrator (SecurityManager) that composes four subsystems:
- REPLLock: Controls REPL access across UART0, WebREPL, TCP, BLE, and UART1 channels.
- AuthProvider: Provides token-based authentication with expiry, rate limiting, and revocation.
- AuditLogger: Logs all REPL commands and security events with suspicious pattern detection.
- SecretStore: Stores sensitive data encrypted on flash with PBKDF2-derived keys and optional wipe.

```mermaid
graph TB
SM["SecurityManager<br/>Central Orchestrator"]
RL["REPLLock<br/>Channel Control"]
AP["AuthProvider<br/>Token Auth"]
AL["AuditLogger<br/>Command & Event Logging"]
SS["SecretStore<br/>Encrypted Secrets"]
SM --> RL
SM --> AP
SM --> AL
SM --> SS
SM --> |"lockdown() / unlock_dev()"| RL
SM --> |"generate_token() / authenticate()"| AP
SM --> |"secure_dispatch()"| AL
SM --> |"store()/get()/wipe_all()"| SS
```

**Diagram sources**
- [security_manager.py:25-82](file://src/lib/security/security_manager.py#L25-L82)
- [repl_lock.py:29-59](file://src/lib/security/repl_lock.py#L29-L59)
- [auth_provider.py:23-67](file://src/lib/security/auth_provider.py#L23-L67)
- [audit_logger.py:17-54](file://src/lib/security/audit_logger.py#L17-L54)
- [secret_store.py:39-79](file://src/lib/security/secret_store.py#L39-L79)

**Section sources**
- [__init__.py:11-16](file://src/lib/security/__init__.py#L11-L16)
- [README.md:9-16](file://src/lib/security/README.md#L9-L16)

## Core Components
- SecurityManager: Initializes and coordinates REPLLock, AuthProvider, AuditLogger, and SecretStore. Provides lockdown(), unlock_dev(), generate_token(), authenticate(), secure_dispatch(), get_status(), print_status(), and emergency_wipe().
- REPLLock: Disables REPL channels and manages status reporting.
- AuthProvider: Generates and validates tokens with expiry and rate limiting.
- AuditLogger: Records REPL commands and security events with suspicious detection and log rotation.
- SecretStore: Stores secrets encrypted on flash with PBKDF2 and optional wipe.

**Section sources**
- [security_manager.py:25-323](file://src/lib/security/security_manager.py#L25-L323)
- [repl_lock.py:29-227](file://src/lib/security/repl_lock.py#L29-L227)
- [auth_provider.py:23-257](file://src/lib/security/auth_provider.py#L23-L257)
- [audit_logger.py:17-197](file://src/lib/security/audit_logger.py#L17-L197)
- [secret_store.py:39-375](file://src/lib/security/secret_store.py#L39-L375)

## Architecture Overview
The SecurityManager acts as a facade that initializes and delegates to subsystems. It enforces production lockdown by disabling REPL channels, enabling audit logging, locking secret storage, and configuring rate limiting. It integrates token-based authentication for protected REPL access and provides secure command dispatching with audit logging.

```mermaid
classDiagram
class SecurityManager {
-bool _dev_mode
-bool _locked_down
-dict _config
+REPLLock repl_lock
+AuthProvider auth
+AuditLogger audit
+SecretStore secrets
+lockdown() void
+unlock_dev() void
+generate_token() str
+authenticate(token) bool
+secure_dispatch(dispatcher, line, transport, token) str
+get_status() dict
+print_status() void
+emergency_wipe() void
}
class REPLLock {
-bool _uart0_disabled
-bool _webrepl_disabled
-bool _tcp_disabled
-bool _ble_disabled
-bool _uart1_disabled
+disable_uart0() void
+disable_webrepl() void
+disable_tcp_repl() void
+disable_ble_repl() void
+disable_uart1_repl() void
+lockdown() void
+unlock_all() void
+status() dict
+is_locked() bool
}
class AuthProvider {
-bytes _secret
-int _token_expiry_ms
-int _max_attempts
-int _lockout_ms
-int _failed_attempts
-int _lockout_until
-dict _active_tokens
+generate_token(salt) str
+authenticate(token) bool
+invalidate(token) void
+invalidate_all() void
+is_expired(token) bool
+active_token_count int
+failed_attempts int
+is_locked_out bool
+remaining_lockout_sec() int
}
class AuditLogger {
-str _log_file
-int _max_entries
-int _max_file_bytes
-list _buffer
-int _write_count
-int _suspicious_count
+log_command(transport, command, result) void
+log_event(level, message) void
+get_recent_logs(count) list
+get_suspicious_count() int
+read_log_file() str
+clear_logs() void
+flush() void
}
class SecretStore {
-str _secret_file
-bytes _master_key
-int _iterations
-bytes _enc_key
-dict _secrets
-bool _locked
-bool _dirty
+store(key, value) void
+get(key) str
+delete(key) void
+list_keys() list
+lock() void
+unlock(master_key) void
+wipe_all() void
+is_locked bool
+secret_count int
}
SecurityManager --> REPLLock : "controls"
SecurityManager --> AuthProvider : "authenticates"
SecurityManager --> AuditLogger : "audits"
SecurityManager --> SecretStore : "stores"
```

**Diagram sources**
- [security_manager.py:25-323](file://src/lib/security/security_manager.py#L25-L323)
- [repl_lock.py:29-227](file://src/lib/security/repl_lock.py#L29-L227)
- [auth_provider.py:23-257](file://src/lib/security/auth_provider.py#L23-L257)
- [audit_logger.py:17-197](file://src/lib/security/audit_logger.py#L17-L197)
- [secret_store.py:39-375](file://src/lib/security/secret_store.py#L39-L375)

## Detailed Component Analysis

### SecurityManager
SecurityManager orchestrates the entire security stack. It initializes subsystems with configurable parameters, enforces lockdown in production, unlocks for development, generates and authenticates tokens, dispatches secure REPL commands, and provides status reporting and emergency wipe.

Key methods:
- lockdown(): Applies production lockdown by disabling REPL channels, logging the event, locking secret store, and setting internal flags.
- unlock_dev(): Unlocks all subsystems for development use and logs the event.
- generate_token(): Creates a time-bound token and logs the generation.
- authenticate(): Validates tokens and logs failed attempts.
- secure_dispatch(): Handles login commands, checks authentication, dispatches commands, and audits results.
- get_status()/print_status(): Reports consolidated security status across subsystems.
- emergency_wipe(): Wipes secrets, clears audit logs, invalidates tokens, and ensures lockdown.

```mermaid
sequenceDiagram
participant Client as "Client"
participant SM as "SecurityManager"
participant AP as "AuthProvider"
participant AL as "AuditLogger"
participant DISP as "CommandDispatcher"
Client->>SM : "secure_dispatch(disp, line, transport, token)"
alt "line starts with 'login'"
SM->>AP : "authenticate(token)"
AP-->>SM : "bool"
SM-->>Client : "response prompt"
else "no token provided"
SM-->>Client : "prompt to login"
else "authenticated"
SM->>DISP : "dispatch(line)"
DISP-->>SM : "result"
SM->>AL : "log_command(transport, line, result)"
SM-->>Client : "result"
end
```

**Diagram sources**
- [security_manager.py:220-251](file://src/lib/security/security_manager.py#L220-L251)
- [auth_provider.py:147-184](file://src/lib/security/auth_provider.py#L147-L184)
- [audit_logger.py:57-97](file://src/lib/security/audit_logger.py#L57-L97)

**Section sources**
- [security_manager.py:125-178](file://src/lib/security/security_manager.py#L125-L178)
- [security_manager.py:179-189](file://src/lib/security/security_manager.py#L179-L189)
- [security_manager.py:193-201](file://src/lib/security/security_manager.py#L193-L201)
- [security_manager.py:203-216](file://src/lib/security/security_manager.py#L203-L216)
- [security_manager.py:220-251](file://src/lib/security/security_manager.py#L220-L251)
- [security_manager.py:255-294](file://src/lib/security/security_manager.py#L255-L294)
- [security_manager.py:297-323](file://src/lib/security/security_manager.py#L297-L323)

### REPLLock
Controls REPL access across multiple channels. It disables UART0 (redirects stdin/stdout and disables keyboard interrupts), stops WebREPL, and marks TCP, BLE, and UART1 channels as disabled. It provides status reporting and bulk lockdown/unlock operations.

```mermaid
flowchart TD
Start(["disable_uart0()"]) --> CheckMicropython{"micropython available?"}
CheckMicropython --> |Yes| DisableKbd["Disable Ctrl+C/D interrupts"]
CheckMicropython --> |No| SkipKbd["Skip kbd_intr"]
DisableKbd --> RedirectStdout["Redirect stdout/stdin to null"]
SkipKbd --> RedirectStdout
RedirectStdout --> MarkUart0["Mark UART0 disabled"]
MarkUart0 --> Done(["UART0 locked"])
```

**Diagram sources**
- [repl_lock.py:62-99](file://src/lib/security/repl_lock.py#L62-L99)

**Section sources**
- [repl_lock.py:62-113](file://src/lib/security/repl_lock.py#L62-L113)
- [repl_lock.py:116-149](file://src/lib/security/repl_lock.py#L116-L149)
- [repl_lock.py:152-171](file://src/lib/security/repl_lock.py#L152-L171)
- [repl_lock.py:174-182](file://src/lib/security/repl_lock.py#L174-L182)
- [repl_lock.py:185-203](file://src/lib/security/repl_lock.py#L185-L203)
- [repl_lock.py:204-227](file://src/lib/security/repl_lock.py#L204-L227)

### AuthProvider
Implements token-based authentication with SHA256-based tokens derived from a device-unique secret, random salt, and timestamp. Tokens expire after a configurable period, and repeated failures trigger a lockout with exponential backoff-like behavior.

```mermaid
flowchart TD
GenStart(["generate_token(salt)"]) --> Seed["Seed = secret + salt + timestamp"]
Seed --> Hash["HashHelper.sha256(seed)"]
Hash --> Hex["to_hex(hash)"]
Hex --> Store["Store token with expiry"]
Store --> ReturnToken(["Return token"])
AuthStart(["authenticate(token)"]) --> CheckLock{"Locked out?"}
CheckLock --> |Yes| ReturnFalse["Return False"]
CheckLock --> |No| Lookup["Lookup token expiry"]
Lookup --> Expired{"Expired?"}
Expired --> |Yes| DelToken["Delete token"] --> ReturnFalse
Expired --> |No| IncFail["Increment failed attempts"]
IncFail --> MaxFail{"Attempts >= max?"}
MaxFail --> |Yes| Lockout["Set lockout until"] --> ReturnFalse
MaxFail --> |No| ReturnTrue["Return True"]
```

**Diagram sources**
- [auth_provider.py:100-128](file://src/lib/security/auth_provider.py#L100-L128)
- [auth_provider.py:147-184](file://src/lib/security/auth_provider.py#L147-L184)

**Section sources**
- [auth_provider.py:100-144](file://src/lib/security/auth_provider.py#L100-L144)
- [auth_provider.py:147-184](file://src/lib/security/auth_provider.py#L147-L184)
- [auth_provider.py:198-225](file://src/lib/security/auth_provider.py#L198-L225)
- [auth_provider.py:236-257](file://src/lib/security/auth_provider.py#L236-L257)

### AuditLogger
Logs all REPL commands and security events with FIFO buffer management and suspicious pattern detection. It flushes logs to flash periodically and maintains a suspicious event counter.

```mermaid
flowchart TD
LogStart(["log_command/ log_event"]) --> AddBuffer["Append to RAM buffer"]
AddBuffer --> FlushCheck{"Write count % 10 == 0 OR level in {ERROR,SECURITY}?"}
FlushCheck --> |Yes| Flush["Flush to flash with FIFO"]
FlushCheck --> |No| Detect["Detect suspicious patterns"]
Flush --> Detect
Detect --> GC["gc.collect()"]
GC --> LogEnd(["Done"])
```

**Diagram sources**
- [audit_logger.py:76-97](file://src/lib/security/audit_logger.py#L76-L97)
- [audit_logger.py:100-131](file://src/lib/security/audit_logger.py#L100-L131)
- [audit_logger.py:134-149](file://src/lib/security/audit_logger.py#L134-L149)

**Section sources**
- [audit_logger.py:57-97](file://src/lib/security/audit_logger.py#L57-L97)
- [audit_logger.py:100-131](file://src/lib/security/audit_logger.py#L100-L131)
- [audit_logger.py:134-149](file://src/lib/security/audit_logger.py#L134-L149)
- [audit_logger.py:152-197](file://src/lib/security/audit_logger.py#L152-L197)

### SecretStore
Stores secrets encrypted on flash using PBKDF2-derived keys and AES-CBC (or XOR fallback). It supports locking to clear RAM cache, unlocking with the master key, and wiping all data including files and salts.

```mermaid
flowchart TD
StoreStart(["store(key, value)"]) --> CheckLock{"Locked?"}
CheckLock --> |Yes| Abort["Abort with lock message"]
CheckLock --> |No| Cache["Cache in RAM"]
Cache --> Dirty["Mark dirty"]
Dirty --> Save["Save to encrypted JSON"]
Save --> StoreEnd(["Done"])
WipeStart(["wipe_all()"]) --> ClearCache["Clear RAM cache"]
ClearCache --> Overwrite["Overwrite secret file"]
Overwrite --> RemoveFile["Remove secret file"]
RemoveFile --> RemoveSalt["Remove salt file"]
RemoveSalt --> Collect["gc.collect()"]
Collect --> WipeEnd(["Wiped"])
```

**Diagram sources**
- [secret_store.py:222-236](file://src/lib/security/secret_store.py#L222-L236)
- [secret_store.py:337-365](file://src/lib/security/secret_store.py#L337-L365)

**Section sources**
- [secret_store.py:222-264](file://src/lib/security/secret_store.py#L222-L264)
- [secret_store.py:311-336](file://src/lib/security/secret_store.py#L311-L336)
- [secret_store.py:337-375](file://src/lib/security/secret_store.py#L337-L375)

### Practical Examples and Workflows
The secure_production_example.py demonstrates:
- Basic lockdown for production environments.
- Secret storage and retrieval with encrypted persistence.
- Token generation and authentication with rate limiting feedback.
- Audit logging for REPL commands and security events.
- Emergency wipe for compromised devices.
- Individual REPL channel locking.
- Full production simulation including token generation and status reporting.

```mermaid
sequenceDiagram
participant App as "Application"
participant Sec as "SecurityManager"
participant RL as "REPLLock"
participant AP as "AuthProvider"
participant AL as "AuditLogger"
participant SS as "SecretStore"
App->>Sec : "lockdown()"
Sec->>RL : "disable channels"
Sec->>AL : "log lockdown event"
Sec->>SS : "lock()"
App->>Sec : "generate_token()"
Sec->>AP : "generate_token()"
Sec->>AL : "log token generation"
App->>Sec : "secure_dispatch(...)"
Sec->>AP : "authenticate(token?)"
Sec->>AL : "log_command(...)"
```

**Diagram sources**
- [secure_production_example.py:20-40](file://src/main/examples/secure_production_example.py#L20-L40)
- [secure_production_example.py:44-74](file://src/main/examples/secure_production_example.py#L44-L74)
- [secure_production_example.py:79-110](file://src/main/examples/secure_production_example.py#L79-L110)
- [secure_production_example.py:115-151](file://src/main/examples/secure_production_example.py#L115-L151)
- [secure_production_example.py:156-178](file://src/main/examples/secure_production_example.py#L156-L178)
- [secure_production_example.py:183-207](file://src/main/examples/secure_production_example.py#L183-L207)
- [secure_production_example.py:212-244](file://src/main/examples/secure_production_example.py#L212-L244)

**Section sources**
- [secure_production_example.py:20-40](file://src/main/examples/secure_production_example.py#L20-L40)
- [secure_production_example.py:44-74](file://src/main/examples/secure_production_example.py#L44-L74)
- [secure_production_example.py:79-110](file://src/main/examples/secure_production_example.py#L79-L110)
- [secure_production_example.py:115-151](file://src/main/examples/secure_production_example.py#L115-L151)
- [secure_production_example.py:156-178](file://src/main/examples/secure_production_example.py#L156-L178)
- [secure_production_example.py:183-207](file://src/main/examples/secure_production_example.py#L183-L207)
- [secure_production_example.py:212-244](file://src/main/examples/secure_production_example.py#L212-L244)

### Boot Integration for Production
The boot_production.py script demonstrates integrating lockdown at boot time, with an optional unlock pin to enable development mode. It ensures the device is locked before main application logic runs.

```mermaid
sequenceDiagram
participant Boot as "boot.py"
participant Pin as "GPIO Pin"
participant Sec as "SecurityManager"
Boot->>Pin : "Configure unlock pin"
Boot->>Boot : "Check pin state"
alt "pin grounded"
Boot->>Sec : "dev_mode = True"
Boot-->>Boot : "Print dev mode notice"
else "pin floating"
Boot->>Sec : "dev_mode = False"
Boot->>Sec : "lockdown()"
Boot-->>Boot : "Print lockdown notice"
end
Boot-->>Boot : "gc.collect()"
```

**Diagram sources**
- [boot_production.py:24-48](file://src/main/boot_production.py#L24-L48)

**Section sources**
- [boot_production.py:24-48](file://src/main/boot_production.py#L24-L48)

## Dependency Analysis
SecurityManager depends on REPLLock, AuthProvider, AuditLogger, and SecretStore. Each subsystem encapsulates its own responsibilities and exposes a focused API. The orchestrator coordinates initialization, configuration, and lifecycle operations.

```mermaid
graph TB
SM["SecurityManager"]
RL["REPLLock"]
AP["AuthProvider"]
AL["AuditLogger"]
SS["SecretStore"]
SM --> RL
SM --> AP
SM --> AL
SM --> SS
```

**Diagram sources**
- [security_manager.py:19-22](file://src/lib/security/security_manager.py#L19-L22)

**Section sources**
- [security_manager.py:19-22](file://src/lib/security/security_manager.py#L19-L22)

## Performance Considerations
- Token generation and authentication involve cryptographic hashing and dictionary lookups; ensure sufficient entropy sources and avoid excessive token creation during lockout periods.
- Audit logging uses a RAM buffer with periodic flushing to flash; tune max entries and file size to balance memory usage and flash wear.
- SecretStore encryption uses PBKDF2 with configurable iterations; higher iteration counts increase security but may impact performance on constrained devices.
- REPLLock redirection and WebREPL stopping are lightweight operations; monitor for exceptions in embedded environments.

## Troubleshooting Guide
Common issues and remedies:
- Authentication failures: Verify token validity and lockout status via status reporting. Check failed attempts and remaining lockout time.
- REPL access not disabled: Confirm lockdown was called and that the device is not in development mode. Review REPLLock status.
- Audit logs not appearing: Ensure audit logging is enabled and that flush conditions are met; check suspicious detection thresholds.
- Secrets not readable: Confirm SecretStore is unlocked and that the master key matches the one used during encryption.
- Emergency wipe effectiveness: After emergency_wipe, verify lockdown status and confirm secrets and logs are cleared.

**Section sources**
- [security_manager.py:255-294](file://src/lib/security/security_manager.py#L255-L294)
- [auth_provider.py:156-184](file://src/lib/security/auth_provider.py#L156-L184)
- [audit_logger.py:100-131](file://src/lib/security/audit_logger.py#L100-L131)
- [secret_store.py:311-336](file://src/lib/security/secret_store.py#L311-L336)
- [security_manager.py:297-323](file://src/lib/security/security_manager.py#L297-L323)

## Conclusion
The SecurityManager provides a cohesive, production-ready security framework for ESP32-C3 devices. By coordinating REPL lockdown, token-based authentication, audit logging, and encrypted secret storage, it delivers strong software-level protection suitable for enterprise IoT deployments. The included examples and boot integration demonstrate practical deployment patterns, while the emergency wipe capability ensures robust incident response.

## Appendices
- API Reference and configuration examples are documented in the module’s README and example scripts.
- For advanced use cases, consider combining the security module with additional protections such as Secure Boot and bytecode compilation.