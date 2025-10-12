from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import pickle
import subprocess

app = Flask(__name__)
app.config['DEBUG'] = True

API_KEY = "hardcoded_secret_key_12345"
DATABASE_PASSWORD = "admin123"

def get_db():
    conn = sqlite3.connect('vulnerable.db')
    return conn

@app.route('/')
def home():
    return jsonify({"message": "Vulnerable Flask Demo App", "endpoints": ["/user", "/search", "/exec", "/deserialize"]})

@app.route('/user/<user_id>')
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return jsonify({"user": user})

@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db()
    cursor = conn.cursor()
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    return jsonify({"results": results})

@app.route('/exec')
def execute_command():
    cmd = request.args.get('cmd', 'ls')
    result = os.system(f"echo {cmd}")
    return jsonify({"output": result})

@app.route('/shell')
def shell_command():
    filename = request.args.get('file', 'test.txt')
    output = subprocess.check_output(f"cat {filename}", shell=True)
    return jsonify({"content": output.decode()})

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    data = request.get_data()
    obj = pickle.loads(data)
    return jsonify({"result": str(obj)})

@app.route('/render')
def render_user_input():
    user_input = request.args.get('content', 'Hello')
    template = f"<html><body><h1>{user_input}</h1></body></html>"
    return render_template_string(template)

@app.route('/eval')
def evaluate_expression():
    expr = request.args.get('expr', '1+1')
    result = eval(expr)
    return jsonify({"result": result})

if __name__ == '__main__':
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL)')
    cursor.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'password123')")
    cursor.execute("INSERT OR IGNORE INTO products VALUES (1, 'Product A', 19.99)")
    conn.commit()
    conn.close()

    app.run(host='0.0.0.0', port=5000, debug=True)
