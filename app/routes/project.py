from flask import Blueprint, request, render_template, redirect, url_for, session, flash
import sqlite3

bp = Blueprint('project', __name__, url_prefix='/project')

@bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('project.dashboard'))

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM projects WHERE user_id = ?", (session['user_id'],))
    projects = c.fetchall()
    c.execute("SELECT t.id, t.description, t.assigned_to, t.status, p.name FROM tasks t JOIN projects p ON t.project_id = p.id WHERE p.user_id = ?", (session['user_id'],))
    tasks = c.fetchall()
    c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return render_template('dashboard/dashboard.html', projects=projects, tasks=tasks, user=user)

@bp.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        name = request.form['name']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO projects (name, user_id) VALUES (?, ?)", (name, session['user_id']))
        conn.commit()
        conn.close()
        flash('Thêm dự án thành công!', 'success')
        return redirect(url_for('project.dashboard'))
    return render_template('project/add_project.html')

@bp.route('/add_task/<int:project_id>', methods=['GET', 'POST'])
def add_task(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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
        flash('Thêm nhiệm vụ thành công!', 'success')
        return redirect(url_for('project.dashboard'))
    return render_template('project/add_task.html', project_id=project_id)

@bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        c.execute("UPDATE projects SET name = ? WHERE id = ? AND user_id = ?", 
                  (name, project_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('Cập nhật dự án thành công!', 'success')
        return redirect(url_for('project.dashboard'))
    c.execute("SELECT name FROM projects WHERE id = ? AND user_id = ?", (project_id, session['user_id']))
    project = c.fetchone()
    conn.close()
    if not project:
        flash('Không tìm thấy dự án!', 'error')
        return redirect(url_for('project.dashboard'))
    return render_template('project/edit_project.html', project_id=project_id, project=project)

@bp.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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
        flash('Cập nhật nhiệm vụ thành công!', 'success')
        return redirect(url_for('project.dashboard'))
    c.execute("SELECT description, assigned_to, status FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    conn.close()
    if not task:
        flash('Không tìm thấy nhiệm vụ!', 'error')
        return redirect(url_for('project.dashboard'))
    return render_template('project/edit_task.html', task_id=task_id, task=task)

@bp.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        c.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, session['user_id']))
        conn.commit()
        flash('Xóa dự án thành công!', 'success')
    except Exception as e:
        print(f"Error deleting project: {e}")
        flash('Lỗi khi xóa dự án!', 'error')
    finally:
        conn.close()
    return redirect(url_for('project.dashboard'))

@bp.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        flash('Xóa nhiệm vụ thành công!', 'success')
    except Exception as e:
        print(f"Error deleting task: {e}")
        flash('Lỗi khi xóa nhiệm vụ!', 'error')
    finally:
        conn.close()
    return redirect(url_for('project.dashboard'))

@bp.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        keyword = request.form['keyword'].lower()
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM projects WHERE user_id = ? AND lower(name) LIKE ?", 
                  (session['user_id'], f'%{keyword}%'))
        projects = c.fetchall()
        c.execute("SELECT t.id, t.description, t.assigned_to, t.status, p.name FROM tasks t JOIN projects p ON t.project_id = p.id WHERE p.user_id = ? AND (lower(t.description) LIKE ? OR lower(t.assigned_to) LIKE ?)", 
                  (session['user_id'], f'%{keyword}%', f'%{keyword}%'))
        tasks = c.fetchall()
        users = set(task[2] for task in tasks if task[2].lower().find(keyword) != -1)
        conn.close()
        return render_template('project/search_results.html', projects=projects, tasks=tasks, users=users, keyword=keyword)
    return render_template('project/search.html')