from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from werkzeug.exceptions import InternalServerError

from app import login_manager
from app.daos import user_dao

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template('auth/login.html')

    data = request.form
    email = data.get('email', "")
    password = data.get('password', "")

    try:
        user = user_dao.auth_user(email.strip(), password.strip())
        login_user(user)

        next_url = request.args.get('next')
        return redirect(next_url if next_url else '/')

    except Exception:
        return render_template('auth/login.html', err_msg="Incorrect email or password")


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('auth/register.html')

    data = request.form
    password = data.get('password')
    confirm = data.get('confirm')
    if password != confirm:
        err_msg = "Passwords do not match"
        return render_template('auth/register.html', err_msg=err_msg)

    name = data.get('name').strip()
    email = data.get('email').strip()
    avatar = request.files.get('avatar')

    try:
        user_dao.add_user(name=name, email=email, password=password, avatar=avatar)
        return redirect(url_for('auth.login'))

    except (ValueError, InternalServerError) as ex:
        return render_template('auth/register.html', err_msg=str(ex))


@auth.route('/logout')
def logout():
    logout_user()
    return redirect('/auth/login')


@login_manager.user_loader
def load_user(id):
    return user_dao.get_user_by_id(id)
