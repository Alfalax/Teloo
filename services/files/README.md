# TeLOO V3 Files Service

File management service with validation, virus scanning, and MinIO storage.

## Features

- **File Upload**: Secure file upload with validation
- **File Validation**: Format, size, and MIME type checking
- **Virus Scanning**: Optional ClamAV integration
- **MinIO Storage**: S3-compatible object storage
- **Presigned URLs**: Temporary download links
- **Template Management**: Excel template downloads

## Quick Start

### Prerequisites

- Python 3.11+
- MinIO server running (or S3-compatible storage)
- ClamAV daemon (optional, for virus scanning)

### Installation

```bash
cd services/files
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

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
```

### Run MinIO (Docker)

```bash
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### Run Service

```bash
python main.py
```

The service will be available at `http://localhost:8004`

## API Endpoints

### Upload File

```bash
POST /v1/files/upload
Content-Type: multipart/form-data

Parameters:
- file: File to upload (required)
- folder: Optional folder path (optional)

Response:
{
  "success": true,
  "file_id": "uuid",
  "object_name": "folder/uuid.xlsx",
  "original_filename": "ofertas.xlsx",
  "size_bytes": 12345,
  "download_url": "presigned-url"
}
```

### Download File

```bash
GET /v1/files/download/{object_name}

Response: File stream
```

### Get Download URL

```bash
GET /v1/files/url/{object_name}?expires_hours=1

Response:
{
  "success": true,
  "object_name": "folder/uuid.xlsx",
  "download_url": "presigned-url",
  "expires_in_hours": 1
}
```

### Delete File

```bash
DELETE /v1/files/{object_name}

Response:
{
  "success": true,
  "message": "File deleted successfully",
  "object_name": "folder/uuid.xlsx"
}
```

### Download Template

```bash
GET /v1/files/templates/ofertas

Response: Excel template file
```

## File Validation

### Size Validation
- Default max size: 5MB
- Configurable via `MAX_FILE_SIZE_MB`

### Extension Validation
- Allowed: .xlsx, .xls, .csv
- Configurable via `ALLOWED_EXTENSIONS`

### MIME Type Validation
- Uses python-magic for detection
- Validates against expected types

### Security Validation
- Path traversal prevention
- Filename sanitization
- Length limits

## Virus Scanning

### Setup ClamAV (Optional)

```bash
# Install ClamAV
sudo apt-get install clamav clamav-daemon

# Update virus definitions
sudo freshclam

# Start daemon
sudo systemctl start clamav-daemon
```

### Enable in Configuration

```env
CLAMAV_ENABLED=true
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
```

### Behavior

- If enabled and available: Scans all uploads
- If enabled but unavailable: Logs warning, continues without scan
- If disabled: Skips scanning entirely

## MinIO Storage

### Bucket Management

- Auto-creates bucket if not exists
- Bucket name configurable via `MINIO_BUCKET_NAME`

### File Organization

```
teloo-files/
├── ofertas/
│   ├── uuid1.xlsx
│   └── uuid2.xlsx
├── templates/
│   └── ofertas_template.xlsx
└── documents/
    └── uuid3.pdf
```

### Presigned URLs

- Temporary download links
- Configurable expiration (1-168 hours)
- No authentication required for download

## Usage Examples

### Python Client

```python
import httpx

# Upload file
with open('ofertas.xlsx', 'rb') as f:
    response = httpx.post(
        'http://localhost:8004/v1/files/upload',
        files={'file': f},
        params={'folder': 'ofertas'}
    )
    result = response.json()
    file_id = result['file_id']

# Get download URL
response = httpx.get(
    f'http://localhost:8004/v1/files/url/ofertas/{file_id}.xlsx',
    params={'expires_hours': 24}
)
download_url = response.json()['download_url']

# Delete file
response = httpx.delete(
    f'http://localhost:8004/v1/files/ofertas/{file_id}.xlsx'
)
```

### JavaScript Client

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8004/v1/files/upload?folder=ofertas', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('File uploaded:', result.file_id);
```

## Monitoring

### Health Check

```bash
curl http://localhost:8004/health
```

Response:
```json
{
  "status": "healthy",
  "service": "files",
  "version": "3.0.0",
  "components": {
    "minio": "healthy",
    "clamav": "disabled"
  }
}
```

## Troubleshooting

### MinIO Connection Failed

- Check if MinIO is running
- Verify endpoint, access key, and secret key
- Test connection: `curl http://localhost:9000/minio/health/live`

### File Upload Fails

- Check file size (must be under MAX_FILE_SIZE_MB)
- Verify file extension is allowed
- Check MinIO bucket permissions

### Virus Scan Errors

- Verify ClamAV daemon is running: `sudo systemctl status clamav-daemon`
- Check ClamAV port: `netstat -an | grep 3310`
- Update virus definitions: `sudo freshclam`

## Development

### Run with auto-reload

```bash
uvicorn main:app --reload --port 8004
```

### View logs

```bash
LOG_LEVEL=DEBUG python main.py
```

## Production

### Security

- Use HTTPS in production
- Implement rate limiting for uploads
- Set appropriate file size limits
- Enable virus scanning
- Restrict allowed file types

### Performance

- Use CDN for file downloads
- Implement file cleanup for old files
- Monitor storage usage
- Consider S3 for production instead of MinIO

### Backup

- Configure MinIO backup strategy
- Replicate to multiple regions
- Regular backup verification
