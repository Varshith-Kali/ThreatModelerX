# Demo Vulnerable Application

This is a sample application with **intentional security vulnerabilities** for testing the ThreatModelerX security scanner.

## ⚠️ WARNING

**DO NOT deploy this application to production or expose it to the internet!**

This application contains multiple security vulnerabilities and is meant ONLY for:
- Testing security scanners
- Security training
- Demonstration purposes

## Vulnerabilities Included

### Python (app.py)
- SQL Injection (CWE-89)
- Cross-Site Scripting (CWE-79)
- Command Injection (CWE-78)
- Insecure Deserialization (CWE-502)
- Hardcoded Credentials (CWE-798)
- Weak Cryptography (CWE-327)
- Debug Mode Enabled (CWE-489)
- Unrestricted File Upload (CWE-434)

### Node.js (server.js)
- SQL Injection (CWE-89)
- Cross-Site Scripting (CWE-79)
- Command Injection (CWE-78)
- Code Injection via eval (CWE-95)
- Path Traversal (CWE-22)
- Weak Random Number Generation (CWE-338)
- Insecure CORS (CWE-942)
- Hardcoded Credentials (CWE-798)
- Missing Authentication
- Sensitive Data in Logs

### Dependencies (package.json)
- Vulnerable jQuery version (1.8.1)
- Vulnerable Lodash version (4.17.11)

## Usage

To test the scanner with this application:

1. Zip this folder
2. Upload to ThreatModelerX
3. Select scan types: SAST, Threat Modeling
4. Review the detected vulnerabilities

## Expected Results

The scanner should detect:
- 15+ security findings
- Multiple STRIDE threats
- High and Critical severity issues
- CWE mappings for each vulnerability

## Files

- `app.py` - Vulnerable Python Flask application
- `server.js` - Vulnerable Node.js/Express application  
- `package.json` - Dependencies with known vulnerabilities
- `README.md` - This file
