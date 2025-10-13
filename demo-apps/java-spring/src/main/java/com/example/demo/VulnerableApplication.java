package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@SpringBootApplication
@RestController
public class VulnerableApplication {

    private final JdbcTemplate jdbcTemplate;
    private static final String API_KEY = "hardcoded_java_secret_key_12345";
    private static final String ADMIN_PASSWORD = "admin123";

    public VulnerableApplication(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public static void main(String[] args) {
        SpringApplication.run(VulnerableApplication.class, args);
    }

    @GetMapping("/")
    public Map<String, Object> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("message", "Vulnerable Java Spring Demo App");
        response.put("endpoints", new String[]{"/user/{id}", "/search", "/exec", "/admin"});
        return response;
    }

    @GetMapping("/user/{id}")
    public Map<String, Object> getUser(@PathVariable String id) {
        // SQL Injection vulnerability
        String sql = "SELECT * FROM users WHERE id = " + id;
        List<Map<String, Object>> users = jdbcTemplate.queryForList(sql);
        
        Map<String, Object> response = new HashMap<>();
        response.put("user", users.isEmpty() ? null : users.get(0));
        return response;
    }

    @GetMapping("/search")
    public Map<String, Object> search(@RequestParam String q) {
        // SQL Injection vulnerability
        String sql = "SELECT * FROM products WHERE name LIKE '%" + q + "%'";
        List<Map<String, Object>> results = jdbcTemplate.queryForList(sql);
        
        Map<String, Object> response = new HashMap<>();
        response.put("results", results);
        return response;
    }

    @GetMapping("/exec")
    public Map<String, Object> executeCommand(@RequestParam String cmd) {
        // Command injection vulnerability
        Map<String, Object> response = new HashMap<>();
        try {
            Process process = Runtime.getRuntime().exec(cmd);
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
            response.put("output", output.toString());
        } catch (Exception e) {
            response.put("error", e.getMessage());
        }
        return response;
    }

    @GetMapping("/admin")
    public Map<String, Object> admin(@RequestParam String username, @RequestParam String password) {
        // Hardcoded credentials vulnerability
        Map<String, Object> response = new HashMap<>();
        if ("admin".equals(username) && ADMIN_PASSWORD.equals(password)) {
            response.put("message", "Welcome admin!");
            response.put("token", API_KEY);
        } else {
            response.put("message", "Access denied");
        }
        return response;
    }
}