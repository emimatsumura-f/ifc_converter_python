# このファイルは認証（ログインや登録）に関する機能を管理します

# 必要なライブラリをインポートします
import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from ifc_app.db import get_db
from ifc_app.models import User

# Blueprintを作成して、URLのプレフィックスを'/auth'に設定
# これにより、すべての認証関連のURLは'/auth/...'となります
bp = Blueprint('auth', __name__, url_prefix='/auth')

# ユーザー登録フォームの定義
# FlaskFormを継承して、登録に必要なフィールドを定義します
class RegistrationForm(FlaskForm):
    # 各フィールドにはバリデーション（入力チェック）が設定されています
    username = StringField('ユーザー名', validators=[DataRequired()])  # 必須項目
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])  # メール形式チェック
    password = PasswordField('パスワード', validators=[
        DataRequired(),
        Length(min=6, max=6, message='パスワードは6文字で入力してください'),
        Regexp('^[0-9]*$', message='パスワードは数字のみで入力してください')
    ])
    password2 = PasswordField('パスワード（確認）', validators=[DataRequired(), EqualTo('password', message='パスワードが一致しません')])  # パスワード一致チェック
    submit = SubmitField('登録')

# ログインフォームの定義
class LoginForm(FlaskForm):
    # ユーザー名をメールアドレスに変更
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

# 登録ページのルート設定
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    # フォームのバリデーションが成功した場合の処理
    if form.validate_on_submit():
        db = get_db()  # データベース接続を取得
        error = None

        # ユーザー名の重複チェック
        if db.execute('SELECT id FROM user WHERE username = ?', 
            (form.username.data,)).fetchone() is not None:
            error = 'ユーザー名 {} は既に登録されています。'.format(form.username.data)
        # メールアドレスの重複チェック
        elif db.execute('SELECT id FROM user WHERE email = ?',
            (form.email.data,)).fetchone() is not None:
            error = 'メールアドレス {} は既に登録されています。'.format(form.email.data)

        if error is None:
            # ユーザー情報をデータベースに挿入
            db.execute(
                'INSERT INTO user (username, email, password) VALUES (?, ?, ?)',
                (form.username.data, form.email.data, generate_password_hash(form.password.data))
            )
            db.commit()
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))

        flash(error, 'error')

    return render_template('auth/register.html', form=form)

# ログインページのルート設定
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    # フォームのバリデーションが成功した場合の処理
    if form.validate_on_submit():
        db = get_db()  # データベース接続を取得
        error = None

        # ユーザー情報の取得
        user_data = db.execute(
            'SELECT * FROM user WHERE email = ?', (form.email.data,)
        ).fetchone()

        # ユーザー名のチェック
        if user_data is None:
            error = 'メールアドレスが正しくありません'
        # パスワードのチェック
        elif not check_password_hash(user_data['password'], form.password.data):
            error = 'パスワードが正しくありません'

        if error is None:
            # ユーザーをログイン状態にする
            user = User(user_data['id'], user_data['username'])
            login_user(user)
            return redirect(url_for('index'))

        flash(error, 'error')

    return render_template('auth/login.html', form=form)

# ログアウトページのルート設定
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))