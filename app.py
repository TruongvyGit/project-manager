from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Thay bằng key ngẫu nhiên

# Khởi tạo database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (id INTEGER PRIMARY KEY, name TEXT, user_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY, project_id INTEGER, description TEXT, assigned_to TEXT, status TEXT)''')
    c.execute("SELECT id FROM users WHERE username = ?", ('admin',))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  ('admin', generate_password_hash('1234')))
    conn.commit()
    conn.close()

# Hàm tạo mật khẩu ngẫu nhiên
def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    return render_template('login.html')

# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            flash('Username already exists!', 'error')
            conn.close()
            return redirect(url_for('register'))
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  (username, generate_password_hash(password)))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route quên mật khẩu
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if user:
            new_password = generate_random_password()
            c.execute("UPDATE users SET password = ? WHERE username = ?", 
                      (generate_password_hash(new_password), username))
            conn.commit()
            conn.close()
            flash(f'Your new password is: {new_password}. Please login and change it.', 'success')
            return redirect(url_for('login'))
        else:
            conn.close()
            flash('Username not found!', 'error')
    return render_template('forgot_password.html')

# Route thay đổi mật khẩu
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        if user and check_password_hash(user[0], old_password):
            c.execute("UPDATE users SET password = ? WHERE id = ?", 
                      (generate_password_hash(new_password), session['user_id']))
            conn.commit()
            conn.close()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
        else:
            conn.close()
            flash('Old password is incorrect!', 'error')
    return render_template('change_password.html')

# Route đăng xuất
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Route trang chính
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

    # Route tìm kiếm
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        keyword = request.form['keyword'].lower()
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # Tìm kiếm project
        c.execute("SELECT id, name FROM projects WHERE user_id = ? AND lower(name) LIKE ?", 
                  (session['user_id'], f'%{keyword}%'))
        projects = c.fetchall()
        # Tìm kiếm task
        c.execute("SELECT t.id, t.description, t.assigned_to, t.status, p.name FROM tasks t JOIN projects p ON t.project_id = p.id WHERE p.user_id = ? AND (lower(t.description) LIKE ? OR lower(t.assigned_to) LIKE ?)", 
                  (session['user_id'], f'%{keyword}%', f'%{keyword}%'))
        tasks = c.fetchall()
        # Tìm kiếm user (chỉ tìm assigned_to trong tasks)
        users = set(task[2] for task in tasks if task[2].lower().find(keyword) != -1)
        conn.close()
        return render_template('search_results.html', projects=projects, tasks=tasks, users=users, keyword=keyword)
    return render_template('search.html')

# Route thêm dự án
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

# Route thêm nhiệm vụ
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

    # Route sửa dự án
@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        c.execute("UPDATE projects SET name = ? WHERE id = ? AND user_id = ?", 
                  (name, project_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('index'))
    c.execute("SELECT name FROM projects WHERE id = ? AND user_id = ?", (project_id, session['user_id']))
    project = c.fetchone()
    conn.close()
    if not project:
        flash('Project not found!', 'error')
        return redirect(url_for('index'))
    return render_template('edit_project.html', project_id=project_id, project=project)

# Route xóa dự án
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

    # Route sửa nhiệm vụ
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        status = request.form['status']
        c.execute("UPDATE tasks SET description = ?, assigned_to = ?, status = ? WHERE id = ?", 
                  (description, assigned_to, status, task_id))
        conn.commit()
        conn.close()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('index'))
    c.execute("SELECT description, assigned_to, status FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    conn.close()
    if not task:
        flash('Task not found!', 'error')
        return redirect(url_for('index'))
    return render_template('edit_task.html', task_id=task_id, task=task)

# Route xóa nhiệm vụ
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
    app.run(debug=True, host='0.0.0.0', port=5000)