# AutoThreatMap - Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Docker Desktop installed and running
- 8GB RAM available
- 10GB disk space

### Step 1: Clone and Start

```bash
git clone <your-repo>
cd auto-threatmap
docker-compose up -d
```

Wait ~60 seconds for all services to start.

### Step 2: Verify Services

Check that all services are running:
```bash
docker-compose ps
```

You should see:
- `postgres` - Database (port 5432)
- `backend` - FastAPI (port 8000)
- `zap` - OWASP ZAP (port 8080)
- `localstack` - AWS emulation (port 4566)

### Step 3: Access the Application

**Frontend**: http://localhost:5173
**Backend API Docs**: http://localhost:8000/docs
**Health Check**: http://localhost:8000/health

### Step 4: Run Your First Scan

1. Open http://localhost:5173
2. Click "New Scan" in the navigation
3. Select "Python Flask (Vulnerable Demo)"
4. Check "Static Analysis" and "Threat Modeling"
5. Click "Start Scan"
6. Wait ~30 seconds for scan to complete
7. View findings and threat model

---

## Local Development Setup

### Backend (Python/FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### Frontend (React/TypeScript)

```bash
npm install
npm run dev
```

Frontend runs at http://localhost:5173

---

## Troubleshooting

### Services won't start
```bash
docker-compose down
docker-compose up -d --build
```

### Port conflicts
Edit `docker-compose.yml` to change ports:
```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Scan fails
Check backend logs:
```bash
docker-compose logs backend
```

Verify demo apps exist:
```bash
ls demo-apps/python-flask/app.py
ls demo-apps/node-express/app.js
```

### Frontend can't connect to backend
Update API_BASE in frontend components to match your backend URL.

---

## Demo Data

### Python Flask App Vulnerabilities
- **Critical**: SQL injection, command injection, code injection
- **High**: Insecure deserialization, hardcoded secrets
- **Medium**: XSS, debug mode enabled

### Node.js Express App Vulnerabilities
- **Critical**: Command injection, code injection
- **High**: Hardcoded secrets, insecure CORS
- **Medium**: Weak random number generation

---

## Next Steps

1. **Explore findings**: Click on findings to see evidence and remediation plans
2. **View threat model**: Check the "Threats" tab to see STRIDE analysis
3. **Try CI/CD**: Copy `.github/workflows/security-scan.yml` to your repo
4. **Customize**: Add your own apps to scan
5. **Extend**: Add new scanners or threat detection rules

---

## Useful Commands

```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f postgres

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Clean up everything
docker-compose down -v  # Warning: deletes all scan data
```

---

## API Examples

### Start a scan
```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/demo-apps/python-flask",
    "scan_types": ["sast", "threat_model"]
  }'
```

### Get scan status
```bash
curl http://localhost:8000/api/scan/SCAN-xxxxxxxxxxxx
```

### Get findings
```bash
curl http://localhost:8000/api/findings?scan_id=SCAN-xxxxxxxxxxxx
```

### Get statistics
```bash
curl http://localhost:8000/api/stats
```

---

## Configuration

### Environment Variables

Create `.env` file:
```bash
DATABASE_URL=postgresql://admin:securepass123@postgres:5432/threatmap
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
```

### Scan Configuration

Edit `backend/app/main.py` to configure:
- Scanner timeouts
- Risk scoring weights
- Remediation templates

### Frontend Configuration

Edit `src/components/*.tsx` to configure:
- API_BASE URL
- Polling intervals
- UI themes

---

## Performance Tips

1. **Faster scans**: Reduce scanner timeouts in backend
2. **Less memory**: Run only backend + postgres without ZAP/LocalStack
3. **Better UI**: Enable React strict mode in production builds

---

## Security Note

**This platform includes intentionally vulnerable applications for demonstration purposes.**

⚠️ **Never deploy demo apps to production**
⚠️ **Never expose demo apps to the internet**
⚠️ **Use demo apps only in isolated development environments**

The main AutoThreatMap platform follows security best practices, but the demo apps are designed to be insecure for testing and education.

---

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See `/docs` folder for detailed guides
- **Demo Video**: [Link to demo]

---

**Ready to scan? Start with the Python Flask demo to see 12+ vulnerabilities detected instantly.**
