# TeLOO V3 Realtime Gateway

WebSocket service for real-time bidirectional communication using Socket.IO.

## Features

- **WebSocket Server**: Socket.IO with FastAPI integration
- **JWT Authentication**: Secure connection with token validation
- **Role-Based Rooms**: Automatic room assignment based on user role
- **Redis Integration**: Event listening and pub/sub for scalability
- **Event Broadcasting**: Real-time notifications to connected clients

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server running
- JWT public key (for RS256) or secret key (for HS256)

### Installation

```bash
cd services/realtime-gateway
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```env
ENVIRONMENT=development
PORT=8003
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=RS256
```

### Run

```bash
python main.py
```

The service will be available at `http://localhost:8003`

## API Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /stats` - Connection statistics
- `WS /socket.io` - WebSocket endpoint

## WebSocket Events

### Client → Server

- `connect` - Establish connection (requires JWT token)
- `disconnect` - Close connection
- `ping` - Ping server
- `subscribe_solicitud` - Subscribe to solicitud updates
- `unsubscribe_solicitud` - Unsubscribe from solicitud

### Server → Client

- `connected` - Connection established
- `user_joined` - User joined room
- `user_left` - User left room
- `pong` - Ping response
- `solicitud_*` - Solicitud events
- `oferta_*` - Oferta events
- `evaluacion_*` - Evaluation events
- `notificacion_*` - Notification events

## Client Connection Example

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8003', {
  auth: {
    token: 'your-jwt-token'
  }
});

socket.on('connect', () => {
  console.log('Connected to Realtime Gateway');
});

socket.on('solicitud_created', (data) => {
  console.log('New solicitud:', data);
});

// Subscribe to specific solicitud
socket.emit('subscribe_solicitud', { solicitud_id: 'sol-123' });
```

## Architecture

```
Frontend Clients
       ↓
  Socket.IO
       ↓
Realtime Gateway ← Redis (Pub/Sub) ← Core API
       ↓
  Event Listener
       ↓
  Broadcasting
```

## Rooms

- `admin` - Admin, Analyst, Support users
- `advisor` - Advisor users
- `client` - Client users
- `user_{user_id}` - Personal room for each user
- `solicitud_{solicitud_id}` - Solicitud-specific room

## Monitoring

Check connection statistics:

```bash
curl http://localhost:8003/stats
```

Response:
```json
{
  "connected_users": 15,
  "admins_connected": 3,
  "advisors_connected": 10,
  "clients_connected": 2
}
```

## Troubleshooting

### Connection Refused

- Check if Redis is running
- Verify Redis connection settings in `.env`

### Authentication Failed

- Verify JWT token is valid
- Check JWT_SECRET_KEY or JWT_PUBLIC_KEY_PATH
- Ensure JWT_ALGORITHM matches token algorithm

### Events Not Received

- Check if Core API is publishing events to Redis
- Verify Redis pub/sub channels are correct
- Check user is in correct room for event type

## Development

### Run with auto-reload

```bash
uvicorn main:socket_app --reload --port 8003
```

### View logs

```bash
LOG_LEVEL=DEBUG python main.py
```

## Production

### Scaling

The service can be scaled horizontally using Redis adapter. Multiple instances will share connections through Redis.

### Security

- Use HTTPS/WSS in production
- Rotate JWT keys regularly
- Implement rate limiting
- Monitor connection counts

### Performance

- Monitor memory usage (connections are kept in memory)
- Set appropriate `WS_MAX_CONNECTIONS`
- Use Redis for session storage if needed
