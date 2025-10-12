const express = require('express');
const app = express();
const { exec } = require('child_process');

app.use(express.json());

const API_SECRET = "my_secret_api_key_123";
const admin_password = "admin123";

app.get('/', (req, res) => {
  res.json({
    message: 'Vulnerable Node.js Express Demo App',
    endpoints: ['/ping', '/eval', '/admin', '/cors-test']
  });
});

app.get('/ping', (req, res) => {
  const host = req.query.host || 'localhost';
  exec(`ping -c 1 ${host}`, (error, stdout, stderr) => {
    res.json({ output: stdout, error: stderr });
  });
});

app.get('/eval', (req, res) => {
  const code = req.query.code || '1+1';
  try {
    const result = eval(code);
    res.json({ result });
  } catch (e) {
    res.json({ error: e.message });
  }
});

app.get('/admin', (req, res) => {
  const username = req.query.username;
  const password = req.query.password;

  if (username === 'admin' && password === admin_password) {
    res.json({ message: 'Welcome admin!', token: API_SECRET });
  } else {
    res.json({ message: 'Access denied' });
  }
});

app.get('/cors-test', (req, res) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', '*');
  res.json({ sensitive: 'data', secret: API_SECRET });
});

app.post('/upload', (req, res) => {
  const userData = req.body;
  const userHtml = `<div>${userData.content}</div>`;
  res.send(userHtml);
});

const crypto = require('crypto');

app.get('/random-token', (req, res) => {
  const token = Math.random().toString(36).substring(7);
  res.json({ token });
});

app.get('/secure-random', (req, res) => {
  const token = crypto.randomBytes(16).toString('hex');
  res.json({ token });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Vulnerable app listening on port ${PORT}`);
  console.log(`Debug mode: true`);
});
