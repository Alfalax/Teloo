# Support Services Implementation Summary

## Overview

This document summarizes the implementation of the three support services for TeLOO V3 marketplace:

1. **Realtime Gateway** - WebSocket communication with Socket.IO
2. **Files Service** - File management with MinIO storage
3. **Notification System** - Push notifications with WhatsApp fallback

---

## 1. Realtime Gateway Service

### Purpose
Provides real-time bidirectional communication between the backend and frontend clients using WebSocket technology.

### Key Features

#### WebSocket Server with Socket.IO
- **Technology**: Socket.IO with FastAPI integration
- **Port**: 8003
- **Protocol**: WebSocket with fallback to long-polling

#### JWT Authentication
- Validates JWT tokens on connection
- Supports both RS256 (public key) and HS256 (secret key) algorithms
- Extracts user information from token payload
- Rejects unauthenticated connections

#### Role-Based Rooms
- **Admin Room**: For ADMIN, ANALYST, and SUPPORT users
- **Advisor Room**: For ADVISOR users
- **Client Room**: For CLIENT users
- **Personal Rooms**: `user_{user_id}` for targeted messages
- **Solicitud Rooms**: `solicitud_{solicitud_id}` for solicitud-specific updates

#### Redis Integration
- **Pub/Sub**: Listens to events from Core API
- **Event Channels**:
  - `solicitud.*` - Solicitud events (created, oleada, updated)
  - `oferta.*` - Oferta events (created, updated, result)
  - `evaluacion.*` - Evaluation events (completed, results)
  - `cliente.*` - Client events
  - `notificacion.*` - Notification events

#### Event Broadcasting
- Broadcasts events to appropriate rooms based on event type
- Notifies specific users about their solicitudes/ofertas
- Supports subscription to specific solicitud updates

### Architecture

```
┌─────────────────┐
│  Frontend       │
│  (Admin/Advisor)│
└────────┬────────┘
         │ WebSocket
         │ (Socket.IO)
         ▼
┌─────────────────┐      ┌─────────────┐
│ Realtime Gateway│◄─────┤   Redis     │
│   (Socket.IO)   │      │  (Pub/Sub)  │
└─────────────────┘      └──────▲──────┘
                                │
                                │ Events
                         ┌──────┴──────┐
                         │  Core API   │
                         └─────────────┘
```

### Files Created
- `services/realtime-gateway/app/config.py` - Configuration management
- `services/realtime-gateway/app/auth.py` - JWT authentication
- `services/realtime-gateway/app/redis_client.py` - Redis client wrapper
- `services/realtime-gateway/app/socket_manager.py` - Socket.IO manager
- `services/realtime-gateway/app/event_listener.py` - Redis event listener
- `services/realtime-gateway/main.py` - Main application

### Configuration
```env
ENVIRONMENT=development
PORT=8003
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
WS_PING_INTERVAL=25
WS_PING_TIMEOUT=60
WS_MAX_CONNECTIONS=1000
```

---

## 2. Files Service

### Purpose
Manages file uploads, validation, virus scanning, and storage using MinIO (S3-compatible object storage).

### Key Features

#### File Upload & Validation
- **Max File Size**: Configurable (default 5MB)
- **Allowed Extensions**: .xlsx, .xls, .csv
- **MIME Type Validation**: Using python-magic
- **Security**: Path traversal prevention, filename sanitization

#### MinIO Storage
- **S3-Compatible**: Uses MinIO for self-hosted object storage
- **Bucket Management**: Auto-creates bucket if not exists
- **Presigned URLs**: Generates temporary download URLs
- **File Operations**: Upload, download, delete, exists check

#### Antivirus Scanning (Optional)
- **ClamAV Integration**: Scans files for viruses before storage
- **Graceful Degradation**: Continues without scanning if ClamAV unavailable
- **Network Socket**: Connects to ClamAV daemon via TCP

#### API Endpoints
- `POST /v1/files/upload` - Upload file with validation
- `GET /v1/files/download/{object_name}` - Download file
- `GET /v1/files/url/{object_name}` - Get presigned download URL
- `DELETE /v1/files/{object_name}` - Delete file
- `GET /v1/files/templates/ofertas` - Download Excel template

### Architecture

```
┌─────────────────┐
│   Frontend      │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐      ┌─────────────┐
│  Files Service  │◄─────┤   ClamAV    │
│                 │      │ (Antivirus) │
└────────┬────────┘      └─────────────┘
         │
         ▼
┌─────────────────┐
│     MinIO       │
│  (S3 Storage)   │
└─────────────────┘
```

### Files Created
- `services/files/app/config.py` - Configuration management
- `services/files/app/minio_client.py` - MinIO client wrapper
- `services/files/app/file_validator.py` - File validation utilities
- `services/files/app/antivirus.py` - ClamAV integration
- `services/files/app/routers/files.py` - API endpoints
- `services/files/main.py` - Main application

### Configuration
```env
ENVIRONMENT=development
PORT=8004
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=teloo-files
MAX_FILE_SIZE_MB=5
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
CLAMAV_ENABLED=false
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
```

---

## 3. Notification System

### Purpose
Manages internal push notifications with automatic fallback to WhatsApp when WebSocket is unavailable.

### Key Features

#### Multi-Channel Delivery
- **Primary**: WebSocket via Realtime Gateway
- **Fallback**: WhatsApp via Agent IA service
- **Queue**: Redis queue for failed notifications

#### Notification Types
- `solicitud_nueva` - New solicitud available for advisor
- `oferta_resultado` - Oferta result (GANADORA, NO_SELECCIONADA, etc.)
- `evaluacion_completada` - Evaluation completed
- `general` - General notifications

#### Priority Levels
- `low` - Non-urgent notifications
- `normal` - Standard notifications
- `high` - Important notifications
- `urgent` - Critical notifications

#### Retry Mechanism
- Failed notifications queued in Redis
- Scheduled job processes queue every 5 minutes
- Automatic retry with exponential backoff

### Architecture

```
┌─────────────────┐
│   Core API      │
│ (Notification   │
│   Service)      │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────────┐  ┌─────────────────┐
│ Realtime Gateway│  │   Agent IA      │
│  (WebSocket)    │  │  (WhatsApp)     │
└────────┬────────┘  └────────┬────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│   Frontend      │  │   WhatsApp      │
│   Clients       │  │   Clients       │
└─────────────────┘  └─────────────────┘
```

### Files Created
- `services/core-api/services/notification_service.py` - Notification service
- `services/core-api/jobs/scheduled_jobs.py` - Added `procesar_notificaciones_pendientes` job
- `services/core-api/services/scheduler_service.py` - Added notification processing to scheduler

### Usage Example

```python
from services.notification_service import notification_service

# Send notification to specific user
await notification_service.send_notification(
    user_id="asesor-123",
    title="Nueva Solicitud Disponible",
    message="Nueva solicitud de repuestos en tu área",
    notification_type="solicitud_nueva",
    data={"solicitud_id": "sol-456"},
    priority="high"
)

# Broadcast to role
await notification_service.send_notification_to_role(
    role="ADMIN",
    title="Sistema Actualizado",
    message="Nueva versión disponible",
    notification_type="sistema_update"
)

# Notify about oferta result
await notification_service.notify_oferta_result(
    oferta=oferta_instance,
    result="GANADORA"
)
```

### Scheduled Job
- **Frequency**: Every 5 minutes
- **Function**: `procesar_notificaciones_pendientes`
- **Purpose**: Process failed notifications from Redis queue
- **Max Batch**: 100 notifications per run

---

## Integration Points

### Core API → Realtime Gateway
- Core API publishes events to Redis
- Realtime Gateway subscribes to Redis channels
- Events automatically broadcast to connected clients

### Core API → Files Service
- Core API redirects file uploads to Files Service
- Files Service returns presigned URLs for downloads
- Core API stores file references in database

### Core API → Notification System
- Core API calls notification service for important events
- Notification service tries WebSocket first
- Falls back to WhatsApp if WebSocket unavailable
- Queues failed notifications for retry

---

## Deployment Considerations

### Realtime Gateway
- Requires Redis for pub/sub and scalability
- Can scale horizontally with Redis adapter
- Needs JWT public key for token verification
- Monitor connection count and memory usage

### Files Service
- Requires MinIO or S3-compatible storage
- Optional ClamAV for virus scanning
- Consider CDN for file downloads in production
- Monitor storage usage and implement cleanup

### Notification System
- Integrated into Core API (no separate deployment)
- Requires Redis for queue management
- Depends on Realtime Gateway and Agent IA services
- Monitor queue size and processing rate

---

## Testing

### Realtime Gateway
```bash
# Start service
cd services/realtime-gateway
python main.py

# Test WebSocket connection (using Socket.IO client)
# Connect with token in auth or query params
```

### Files Service
```bash
# Start service
cd services/files
python main.py

# Test file upload
curl -X POST http://localhost:8004/v1/files/upload \
  -F "file=@test.xlsx"

# Test health check
curl http://localhost:8004/health
```

### Notification System
```bash
# Process pending notifications manually
cd services/core-api
python -c "
import asyncio
from jobs.scheduled_jobs import procesar_notificaciones_pendientes
asyncio.run(procesar_notificaciones_pendientes())
"
```

---

## Requirements Validation

### Requirement 10.1 ✅
- WebSocket server implemented with Socket.IO
- Real-time notifications to connected clients
- Role-based room broadcasting

### Requirement 10.2 ✅
- JWT authentication for WebSocket connections
- User identification and authorization
- Secure connection establishment

### Requirement 4.4 ✅
- File upload with validation (format, size, type)
- MinIO storage for Excel files
- Antivirus scanning (optional)
- Template download endpoints

### Requirement 10.3, 10.4, 10.5 ✅
- Internal push notification system
- WhatsApp fallback when WebSocket unavailable
- Redis queue for failed notifications
- Automatic retry mechanism

---

## Next Steps

1. **Testing**: Write integration tests for all three services
2. **Monitoring**: Add Prometheus metrics for connection counts, file uploads, notification delivery
3. **Documentation**: Create API documentation for Files Service endpoints
4. **Security**: Implement rate limiting for file uploads
5. **Performance**: Load test WebSocket connections and file uploads
6. **Production**: Configure production settings for all services

---

## Conclusion

All three support services have been successfully implemented:

1. **Realtime Gateway** provides real-time bidirectional communication with role-based broadcasting
2. **Files Service** handles file management with validation, storage, and optional virus scanning
3. **Notification System** ensures reliable message delivery with automatic fallback and retry

These services work together to provide a robust infrastructure for the TeLOO V3 marketplace platform.
