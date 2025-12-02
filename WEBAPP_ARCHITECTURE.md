# Web Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser (Client)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ Dashboard  │  │   Report   │  │   Live Logs Display    │ │
│  │    Tab     │  │    Tab     │  │   (Auto-scroll)        │ │
│  └────────────┘  └────────────┘  └────────────────────────┘ │
│         │              │                     │                │
│         └──────────────┴─────────────────────┘                │
│                        │                                      │
│                   JavaScript                                  │
│              (Polling every 1 second)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Flask Web Server (app.py)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                      │   │
│  │  • POST /api/analyze    - Start analysis             │   │
│  │  • GET  /api/status     - Get status & logs          │   │
│  │  • GET  /api/report     - Get report data            │   │
│  │  • GET  /api/reports    - List all reports           │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Analysis State Manager                   │   │
│  │  • Running status                                     │   │
│  │  • Log messages buffer                                │   │
│  │  • Result file tracking                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Background Thread Manager                  │   │
│  │  • Spawns analysis thread                             │   │
│  │  • Captures stdout/stderr                             │   │
│  │  • Updates state in real-time                         │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ subprocess.Popen
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Analysis Engine (main_github.py)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Command Line Interface               │   │
│  │  • Argument parsing                                   │   │
│  │  • Mode selection (GitHub/Local/SBOM)                │   │
│  │  • Configuration loading                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Analysis Orchestration                   │   │
│  │  • Data collection                                    │   │
│  │  • SBOM generation                                    │   │
│  │  • Multi-agent coordination                           │   │
│  │  • Report generation                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│         ┌───────────────┼───────────────┐                    │
│         ▼               ▼               ▼                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐            │
│  │  Tools   │   │  Agents  │   │   External   │            │
│  │  Layer   │   │  Layer   │   │     APIs     │            │
│  └──────────┘   └──────────┘   └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Files (outputs/)                   │
│  • {timestamp}_findings.json                                 │
│  • {timestamp}_report.html                                   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Initiates Analysis

```
User Input → JavaScript → POST /api/analyze → Flask Handler
                                                     │
                                                     ▼
                                            Spawn Background Thread
                                                     │
                                                     ▼
                                            Execute main_github.py
```

### 2. Real-time Status Updates

```
Analysis Running → stdout/stderr → Log Buffer → analysis_state
                                                      │
                                                      ▼
JavaScript Polling → GET /api/status → Return Logs & Status
                                                      │
                                                      ▼
                                            Update UI in Real-time
```

### 3. Report Generation

```
Analysis Complete → Save to outputs/ → Update analysis_state
                                              │
                                              ▼
User Switches Tab → GET /api/report → Load JSON File
                                              │
                                              ▼
                                    Render Interactive Report
```

## Component Details

### Frontend (templates/index.html)

**Technologies:**
- Pure HTML5/CSS3/JavaScript
- No external frameworks (lightweight)
- Responsive design
- Real-time updates via polling

**Key Features:**
- Tab-based navigation
- Mode toggle buttons
- Live log streaming
- Auto-scroll logs
- Interactive report rendering
- Statistics dashboard

### Backend (app.py)

**Technologies:**
- Flask web framework
- Threading for background tasks
- Subprocess for analysis execution
- JSON for data exchange

**Key Components:**

1. **API Routes:**
   - RESTful endpoints
   - JSON request/response
   - Error handling

2. **State Management:**
   - Global analysis_state dict
   - Thread-safe operations
   - Log buffering

3. **Background Execution:**
   - Daemon threads
   - Process output streaming
   - Exit code handling

### Analysis Engine (main_github.py)

**Unchanged from CLI version:**
- Same command-line interface
- Same analysis logic
- Same output format
- Fully compatible

## Communication Protocol

### Request Format (POST /api/analyze)

```json
{
  "mode": "github|local|sbom",
  "target": "url_or_path",
  "confidence": 0.7,
  "skip_update": false,
  "skip_osv": false
}
```

### Response Format (GET /api/status)

```json
{
  "running": true,
  "status": "running|completed|failed|idle",
  "logs": [
    {
      "timestamp": "2023-12-01 14:30:22",
      "level": "info",
      "message": "Starting analysis..."
    }
  ],
  "result_file": "20231201_143022_findings.json",
  "start_time": "2023-12-01T14:30:22",
  "end_time": null
}
```

### Report Format (GET /api/report)

```json
{
  "findings": [
    {
      "package": "malicious-pkg",
      "version": "1.0.0",
      "severity": "critical",
      "finding_type": "malicious_package",
      "confidence": 0.95,
      "evidence": ["..."],
      "recommendations": ["..."]
    }
  ],
  "metadata": {
    "target": "https://github.com/owner/repo",
    "analysis_type": "github",
    "timestamp": "2023-12-01T14:30:22",
    "confidence_threshold": 0.7
  }
}
```

## Scalability Considerations

### Current Design (Single User)

- ✅ Simple architecture
- ✅ No database required
- ✅ Easy to deploy
- ✅ Low resource usage
- ⚠️ One analysis at a time
- ⚠️ No user authentication

### Future Enhancements

For multi-user deployment:

1. **Queue System:**
   - Redis/Celery for task queue
   - Multiple worker processes
   - Concurrent analyses

2. **Database:**
   - PostgreSQL for persistence
   - User accounts
   - Analysis history

3. **WebSockets:**
   - Replace polling with push
   - Real-time updates
   - Lower latency

4. **Authentication:**
   - User login system
   - API key management
   - Role-based access

## Security Considerations

### Current Implementation

- ✅ Runs locally (localhost only)
- ✅ No external data storage
- ✅ API keys in .env file
- ✅ Input validation
- ⚠️ No authentication (local use)
- ⚠️ Debug mode enabled

### Production Deployment

For public deployment, add:

1. **Authentication:**
   - User login system
   - Session management
   - CSRF protection

2. **Input Validation:**
   - Sanitize all inputs
   - Path traversal prevention
   - Rate limiting

3. **HTTPS:**
   - SSL/TLS encryption
   - Secure cookies
   - HSTS headers

4. **Process Isolation:**
   - Containerization (Docker)
   - Resource limits
   - Sandboxing

## Performance Optimization

### Current Performance

- **Startup Time:** < 1 second
- **Status Polling:** 1 second interval
- **Log Buffer:** In-memory (unlimited)
- **File I/O:** Direct file system access

### Optimization Opportunities

1. **Caching:**
   - Cache SBOM generation
   - Cache API responses
   - Cache database queries

2. **Async Operations:**
   - Async file I/O
   - Async API calls
   - WebSocket updates

3. **Resource Management:**
   - Log rotation
   - Temp file cleanup
   - Memory limits

## Deployment Options

### Local Development

```bash
python app.py
# Access at http://localhost:5000
```

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Container

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### Cloud Deployment

- **Heroku:** Simple git push deployment
- **AWS:** EC2 or Elastic Beanstalk
- **Google Cloud:** App Engine or Cloud Run
- **Azure:** App Service

## Monitoring & Logging

### Current Logging

- Console output (stdout)
- In-memory log buffer
- File-based results

### Production Monitoring

Add:
- Application logging (loguru)
- Error tracking (Sentry)
- Performance monitoring (New Relic)
- Health check endpoints

## Testing Strategy

### Unit Tests

- API endpoint tests
- State management tests
- Background thread tests

### Integration Tests

- End-to-end workflow tests
- Browser automation (Selenium)
- Load testing (Locust)

### Manual Testing

- Cross-browser testing
- Mobile responsiveness
- Error scenario testing

---

**Note:** This architecture is designed for simplicity and ease of use. For production deployment with multiple users, consider the scalability and security enhancements mentioned above.
