"""
Demo Vulnerable Web Application
This is a sample application with intentional security vulnerabilities for testing purposes.
DO NOT use this code in production!
"""

from flask import Flask, request, render_template_string, redirect
import sqlite3
import pickle
import os
import hashlib

app = Flask(__name__)

# VULNERABILITY: Hardcoded credentials (CWE-798)
DATABASE_PASSWORD = "admin123"
API_KEY = "sk_test_1234567890abcdef"

@app.route('/')
def index():
    return """
    <h1>Vulnerable Demo App</h1>
    <p>This application contains intentional security vulnerabilities for testing.</p>
    <ul>
        <li><a href="/search">SQL Injection Demo</a></li>
        <li><a href="/upload">File Upload Demo</a></li>
        <li><a href="/user">XSS Demo</a></li>
    </ul>
    """

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    # VULNERABILITY: SQL Injection (CWE-89)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%'"
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    
    return f"<h2>Search Results:</h2><pre>{results}</pre>"

@app.route('/user')
def user_profile():
    username = request.args.get('name', 'Guest')
    
    # VULNERABILITY: Cross-Site Scripting (CWE-79)
    template = f"""
    <html>
        <body>
            <h1>Welcome, {username}!</h1>
            <p>Your profile page</p>
        </body>
    </html>
    """
    return render_template_string(template)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    
    # VULNERABILITY: Unrestricted File Upload (CWE-434)
    if file:
        filename = file.filename
        file.save(os.path.join('/uploads', filename))
        return f"File {filename} uploaded successfully"
    
    return "No file uploaded"

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    data = request.data
    
    # VULNERABILITY: Insecure Deserialization (CWE-502)
    obj = pickle.loads(data)
    return f"Deserialized: {obj}"

@app.route('/command')
def run_command():
    cmd = request.args.get('cmd', 'ls')
    
    # VULNERABILITY: Command Injection (CWE-78)
    result = os.popen(cmd).read()
    return f"<pre>{result}</pre>"

def hash_password(password):
    # VULNERABILITY: Use of weak cryptographic algorithm (CWE-327)
    return hashlib.md5(password.encode()).hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # VULNERABILITY: Weak password hashing
    hashed = hash_password(password)
    
    # VULNERABILITY: SQL Injection in authentication
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return redirect('/dashboard')
    return "Login failed"

# VULNERABILITY: Debug mode enabled in production (CWE-489)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
