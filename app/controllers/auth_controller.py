from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, current_user, logout_user
from werkzeug.exceptions import InternalServerError

from app import login_manager
from app.daos import auth_user, add_user, get_user_by_id

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template('auth/login.html')

    data = request.form
    email = data.get('email', "")
    password = data.get('password', "")

    try:
        user = auth_user(email.strip(), password.strip())
        login_user(user)

        next = request.args.get('next')
        return redirect(next if next else '/')

    except Exception as ex:
        return render_template('auth/login.html', err_msg=str(ex))


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

    try:
        user = add_user(name=data.get('name'), email=data.get('email'), password=password)
        return redirect(url_for('auth.login'))

    except (ValueError, InternalServerError) as ex:
        return render_template('auth/register.html', err_msg=str(ex))


@auth.route('/logout')
def logout():
    logout_user()
    return redirect('/auth/login')


@login_manager.user_loader
def load_user(id):
    return get_user_by_id(id)
