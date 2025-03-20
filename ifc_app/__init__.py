import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'ifc_app.sqlite'),
        DEBUG=True  # デバッグモードを有効化
    )

    # CSRF保護を初期化
    csrf = CSRFProtect()
    csrf.init_app(app)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # データベース初期化
    from ifc_app import db
    db.init_app(app)
    
    # ログイン管理の設定
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
    login_manager.init_app(app)

    from ifc_app.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.get(id)
    
    # Blueprintの登録
    from ifc_app import auth
    app.register_blueprint(auth.bp)
    
    from ifc_app import views
    app.register_blueprint(views.bp)
    app.add_url_rule('/', endpoint='index')
    
    return app