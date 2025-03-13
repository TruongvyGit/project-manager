from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string

bp = Blueprint('auth', __name__)

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@bp.route('/login', methods=['GET', 'POST'])
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
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('project.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            flash('Tên đăng nhập đã tồn tại!', 'error')
            conn.close()
            return redirect(url_for('auth.register'))
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                  (username, generate_password_hash(password)))
        conn.commit()
        conn.close()
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@bp.route('/forgot_password', methods=['GET', 'POST'])
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
            flash(f'Mật khẩu mới của bạn là: {new_password}. Vui lòng đăng nhập và đổi lại.', 'success')
            return redirect(url_for('auth.login'))
        else:
            conn.close()
            flash('Tên đăng nhập không tồn tại!', 'error')
    return render_template('auth/forgot_password.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('auth.login'))