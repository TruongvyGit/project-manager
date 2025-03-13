from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Thay bằng key bất kỳ

# Khởi tạo database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, user_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, project_id INTEGER, description TEXT, assigned_to TEXT, status TEXT)''')
    c.execute("INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', '1234')")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM projects WHERE user_id = ?", (session['user_id'],))
    projects = c.fetchall()
    c.execute("SELECT t.id, t.description, t.assigned_to, t.status, p.name FROM tasks t JOIN projects p ON t.project_id = p.id WHERE p.user_id = ?", (session['user_id'],))
    tasks = c.fetchall()
    conn.close()
    return render_template('index.html', projects=projects, tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        return "Login failed!"
    return render_template('login.html')

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, user_id) VALUES (?, ?)", (name, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_project.html')

@app.route('/add_task/<int:project_id>', methods=['GET', 'POST'])
def add_task(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        status = request.form['status']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO tasks (project_id, description, assigned_to, status) VALUES (?, ?, ?, ?)", 
                  (project_id, description, assigned_to, status))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_task.html', project_id=project_id)

@app.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        c.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, session['user_id']))
        conn.commit()
    except Exception as e:
        print(f"Error deleting project: {e}")
        return "Error deleting project", 500
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    except Exception as e:
        print(f"Error deleting task: {e}")
        return "Error deleting task", 500
    finally:
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)