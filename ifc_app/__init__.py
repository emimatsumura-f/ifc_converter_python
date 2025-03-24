# このファイルはFlaskアプリケーションの中心となる設定ファイルです

# 必要なライブラリをインポートします
import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# アプリケーションを作成する関数を定義します
def create_app(test_config=None):
    # Flaskアプリケーションを初期化します
    # instance_relative_config=Trueは、設定ファイルをインスタンスフォルダから読み込むことを意味します
    app = Flask(__name__, instance_relative_config=True)
    
    # アプリケーションの基本設定を行います
    app.config.from_mapping(
        # 開発環境用の秘密鍵を設定（本番環境では必ず変更してください）
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        # SQLiteデータベースのパスを設定
        DATABASE=os.path.join(app.instance_path, 'ifc_app.sqlite'),
        # アップロードされたファイルの保存先を設定
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 最大100MB
        # タイムアウトとバッファサイズの設定を追加
        PERMANENT_SESSION_LIFETIME=1800,  # 30分
        MAX_BUFFER_SIZE=100 * 1024 * 1024  # アップロード用バッファサイズ
    )

    # CSRF保護の設定
    csrf = CSRFProtect()
    csrf.init_app(app)

    # セッションの設定
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30分

    if test_config is None:
        # テスト設定が無い場合は、config.pyから設定を読み込みます（存在する場合）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト設定がある場合は、それを適用します
        app.config.update(test_config)

    # インスタンスフォルダとアップロードフォルダが存在することを確認します
    # これらのフォルダはGitには含まれないため、手動で作成する必要があります
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError as e:
        print(f"Error creating directories: {str(e)}")

    # データベースの初期化
    from ifc_app import db
    db.init_app(app)
    
    # ログイン管理の設定
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # ログインページのルートを指定
    login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
    login_manager.init_app(app)

    # ユーザーローダーの設定
    # これは、セッションからユーザー情報を取得するために使用されます
    from ifc_app.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.get(id)
    
    # Blueprintの登録
    # 各機能（認証、ビュー）をアプリケーションに登録します
    from ifc_app import auth
    app.register_blueprint(auth.bp)
    
    from ifc_app import views
    app.register_blueprint(views.bp)
    # メインページのURLを'/'に設定
    app.add_url_rule('/', endpoint='index')
    
    return app

# アプリケーションインスタンスの作成
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)