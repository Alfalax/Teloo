# TeLOO V3 Alert System

## Overview

The Alert System monitors critical KPIs and automatically sends notifications when thresholds are exceeded. It supports configurable thresholds, multiple notification channels (email, Slack), and provides comprehensive alerting capabilities for system health monitoring.

## Features

- **Configurable Thresholds**: Set custom thresholds for any metric
- **Multiple Notification Channels**: Email and Slack notifications
- **Automatic Monitoring**: Runs every 5 minutes via scheduled job
- **Alert Suppression**: Prevents spam by limiting alerts to once per hour
- **Alert History**: Complete audit trail of all triggered alerts
- **Severity Levels**: LOW, MEDIUM, HIGH, CRITICAL based on threshold deviation
- **Default Alerts**: Pre-configured alerts for critical system metrics

## Default Alerts

The system comes with 5 pre-configured alerts for critical metrics:

| Alert Name | Metric | Threshold | Severity | Channels |
|------------|--------|-----------|----------|----------|
| Tasa de Error Alta | `tasa_error` | > 5% | HIGH | email, slack |
| Latencia P95 Alta | `latencia_promedio` | > 300ms | MEDIUM | slack |
| Tasa de Conversión Baja | `tasa_conversion` | < 10% | MEDIUM | email |
| Disponibilidad del Sistema Baja | `disponibilidad_sistema` | < 99% | CRITICAL | email, slack |
| Alto Porcentaje de Solicitudes sin Ofertas | `solicitudes_sin_ofertas_pct` | > 30% | HIGH | email, slack |

## Configuration

### Environment Variables

```bash
# Alert System Configuration
ALERT_CHECK_INTERVAL=300          # Check interval in seconds (5 minutes)
ALERT_ERROR_RATE=0.05            # Error rate threshold (5%)
ALERT_LATENCY_P95=300            # Latency threshold in ms
ALERT_CONVERSION_RATE=0.1        # Conversion rate threshold (10%)

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=alerts@teloo.com
ALERT_EMAIL_TO=admin@teloo.com,ops@teloo.com

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts
```

### Email Setup

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password in `SMTP_PASSWORD`

For other providers, adjust `SMTP_SERVER` and `SMTP_PORT` accordingly.

### Slack Setup

1. Create a Slack App in your workspace
2. Enable Incoming Webhooks
3. Create a webhook for your desired channel
4. Use the webhook URL in `SLACK_WEBHOOK_URL`

## API Endpoints

### Get Active Alerts
```http
GET /alerts/
```

### Create Custom Alert
```http
POST /alerts/
Content-Type: application/json

{
  "nombre": "High CPU Usage",
  "metrica_nombre": "cpu_usage",
  "operador": ">",
  "valor_umbral": 80.0,
  "canales_notificacion": ["email", "slack"]
}
```

### Update Alert
```http
PUT /alerts/{alert_id}
Content-Type: application/json

{
  "valor_umbral": 90.0,
  "activa": true
}
```

### Delete Alert
```http
DELETE /alerts/{alert_id}
```

### Get Alert History
```http
GET /alerts/history?days=7
```

### Manual Alert Check
```http
POST /alerts/check
```

### Test Notifications
```http
POST /alerts/test/email
POST /alerts/test/slack
```

### Get Available Metrics
```http
GET /alerts/metrics/available
```

### Get Alert System Status
```http
GET /alerts/status
```

## Available Metrics

| Metric Name | Description | Unit | Recommended Thresholds |
|-------------|-------------|------|----------------------|
| `tasa_error` | System error rate | percentage | Warning: 2%, Critical: 5% |
| `latencia_promedio` | Average response latency | milliseconds | Warning: 200ms, Critical: 500ms |
| `tasa_conversion` | Request conversion rate | percentage | Warning: 15%, Critical: 10% |
| `disponibilidad_sistema` | System availability | percentage | Warning: 98%, Critical: 95% |
| `solicitudes_sin_ofertas_pct` | Requests without offers | percentage | Warning: 20%, Critical: 30% |

## Alert Operators

- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `==` - Equal to
- `!=` - Not equal to

## Severity Levels

Severity is automatically determined based on how far the current value deviates from the threshold:

- **LOW**: Minor deviation
- **MEDIUM**: Moderate deviation
- **HIGH**: Significant deviation (2x threshold)
- **CRITICAL**: Severe deviation (3x threshold) or system availability issues

## Alert Suppression

To prevent alert spam, the system implements suppression logic:
- Same alert can only be triggered once per hour
- Suppression is tracked per alert configuration
- Manual alert checks bypass suppression

## Notification Formats

### Email Notifications

- HTML formatted emails with alert details
- Includes metric information, current value, threshold
- Provides recommended actions based on metric type
- Links to dashboard and logs (configurable)

### Slack Notifications

- Rich message format with color coding
- Structured fields for easy reading
- Severity indicators with emojis
- Timestamp and footer information

## Monitoring and Maintenance

### Health Check

The alert system status is included in the main health check endpoint:

```http
GET /health
```

Response includes:
- Alert system status
- Number of active alerts
- Last check timestamp

### Logs

Alert system activities are logged with structured logging:
- Alert triggers and suppressions
- Notification delivery status
- Configuration changes
- Error conditions

### Metrics Cleanup

The system automatically cleans up:
- Expired metrics (based on TTL)
- Old alert history (configurable retention)
- Stale cache entries

## Troubleshooting

### Common Issues

1. **Alerts not triggering**
   - Check if alerts are active: `GET /alerts/`
   - Verify metric values: `GET /alerts/metrics/available`
   - Check scheduler status: `GET /health`

2. **Email notifications not working**
   - Test configuration: `POST /alerts/test/email`
   - Verify SMTP settings in environment variables
   - Check firewall/network connectivity

3. **Slack notifications not working**
   - Test configuration: `POST /alerts/test/slack`
   - Verify webhook URL is correct
   - Check Slack app permissions

4. **High alert volume**
   - Review threshold values
   - Check suppression settings
   - Consider adjusting severity levels

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed information about:
- Alert evaluation process
- Metric calculations
- Notification attempts
- Suppression logic

## Development

### Running Tests

```bash
# Test imports and basic functionality
python test_alert_imports.py

# Test with database (requires setup)
python test_alert_system.py
```

### Adding New Metrics

1. Add metric calculation to `MetricsCalculator`
2. Update `_get_metric_value()` in `AlertManager`
3. Add to available metrics in alerts router
4. Update documentation

### Custom Notification Channels

To add new notification channels:

1. Extend `NotificationService` with new method
2. Update `AlertManager._trigger_alert()` to handle new channel
3. Add channel validation in API endpoints
4. Update configuration documentation

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scheduler     │───▶│  Alert Manager   │───▶│ Notification    │
│  (every 5min)   │    │                  │    │   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Metrics          │    │ Email / Slack   │
                       │ Calculator       │    │ Notifications   │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Database         │
                       │ (Alerts, History)│
                       └──────────────────┘
```

## Security Considerations

- SMTP credentials should be stored securely
- Slack webhook URLs should be protected
- Alert history may contain sensitive system information
- Consider rate limiting for API endpoints
- Validate all user inputs for custom alerts

## Performance

- Alert checks run every 5 minutes by default
- Metrics are cached to reduce database load
- Suppression prevents notification spam
- Cleanup jobs maintain database size
- Async operations prevent blocking

## Future Enhancements

- Integration with external monitoring systems (Prometheus, Grafana)
- SMS notifications via Twilio
- Webhook notifications for custom integrations
- Alert escalation policies
- Machine learning-based anomaly detection
- Custom alert templates
- Alert acknowledgment system