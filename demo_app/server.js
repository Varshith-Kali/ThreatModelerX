/**
 * Vulnerable Node.js/Express Application
 * Contains intentional security vulnerabilities for testing
 * DO NOT use in production!
 */

const express = require('express');
const mysql = require('mysql');
const { exec } = require('child_process');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// VULNERABILITY: Hardcoded credentials (CWE-798)
const DB_PASSWORD = 'root123';
const SECRET_KEY = 'my-secret-key-12345';

// VULNERABILITY: Insecure CORS configuration (CWE-942)
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', '*');
    next();
});

// Database connection
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: DB_PASSWORD,
    database: 'testdb'
});

app.get('/', (req, res) => {
    res.send(`
        <h1>Vulnerable Demo App</h1>
        <ul>
            <li><a href="/users?id=1">SQL Injection</a></li>
            <li><a href="/search?q=test">XSS Demo</a></li>
            <li><a href="/exec?cmd=ls">Command Injection</a></li>
        </ul>
    `);
});

// VULNERABILITY: SQL Injection (CWE-89)
app.get('/users', (req, res) => {
    const userId = req.query.id;
    const query = `SELECT * FROM users WHERE id = ${userId}`;

    db.query(query, (err, results) => {
        if (err) return res.status(500).send(err);
        res.json(results);
    });
});

// VULNERABILITY: Cross-Site Scripting (CWE-79)
app.get('/search', (req, res) => {
    const searchQuery = req.query.q;
    res.send(`<h2>Search results for: ${searchQuery}</h2>`);
});

// VULNERABILITY: Command Injection (CWE-78)
app.get('/exec', (req, res) => {
    const command = req.query.cmd;
    exec(command, (error, stdout, stderr) => {
        if (error) {
            res.send(`Error: ${error.message}`);
            return;
        }
        res.send(`<pre>${stdout}</pre>`);
    });
});

// VULNERABILITY: Code Injection via eval (CWE-95)
app.post('/calculate', (req, res) => {
    const expression = req.body.expr;
    try {
        const result = eval(expression);
        res.json({ result });
    } catch (e) {
        res.status(400).json({ error: e.message });
    }
});

// VULNERABILITY: Weak random number generation (CWE-338)
app.get('/token', (req, res) => {
    const token = Math.random().toString(36).substring(7);
    res.json({ token });
});

// VULNERABILITY: Path Traversal (CWE-22)
app.get('/file', (req, res) => {
    const filename = req.query.name;
    const fs = require('fs');
    fs.readFile(`./uploads/${filename}`, 'utf8', (err, data) => {
        if (err) return res.status(404).send('File not found');
        res.send(data);
    });
});

// VULNERABILITY: Missing authentication
app.get('/admin', (req, res) => {
    res.json({ message: 'Admin panel - no authentication required!' });
});

// VULNERABILITY: Sensitive data in logs
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    console.log(`Login attempt: ${username}:${password}`);
    res.json({ success: true });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

module.exports = app;
