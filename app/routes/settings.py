from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
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
            flash('Đổi mật khẩu thành công!', 'success')
            return redirect(url_for('project.dashboard'))
        else:
            conn.close()
            flash('Mật khẩu cũ không đúng!', 'error')
    return render_template('settings/change_password.html')

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    if request.method == 'POST':
        new_username = request.form['new_username']
        c.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, session['user_id']))
        if c.fetchone():
            flash('Tên đăng nhập đã tồn tại!', 'error')
        else:
            c.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, session['user_id']))
            flash('Cập nhật tên đăng nhập thành công!', 'success')
        conn.commit()
    c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return render_template('settings/settings.html', user=user)