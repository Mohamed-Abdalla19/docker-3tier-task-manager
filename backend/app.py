import time
import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import OperationalError

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'tasks_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'password')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def wait_for_db(max_retries=20, delay=3):
    for i in range(max_retries):
        try:
            conn = get_connection()
            conn.close()
            print(f"[+] Connected to DB on attempt {i+1}")
            return True
        except OperationalError as e:
            print(f"[-] DB not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Database connection failed after multiple retries.")

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[+] Table 'tasks' ensured.")

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM tasks ORDER BY id;")
    tasks = [{'id': t[0], 'title': t[1]} for t in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(tasks)

@app.route('/add', methods=['POST'])
def add_task():
    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title required'}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s);", (title,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Task added!'})

@app.route('/delete/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    deleted_rows = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    if deleted_rows == 0:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({'message': f'Task {task_id} deleted'})

if __name__ == '__main__':
    print("[*] Waiting for DB to be ready...")
    wait_for_db()
    print("[*] Initializing DB...")
    init_db()
    print("[*] Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
