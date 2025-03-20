import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from ifc_app.db import get_db
from ifc_app.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    password2 = PasswordField('パスワード（確認）', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('登録')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        db = get_db()
        error = None

        if db.execute('SELECT id FROM user WHERE username = ?', 
            (form.username.data,)).fetchone() is not None:
            error = 'ユーザー名 {} は既に登録されています。'.format(form.username.data)
        elif db.execute('SELECT id FROM user WHERE email = ?',
            (form.email.data,)).fetchone() is not None:
            error = 'メールアドレス {} は既に登録されています。'.format(form.email.data)

        if error is None:
            db.execute(
                'INSERT INTO user (username, email, password) VALUES (?, ?, ?)',
                (form.username.data, form.email.data, generate_password_hash(form.password.data))
            )
            db.commit()
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))

        flash(error, 'error')

    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        user_data = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user_data is None:
            error = 'ユーザー名が正しくありません'
        elif not check_password_hash(user_data['password'], password):
            error = 'パスワードが正しくありません'

        if error is None:
            user = User(user_data['id'], user_data['username'])
            login_user(user)
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))