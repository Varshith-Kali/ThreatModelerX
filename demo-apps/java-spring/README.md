# Vulnerable Java Spring Demo App

This is a deliberately vulnerable Java Spring Boot application for security testing and demonstration purposes.

## Vulnerabilities

- SQL Injection
- Command Injection
- Hardcoded Credentials
- Insecure Configuration

## Running the Application

```bash
cd java-spring
./mvnw spring-boot:run
```

The application will be available at http://localhost:8080

## Endpoints

- `/` - Home page
- `/user/{id}` - SQL Injection vulnerability
- `/search?q=query` - SQL Injection vulnerability
- `/exec?cmd=command` - Command Injection vulnerability
- `/admin?username=admin&password=admin123` - Hardcoded credentials