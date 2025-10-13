# Vulnerable Go Gin Demo App

This is a deliberately vulnerable Go Gin application for security testing and demonstration purposes.

## Vulnerabilities

- SQL Injection
- Command Injection
- Hardcoded Credentials
- Insecure Configuration

## Running the Application

```bash
cd go-gin
go run main.go
```

The application will be available at http://localhost:8081

## Endpoints

- `/` - Home page
- `/user/:id` - SQL Injection vulnerability
- `/search?q=query` - SQL Injection vulnerability
- `/exec?cmd=command` - Command Injection vulnerability
- `/admin?username=admin&password=admin123` - Hardcoded credentials